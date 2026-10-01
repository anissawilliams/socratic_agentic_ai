-- 003: Server-authoritative phase timers for pretest, tutor, and posttest.
--
-- Clock starts when the phase content is first created (assessment attempt
-- or tutor session), using the server's timestamp. Demographics and the
-- survey are untimed. The limit in effect is stamped on the row the first
-- time the timer is read, so later setting changes never alter a running
-- or finished phase.

begin;

-- 1. Timing columns. ---------------------------------------------------
alter table public.assessment_attempt
    add column if not exists time_limit_seconds integer
        check (time_limit_seconds > 0),
    add column if not exists timed_out boolean not null default false;

alter table public.tutor_session
    add column if not exists time_limit_seconds integer
        check (time_limit_seconds > 0),
    add column if not exists end_reason_code text
        check (end_reason_code in ('evaluator', 'timeout'));

-- 2. Tutor end reason + protection against a late turn reopening a session.
create or replace function public.guard_tutor_session_completion()
returns trigger
language plpgsql
as $$
begin
    -- A turn that was still generating when time ran out must not flip a
    -- completed session back to active.
    if old.status = 'complete' and new.status <> 'complete' then
        new.status := old.status;
        new.completed_at := old.completed_at;
        new.end_reason_code := old.end_reason_code;
        return new;
    end if;

    -- Completion through the normal turn path means the evaluator ended it.
    if new.status = 'complete'
       and old.status <> 'complete'
       and new.end_reason_code is null then
        new.end_reason_code := 'evaluator';
    end if;

    return new;
end;
$$;

drop trigger if exists guard_tutor_session_completion on public.tutor_session;

create trigger guard_tutor_session_completion
    before update on public.tutor_session
    for each row
    execute function public.guard_tutor_session_completion();

-- 3. Read (and stamp) the running timer for the participant's current phase.
create or replace function public.get_phase_timer(
    p_participant_id uuid,
    p_phase text,
    p_time_limit_seconds integer
)
returns table (
    started_at timestamptz,
    time_limit_seconds integer,
    server_now timestamptz
)
language plpgsql
security definer
set search_path = public
as $$
declare
    subject_id uuid;
    participation_id uuid;
begin
    if p_phase not in ('pretest', 'tutor', 'posttest') then
        raise exception 'Phase % is not timed', p_phase;
    end if;

    subject_id := public.resolve_study_subject(p_participant_id);

    select id into participation_id
    from public.study_participation
    where study_subject_id = subject_id
      and status = p_phase;

    if participation_id is null then
        return;
    end if;

    if p_phase = 'tutor' then
        update public.tutor_session session
        set time_limit_seconds = coalesce(session.time_limit_seconds, p_time_limit_seconds)
        where session.id = (
            select s.id from public.tutor_session s
            where s.study_participation_id = participation_id
              and s.status = 'active'
            order by s.started_at desc
            limit 1
        )
        returning session.started_at, session.time_limit_seconds, now()
        into started_at, time_limit_seconds, server_now;
    else
        update public.assessment_attempt attempt
        set time_limit_seconds = coalesce(attempt.time_limit_seconds, p_time_limit_seconds)
        where attempt.id = (
            select a.id from public.assessment_attempt a
            where a.study_participation_id = participation_id
              and a.stage = p_phase
              and a.status = 'started'
            order by a.started_at desc
            limit 1
        )
        returning attempt.started_at, attempt.time_limit_seconds, now()
        into started_at, time_limit_seconds, server_now;
    end if;

    if started_at is not null then
        return next;
    end if;
end;
$$;

-- 4. End the tutor phase when time runs out (idempotent). ------------------
create or replace function public.expire_tutor_session(
    p_participant_id uuid
)
returns timestamptz
language plpgsql
security definer
set search_path = public
as $$
declare
    subject_id uuid;
    participation_id uuid;
    session_id uuid;
    session_started timestamptz;
    session_limit integer;
    ended_time timestamptz := now();
begin
    subject_id := public.resolve_study_subject(p_participant_id);

    select id into participation_id
    from public.study_participation
    where study_subject_id = subject_id
      and status = 'tutor'
    for update;

    if participation_id is null then
        return null;  -- already moved on; nothing to do
    end if;

    select s.id, s.started_at, s.time_limit_seconds
    into session_id, session_started, session_limit
    from public.tutor_session s
    where s.study_participation_id = participation_id
      and s.status = 'active'
    order by s.started_at desc
    limit 1
    for update;

    if session_id is null or session_limit is null then
        raise exception 'No running tutor timer';
    end if;

    -- Small tolerance for network delay; never end a session early.
    if ended_time < session_started + make_interval(secs => session_limit - 3) then
        raise exception 'Tutor time has not expired';
    end if;

    update public.tutor_session
    set status = 'complete',
        completed_at = ended_time,
        end_reason_code = 'timeout'
    where id = session_id;

    update public.study_participation
    set status = 'posttest'
    where id = participation_id;

    insert into public.study_event(
        study_subject_id, study_participation_id, tutor_session_id,
        sequence_number, event_type_code, event_schema_version,
        occurred_at, idempotency_key
    ) values (
        subject_id, participation_id, session_id,
        public.next_study_event_sequence(subject_id),
        'tutor_session_timed_out', 'tutor_session_timed_out.v1',
        ended_time, gen_random_uuid()
    );

    return ended_time;
end;
$$;

-- 5. Submit an assessment when time runs out (blank answers allowed). ------
-- Only non-blank answers are stored; unanswered questions simply have no row.
create or replace function public.submit_assessment_on_timeout(
    p_attempt_id uuid,
    p_participant_id uuid,
    p_submission_id uuid,
    p_question_ids text[],
    p_construct_codes text[],
    p_response_texts text[]
)
returns timestamptz
language plpgsql
security definer
set search_path = public
as $$
declare
    subject_id uuid;
    participation_id uuid;
    submitted_time timestamptz;
    attempt_status text;
    attempt_stage text;
    attempt_started timestamptz;
    attempt_limit integer;
begin
    if cardinality(p_question_ids) <> 4
       or cardinality(p_construct_codes) <> 4
       or cardinality(p_response_texts) <> 4 then
        raise exception 'Exactly four assessment slots are required';
    end if;

    subject_id := public.resolve_study_subject(p_participant_id);

    select attempt.study_participation_id, attempt.submitted_at,
           attempt.status, attempt.stage,
           attempt.started_at, attempt.time_limit_seconds
    into participation_id, submitted_time, attempt_status, attempt_stage,
         attempt_started, attempt_limit
    from public.assessment_attempt attempt
    join public.study_participation participation
      on participation.id = attempt.study_participation_id
    where attempt.id = p_attempt_id
      and participation.study_subject_id = subject_id
    for update of attempt;

    if not found then
        raise exception 'Assessment attempt does not belong to participant';
    end if;

    if submitted_time is not null then
        return submitted_time;  -- already submitted (normally or by timeout)
    end if;

    if attempt_status <> 'started' then
        raise exception 'Only a started assessment attempt can be submitted';
    end if;

    if attempt_limit is null
       or now() < attempt_started + make_interval(secs => attempt_limit - 3) then
        raise exception 'Assessment time has not expired';
    end if;

    submitted_time := now();

    insert into public.assessment_answer(
        assessment_attempt_id, question_id, construct_code,
        display_order, response_text, submitted_at
    )
    select
        p_attempt_id,
        p_question_ids[item_index],
        p_construct_codes[item_index],
        item_index::smallint,
        btrim(p_response_texts[item_index]),
        submitted_time
    from generate_subscripts(p_question_ids, 1) as item_index
    where length(btrim(coalesce(p_response_texts[item_index], ''))) > 0;

    update public.assessment_attempt
    set status = 'submitted', submitted_at = submitted_time, timed_out = true
    where id = p_attempt_id;

    -- Same stage transition as a normal submit (Round 2 posttest is routed
    -- to the survey by the trigger from migration 002).
    update public.study_participation
    set status = case when attempt_stage = 'pretest' then 'tutor' else 'complete' end,
        started_at = coalesce(started_at, submitted_time),
        completed_at = case when attempt_stage = 'posttest'
            then submitted_time else completed_at end
    where id = participation_id;

    insert into public.study_event(
        study_subject_id, study_participation_id, assessment_attempt_id,
        sequence_number, event_type_code, event_schema_version,
        occurred_at, idempotency_key
    ) values (
        subject_id, participation_id, p_attempt_id,
        public.next_study_event_sequence(subject_id),
        'assessment_timed_out', 'assessment_timed_out.v1',
        submitted_time, p_submission_id
    );

    return submitted_time;
end;
$$;

commit;
