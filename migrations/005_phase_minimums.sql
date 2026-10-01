-- 005: Minimum times per phase (run after 003).
--
-- Pretest/posttest: a normal submit is refused before the minimum
-- (timeout submits are always allowed). Tutor: after the minimum the
-- participant may choose to continue ('participant' end reason).

begin;

alter table public.assessment_attempt
    add column if not exists min_time_seconds integer
        check (min_time_seconds >= 0);

alter table public.tutor_session
    add column if not exists min_time_seconds integer
        check (min_time_seconds >= 0);

alter table public.tutor_session
    drop constraint if exists tutor_session_end_reason_code_check;

alter table public.tutor_session
    add constraint tutor_session_end_reason_code_check
        check (end_reason_code in ('evaluator', 'timeout', 'participant'));

-- 1. Refuse an early normal submit (database-level guarantee). -------------
create or replace function public.enforce_assessment_minimum_time()
returns trigger
language plpgsql
as $$
begin
    if old.status = 'started'
       and new.status = 'submitted'
       and not new.timed_out
       and old.min_time_seconds is not null
       and now() < old.started_at + make_interval(secs => old.min_time_seconds - 3) then
        raise exception 'Minimum time for this step has not been reached';
    end if;
    return new;
end;
$$;

drop trigger if exists enforce_assessment_minimum_time on public.assessment_attempt;

create trigger enforce_assessment_minimum_time
    before update on public.assessment_attempt
    for each row
    execute function public.enforce_assessment_minimum_time();

-- 2. Timer read now stamps and returns the minimum too. --------------------
drop function if exists public.get_phase_timer(uuid, text, integer);

create or replace function public.get_phase_timer(
    p_participant_id uuid,
    p_phase text,
    p_time_limit_seconds integer,
    p_min_time_seconds integer
)
returns table (
    started_at timestamptz,
    min_time_seconds integer,
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
        set time_limit_seconds = coalesce(session.time_limit_seconds, p_time_limit_seconds),
            min_time_seconds = coalesce(session.min_time_seconds, p_min_time_seconds)
        where session.id = (
            select s.id from public.tutor_session s
            where s.study_participation_id = participation_id
              and s.status = 'active'
            order by s.started_at desc
            limit 1
        )
        returning session.started_at, session.min_time_seconds,
                  session.time_limit_seconds, now()
        into started_at, min_time_seconds, time_limit_seconds, server_now;
    else
        update public.assessment_attempt attempt
        set time_limit_seconds = coalesce(attempt.time_limit_seconds, p_time_limit_seconds),
            min_time_seconds = coalesce(attempt.min_time_seconds, p_min_time_seconds)
        where attempt.id = (
            select a.id from public.assessment_attempt a
            where a.study_participation_id = participation_id
              and a.stage = p_phase
              and a.status = 'started'
            order by a.started_at desc
            limit 1
        )
        returning attempt.started_at, attempt.min_time_seconds,
                  attempt.time_limit_seconds, now()
        into started_at, min_time_seconds, time_limit_seconds, server_now;
    end if;

    if started_at is not null then
        return next;
    end if;
end;
$$;

-- 3. Participant chooses to continue after the tutor minimum. --------------
create or replace function public.finish_tutor_session(
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
    session_min integer;
    ended_time timestamptz := now();
begin
    subject_id := public.resolve_study_subject(p_participant_id);

    select id into participation_id
    from public.study_participation
    where study_subject_id = subject_id
      and status = 'tutor'
    for update;

    if participation_id is null then
        return null;  -- already moved on
    end if;

    select s.id, s.started_at, s.min_time_seconds
    into session_id, session_started, session_min
    from public.tutor_session s
    where s.study_participation_id = participation_id
      and s.status = 'active'
    order by s.started_at desc
    limit 1
    for update;

    if session_id is null or session_min is null then
        raise exception 'No running tutor timer';
    end if;

    if ended_time < session_started + make_interval(secs => session_min - 3) then
        raise exception 'Minimum tutor time has not been reached';
    end if;

    update public.tutor_session
    set status = 'complete',
        completed_at = ended_time,
        end_reason_code = 'participant'
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
        'tutor_session_finished_by_participant',
        'tutor_session_finished_by_participant.v1',
        ended_time, gen_random_uuid()
    );

    return ended_time;
end;
$$;

commit;
