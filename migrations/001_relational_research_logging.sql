begin;

create table if not exists public.study_subject (
    id uuid primary key default gen_random_uuid(),
    is_test boolean not null default false,
    next_event_sequence bigint not null default 1 check (next_event_sequence > 0),
    created_at timestamptz not null default now()
);

create table if not exists public.study_subject_identity_link (
    study_subject_id uuid primary key references public.study_subject(id),
    participant_id uuid not null unique references public.study_participant(id),
    linked_at timestamptz not null default now(),
    detached_at timestamptz
);

create table if not exists public.study_participation (
    id uuid primary key default gen_random_uuid(),
    study_subject_id uuid not null references public.study_subject(id),
    round_number smallint not null check (round_number in (1, 2)),
    cohort_code text not null,
    transfer_type text not null check (transfer_type in ('near', 'far')),
    assigned_condition_code text not null,
    pretest_instrument_key text not null,
    pretest_scenario_key text not null,
    tutor_scenario_key text not null,
    posttest_instrument_key text not null,
    posttest_scenario_key text not null,
    status text not null default 'not_started' check (
        status in (
            'not_started',
            'demographics',
            'pretest',
            'tutor',
            'posttest',
            'complete'
        )
    ),
    started_at timestamptz,
    completed_at timestamptz,
    unique (study_subject_id, round_number),
    check (
        (round_number = 1 and transfer_type = 'near')
        or (round_number = 2 and transfer_type = 'far')
    ),
    check (pretest_scenario_key <> posttest_scenario_key)
);

-- demographic_response is intentionally deferred. Formal enrollment is
-- blocked until the approved demographic instrument can be represented with
-- explicit typed columns in a follow-up migration; untyped payloads are not an interim.

create table if not exists public.assessment_attempt (
    id uuid primary key default gen_random_uuid(),
    study_participation_id uuid not null references public.study_participation(id),
    stage text not null check (stage in ('pretest', 'posttest')),
    instrument_key text not null,
    instrument_version text not null,
    content_sha256 char(64) not null,
    scenario_key text not null,
    scenario_version text not null,
    scenario_sha256 char(64) not null,
    attempt_number smallint not null default 1 check (attempt_number >= 1),
    idempotency_key uuid not null unique,
    status text not null default 'started' check (
        status in ('started', 'submitted', 'abandoned')
    ),
    started_at timestamptz not null default now(),
    submitted_at timestamptz,
    abandoned_at timestamptz,
    abandonment_reason_code text,
    unique (study_participation_id, stage, attempt_number),
    check (
        (status = 'started' and submitted_at is null and abandoned_at is null)
        or (status = 'submitted' and submitted_at is not null and abandoned_at is null)
        or (
            status = 'abandoned'
            and submitted_at is null
            and abandoned_at is not null
            and abandonment_reason_code is not null
        )
    )
);

create table if not exists public.assessment_answer (
    id uuid primary key default gen_random_uuid(),
    assessment_attempt_id uuid not null references public.assessment_attempt(id) on delete cascade,
    question_id text not null,
    construct_code text not null,
    display_order smallint not null check (display_order between 1 and 4),
    response_text text not null check (length(btrim(response_text)) > 0),
    submitted_at timestamptz not null default now(),
    unique (assessment_attempt_id, question_id),
    unique (assessment_attempt_id, display_order)
);

create table if not exists public.tutor_session (
    id uuid primary key,
    study_subject_id uuid not null references public.study_subject(id),
    study_participation_id uuid not null references public.study_participation(id),
    assigned_condition_code text not null,
    runtime_condition_code text not null,
    scenario_key text not null,
    scenario_version text not null,
    scenario_sha256 char(64) not null,
    tutor_prompt_bundle_key text not null,
    tutor_prompt_bundle_version text not null,
    tutor_prompt_bundle_sha256 char(64) not null,
    prompt_sha256 char(64) not null,
    application_revision text not null,
    model_name text not null,
    opening_turn_id uuid not null unique,
    opening_message text not null,
    status text not null default 'active' check (status in ('active', 'complete', 'failed')),
    current_phase_code text,
    previous_phase_code text,
    started_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    completed_at timestamptz
);

create table if not exists public.tutor_turn (
    id uuid primary key,
    tutor_session_id uuid not null references public.tutor_session(id) on delete cascade,
    turn_number integer not null check (turn_number >= 1),
    student_message text not null,
    status text not null default 'started' check (status in ('started', 'completed', 'failed')),
    tutor_response text,
    phase_before_code text,
    phase_after_code text,
    previous_phase_code text,
    is_session_complete boolean not null default false,
    started_at timestamptz not null,
    completed_at timestamptz,
    failed_at timestamptz,
    latency_ms integer check (latency_ms >= 0),
    model_name text not null,
    tutor_prompt_bundle_key text not null,
    tutor_prompt_bundle_version text not null,
    tutor_prompt_bundle_sha256 char(64) not null,
    prompt_sha256 char(64) not null,
    application_revision text not null,
    input_tokens integer check (input_tokens >= 0),
    output_tokens integer check (output_tokens >= 0),
    error_code text,
    error_detail text,
    unique (tutor_session_id, turn_number),
    check (
        (status = 'started' and completed_at is null and failed_at is null)
        or (
            status = 'completed'
            and tutor_response is not null
            and completed_at is not null
            and failed_at is null
        )
        or (
            status = 'failed'
            and completed_at is null
            and failed_at is not null
            and error_code is not null
        )
    )
);

create table if not exists public.response_evaluation (
    tutor_turn_id uuid primary key references public.tutor_turn(id) on delete cascade,
    phase_goal_satisfied boolean not null,
    decision_code text not null check (decision_code in ('stay', 'advance')),
    reasoning_summary text not null,
    evidence text not null,
    learner_contribution text not null,
    addressed_question text not null,
    unresolved_issue text,
    follow_up_target text,
    session_goal_satisfied boolean not null,
    session_unresolved_issue text,
    session_completion_reason text,
    evaluator_model_name text not null,
    evaluator_prompt_version text not null,
    evaluator_prompt_sha256 char(64) not null,
    application_revision text not null,
    evaluated_at timestamptz not null default now()
);

create table if not exists public.evaluation_avoid_repeating (
    tutor_turn_id uuid not null references public.tutor_turn(id) on delete cascade,
    item_order smallint not null check (item_order > 0),
    content text not null,
    primary key (tutor_turn_id, item_order)
);

create table if not exists public.routing_decision (
    tutor_turn_id uuid primary key references public.tutor_turn(id) on delete cascade,
    action_code text not null check (action_code in ('stay', 'switch', 'revisit')),
    selected_phase_code text not null,
    topic_code text not null,
    move_type_code text not null,
    target text not null,
    reasoning_summary text not null,
    router_model_name text not null,
    router_prompt_version text not null,
    router_prompt_sha256 char(64) not null,
    application_revision text not null,
    routed_at timestamptz not null default now()
);

create table if not exists public.routing_avoid_repeating (
    tutor_turn_id uuid not null references public.tutor_turn(id) on delete cascade,
    item_order smallint not null check (item_order > 0),
    content text not null,
    primary key (tutor_turn_id, item_order)
);

create table if not exists public.study_event (
    id uuid primary key default gen_random_uuid(),
    study_subject_id uuid not null references public.study_subject(id),
    study_participation_id uuid references public.study_participation(id),
    assessment_attempt_id uuid references public.assessment_attempt(id),
    tutor_session_id uuid references public.tutor_session(id),
    tutor_turn_id uuid references public.tutor_turn(id),
    event_type_code text not null,
    event_schema_version text not null,
    sequence_number bigint not null,
    occurred_at timestamptz not null,
    recorded_at timestamptz not null default now(),
    idempotency_key uuid not null unique,
    unique (study_subject_id, sequence_number)
);

comment on table public.tutor_turn is
    'One attempted learner/tutor exchange. Begins when the learner message is accepted and ends with the corresponding tutor response or a terminal error.';
comment on column public.tutor_turn.turn_number is
    'Session-local attempt number. Evaluation, routing, and response rows referencing this turn all belong to this number; routing is not for the next turn.';
comment on column public.tutor_turn.started_at is
    'Time the learner message was durably accepted.';
comment on column public.tutor_turn.completed_at is
    'Time the corresponding tutor response and same-turn diagnostics were committed.';
comment on column public.tutor_turn.failed_at is
    'Time this attempted exchange was terminally marked failed.';
comment on table public.response_evaluation is
    'Evaluation of the learner message belonging to the referenced tutor turn.';
comment on table public.routing_decision is
    'Routing used to select the tutor response belonging to the referenced tutor turn, not the following turn.';

create index if not exists assessment_attempt_participation_idx
    on public.assessment_attempt(study_participation_id, stage);
create unique index if not exists assessment_attempt_one_started_idx
    on public.assessment_attempt(study_participation_id, stage)
    where status = 'started';
create index if not exists tutor_session_subject_idx
    on public.tutor_session(study_subject_id, started_at);
create index if not exists tutor_turn_session_idx
    on public.tutor_turn(tutor_session_id, turn_number);
create index if not exists study_event_subject_idx
    on public.study_event(study_subject_id, sequence_number);

alter table public.study_subject enable row level security;
alter table public.study_subject_identity_link enable row level security;
alter table public.study_participation enable row level security;
alter table public.assessment_attempt enable row level security;
alter table public.assessment_answer enable row level security;
alter table public.tutor_session enable row level security;
alter table public.tutor_turn enable row level security;
alter table public.response_evaluation enable row level security;
alter table public.evaluation_avoid_repeating enable row level security;
alter table public.routing_decision enable row level security;
alter table public.routing_avoid_repeating enable row level security;
alter table public.study_event enable row level security;

create or replace function public.resolve_study_subject(p_participant_id uuid)
returns uuid
language plpgsql
security definer
set search_path = public
as $$
declare
    resolved_id uuid;
    participant_is_test boolean;
begin
    select study_subject_id into resolved_id
    from public.study_subject_identity_link
    where participant_id = p_participant_id;

    if resolved_id is not null then
        return resolved_id;
    end if;

    select is_test into participant_is_test
    from public.study_participant
    where id = p_participant_id;

    if not found then
        raise exception 'Unknown participant';
    end if;

    begin
        insert into public.study_subject(is_test)
        values (coalesce(participant_is_test, false))
        returning id into resolved_id;

        insert into public.study_subject_identity_link(
            study_subject_id,
            participant_id
        ) values (
            resolved_id,
            p_participant_id
        );
    exception when unique_violation then
        select study_subject_id into resolved_id
        from public.study_subject_identity_link
        where participant_id = p_participant_id;
    end;

    return resolved_id;
end;
$$;

create or replace function public.next_study_event_sequence(p_subject_id uuid)
returns bigint
language plpgsql
security definer
set search_path = public
as $$
declare
    allocated_sequence bigint;
begin
    update public.study_subject
    set next_event_sequence = next_event_sequence + 1
    where id = p_subject_id
    returning next_event_sequence - 1 into allocated_sequence;

    if not found then
        raise exception 'Unknown study subject';
    end if;

    return allocated_sequence;
end;
$$;

create or replace function public.get_current_study_participation(
    p_participant_id uuid
)
returns setof public.study_participation
language sql
security definer
set search_path = public
as $$
    select participation.*
    from public.study_participation participation
    where participation.study_subject_id = public.resolve_study_subject(p_participant_id)
      and participation.status <> 'complete'
    order by participation.round_number
    limit 1;
$$;

create or replace function public.start_tutor_session(
    p_session_id uuid,
    p_participant_id uuid,
    p_study_participation_id uuid,
    p_assigned_condition_code text,
    p_runtime_condition_code text,
    p_scenario_key text,
    p_scenario_version text,
    p_scenario_sha256 char(64),
    p_tutor_prompt_bundle_key text,
    p_tutor_prompt_bundle_version text,
    p_tutor_prompt_bundle_sha256 char(64),
    p_prompt_sha256 char(64),
    p_application_revision text,
    p_model_name text,
    p_opening_turn_id uuid,
    p_opening_message text,
    p_current_phase_code text
)
returns void
language plpgsql
security definer
set search_path = public
as $$
declare
    subject_id uuid;
begin
    subject_id := public.resolve_study_subject(p_participant_id);

    if not exists (
        select 1 from public.study_participation
        where id = p_study_participation_id
          and study_subject_id = subject_id
          and assigned_condition_code = p_assigned_condition_code
          and tutor_scenario_key = p_scenario_key
          and status = 'tutor'
    ) then
        raise exception 'Tutor session does not match an active study assignment';
    end if;

    insert into public.tutor_session(
        id,
        study_subject_id,
        study_participation_id,
        assigned_condition_code,
        runtime_condition_code,
        scenario_key,
        scenario_version,
        scenario_sha256,
        tutor_prompt_bundle_key,
        tutor_prompt_bundle_version,
        tutor_prompt_bundle_sha256,
        prompt_sha256,
        application_revision,
        model_name,
        opening_turn_id,
        opening_message,
        current_phase_code
    ) values (
        p_session_id,
        subject_id,
        p_study_participation_id,
        p_assigned_condition_code,
        p_runtime_condition_code,
        p_scenario_key,
        p_scenario_version,
        p_scenario_sha256,
        p_tutor_prompt_bundle_key,
        p_tutor_prompt_bundle_version,
        p_tutor_prompt_bundle_sha256,
        p_prompt_sha256,
        p_application_revision,
        p_model_name,
        p_opening_turn_id,
        p_opening_message,
        p_current_phase_code
    );

    insert into public.study_event(
        study_subject_id,
        study_participation_id,
        tutor_session_id,
        sequence_number,
        event_type_code,
        event_schema_version,
        occurred_at,
        idempotency_key
    ) values (
        subject_id,
        p_study_participation_id,
        p_session_id,
        public.next_study_event_sequence(subject_id),
        'tutor_session_started',
        'tutor_session_started.v1',
        now(),
        p_opening_turn_id
    );
end;
$$;

create or replace function public.start_tutor_turn(
    p_turn_id uuid,
    p_session_id uuid,
    p_participant_id uuid,
    p_student_message text,
    p_phase_before_code text,
    p_model_name text,
    p_tutor_prompt_bundle_key text,
    p_tutor_prompt_bundle_version text,
    p_tutor_prompt_bundle_sha256 char(64),
    p_prompt_sha256 char(64),
    p_application_revision text
)
returns void
language plpgsql
security definer
set search_path = public
as $$
declare
    subject_id uuid;
    participation_id uuid;
    next_turn_number integer;
begin
    subject_id := public.resolve_study_subject(p_participant_id);

    if exists (select 1 from public.tutor_turn where id = p_turn_id) then
        return;
    end if;

    select study_participation_id into participation_id
    from public.tutor_session
    where id = p_session_id
      and study_subject_id = subject_id
      and status = 'active'
    for update;

    if not found then
        raise exception 'Unknown, inactive, or unauthorized tutor session';
    end if;

    select coalesce(max(turn_number), 0) + 1 into next_turn_number
    from public.tutor_turn
    where tutor_session_id = p_session_id;

    insert into public.tutor_turn(
        id, tutor_session_id, turn_number, status, student_message,
        phase_before_code, started_at, model_name, tutor_prompt_bundle_key,
        tutor_prompt_bundle_version, tutor_prompt_bundle_sha256, prompt_sha256,
        application_revision
    ) values (
        p_turn_id, p_session_id, next_turn_number, 'started', p_student_message,
        p_phase_before_code, now(), p_model_name, p_tutor_prompt_bundle_key,
        p_tutor_prompt_bundle_version, p_tutor_prompt_bundle_sha256,
        p_prompt_sha256,
        p_application_revision
    );

    insert into public.study_event(
        study_subject_id, study_participation_id, tutor_session_id,
        tutor_turn_id, sequence_number,
        event_type_code, event_schema_version, occurred_at, idempotency_key
    ) values (
        subject_id, participation_id, p_session_id, p_turn_id,
        public.next_study_event_sequence(subject_id),
        'tutor_turn_started', 'tutor_turn_started.v1', now(), p_turn_id
    );
end;
$$;

create or replace function public.record_tutor_turn(
    p_turn_id uuid,
    p_session_id uuid,
    p_participant_id uuid,
    p_tutor_response text,
    p_phase_before_code text,
    p_phase_after_code text,
    p_previous_phase_code text,
    p_is_session_complete boolean,
    p_completed_at timestamptz,
    p_latency_ms integer,
    p_input_tokens integer,
    p_output_tokens integer,
    p_phase_goal_satisfied boolean,
    p_evaluation_decision_code text,
    p_evaluation_reasoning_summary text,
    p_evaluation_evidence text,
    p_learner_contribution text,
    p_addressed_question text,
    p_unresolved_issue text,
    p_follow_up_target text,
    p_evaluation_avoid_repeating text[],
    p_session_goal_satisfied boolean,
    p_session_unresolved_issue text,
    p_session_completion_reason text,
    p_evaluator_model_name text,
    p_evaluator_prompt_version text,
    p_evaluator_prompt_sha256 char(64),
    p_evaluator_application_revision text,
    p_routing_action_code text,
    p_selected_phase_code text,
    p_routing_topic_code text,
    p_routing_move_type_code text,
    p_routing_target text,
    p_routing_reasoning_summary text,
    p_routing_avoid_repeating text[],
    p_router_model_name text,
    p_router_prompt_version text,
    p_router_prompt_sha256 char(64),
    p_router_application_revision text
)
returns void
language plpgsql
security definer
set search_path = public
as $$
declare
    subject_id uuid;
    participation_id uuid;
    completion_event_id uuid;
begin
    subject_id := public.resolve_study_subject(p_participant_id);

    select study_participation_id into participation_id
    from public.tutor_session
    where id = p_session_id
      and study_subject_id = subject_id
    for update;

    if not found then
        raise exception 'Unknown tutor session';
    end if;

    if exists (
        select 1 from public.tutor_turn
        where id = p_turn_id and status = 'completed'
    ) then
        return;
    end if;

    update public.tutor_turn
    set status = 'completed',
        tutor_response = p_tutor_response,
        phase_after_code = p_phase_after_code,
        previous_phase_code = p_previous_phase_code,
        is_session_complete = p_is_session_complete,
        completed_at = coalesce(p_completed_at, now()),
        failed_at = null,
        error_code = null,
        error_detail = null,
        latency_ms = p_latency_ms,
        input_tokens = p_input_tokens,
        output_tokens = p_output_tokens
    where id = p_turn_id
      and tutor_session_id = p_session_id
      and status = 'started';

    if not found then
        raise exception 'Tutor turn is missing or is not in started state';
    end if;

    insert into public.response_evaluation(
        tutor_turn_id,
        phase_goal_satisfied,
        decision_code,
        reasoning_summary,
        evidence,
        learner_contribution,
        addressed_question,
        unresolved_issue,
        follow_up_target,
        session_goal_satisfied,
        session_unresolved_issue,
        session_completion_reason,
        evaluator_model_name,
        evaluator_prompt_version,
        evaluator_prompt_sha256,
        application_revision
    ) values (
        p_turn_id,
        p_phase_goal_satisfied,
        p_evaluation_decision_code,
        p_evaluation_reasoning_summary,
        p_evaluation_evidence,
        p_learner_contribution,
        p_addressed_question,
        p_unresolved_issue,
        p_follow_up_target,
        p_session_goal_satisfied,
        p_session_unresolved_issue,
        p_session_completion_reason,
        p_evaluator_model_name,
        p_evaluator_prompt_version,
        p_evaluator_prompt_sha256,
        p_evaluator_application_revision
    );

    insert into public.evaluation_avoid_repeating(
        tutor_turn_id,
        item_order,
        content
    )
    select p_turn_id, ordinal::smallint, item
    from unnest(coalesce(p_evaluation_avoid_repeating, array[]::text[]))
        with ordinality as values_to_insert(item, ordinal);

    if p_routing_action_code is not null then
        insert into public.routing_decision(
            tutor_turn_id,
            action_code,
            selected_phase_code,
            topic_code,
            move_type_code,
            target,
            reasoning_summary,
            router_model_name,
            router_prompt_version,
            router_prompt_sha256,
            application_revision
        ) values (
            p_turn_id,
            p_routing_action_code,
            p_selected_phase_code,
            p_routing_topic_code,
            p_routing_move_type_code,
            p_routing_target,
            p_routing_reasoning_summary,
            p_router_model_name,
            p_router_prompt_version,
            p_router_prompt_sha256,
            p_router_application_revision
        );

        insert into public.routing_avoid_repeating(
            tutor_turn_id,
            item_order,
            content
        )
        select p_turn_id, ordinal::smallint, item
        from unnest(coalesce(p_routing_avoid_repeating, array[]::text[]))
            with ordinality as values_to_insert(item, ordinal);
    end if;

    update public.tutor_session
    set current_phase_code = p_phase_after_code,
        previous_phase_code = p_previous_phase_code,
        status = case when p_is_session_complete then 'complete' else 'active' end,
        completed_at = case when p_is_session_complete then p_completed_at else null end,
        updated_at = now()
    where id = p_session_id;

    if p_is_session_complete then
        update public.study_participation
        set status = 'posttest'
        where id = participation_id and status = 'tutor';
    end if;

    completion_event_id := gen_random_uuid();

    insert into public.study_event(
        study_subject_id,
        study_participation_id,
        tutor_session_id,
        tutor_turn_id,
        sequence_number,
        event_type_code,
        event_schema_version,
        occurred_at,
        idempotency_key
    ) values (
        subject_id,
        participation_id,
        p_session_id,
        p_turn_id,
        public.next_study_event_sequence(subject_id),
        case when p_is_session_complete then 'tutor_session_completed' else 'tutor_turn_completed' end,
        case when p_is_session_complete then 'tutor_session_completed.v1' else 'tutor_turn_completed.v1' end,
        coalesce(p_completed_at, now()),
        completion_event_id
    );
end;
$$;

create or replace function public.fail_tutor_turn(
    p_turn_id uuid,
    p_session_id uuid,
    p_participant_id uuid,
    p_error_code text,
    p_error_detail text,
    p_latency_ms integer,
    p_input_tokens integer,
    p_output_tokens integer
)
returns void
language plpgsql
security definer
set search_path = public
as $$
declare
    subject_id uuid;
    participation_id uuid;
    failure_event_id uuid;
begin
    subject_id := public.resolve_study_subject(p_participant_id);

    select study_participation_id into participation_id
    from public.tutor_session
    where id = p_session_id and study_subject_id = subject_id
    for update;

    if not found then
        raise exception 'Unknown or unauthorized tutor session';
    end if;

    update public.tutor_turn
    set status = 'failed',
        failed_at = now(),
        error_code = p_error_code,
        error_detail = left(p_error_detail, 2000),
        latency_ms = p_latency_ms,
        input_tokens = p_input_tokens,
        output_tokens = p_output_tokens
    where id = p_turn_id
      and tutor_session_id = p_session_id
      and status = 'started';

    if not found then
        return;
    end if;

    update public.tutor_session set updated_at = now() where id = p_session_id;
    failure_event_id := gen_random_uuid();

    insert into public.study_event(
        study_subject_id, study_participation_id, tutor_session_id,
        tutor_turn_id, sequence_number,
        event_type_code, event_schema_version, occurred_at, idempotency_key
    ) values (
        subject_id, participation_id, p_session_id, p_turn_id,
        public.next_study_event_sequence(subject_id),
        'tutor_turn_failed', 'tutor_turn_failed.v1', now(), failure_event_id
    );
end;
$$;

create or replace function public.start_assessment_attempt(
    p_attempt_id uuid,
    p_participant_id uuid,
    p_study_participation_id uuid,
    p_stage text,
    p_instrument_key text,
    p_instrument_version text,
    p_content_sha256 char(64),
    p_scenario_key text,
    p_scenario_version text,
    p_scenario_sha256 char(64),
    p_attempt_number smallint,
    p_idempotency_key uuid
)
returns uuid
language plpgsql
security definer
set search_path = public
as $$
declare
    subject_id uuid;
    existing_attempt_id uuid;
    expected_instrument_key text;
    expected_scenario_key text;
    participation_status text;
begin
    subject_id := public.resolve_study_subject(p_participant_id);

    select
        case when p_stage = 'pretest'
            then pretest_instrument_key else posttest_instrument_key end,
        case when p_stage = 'pretest'
            then pretest_scenario_key else posttest_scenario_key end,
        status
    into expected_instrument_key, expected_scenario_key, participation_status
    from public.study_participation
    where id = p_study_participation_id
      and study_subject_id = subject_id;

    if not found then
        raise exception 'Study participation does not belong to participant';
    end if;
    if p_stage not in ('pretest', 'posttest')
       or participation_status <> p_stage then
        raise exception 'Assessment stage is not currently available';
    end if;
    if p_instrument_key <> expected_instrument_key
       or p_scenario_key <> expected_scenario_key then
        raise exception 'Assessment content does not match study assignment';
    end if;

    select id into existing_attempt_id
    from public.assessment_attempt
    where idempotency_key = p_idempotency_key;

    if existing_attempt_id is not null then
        return existing_attempt_id;
    end if;

    insert into public.assessment_attempt(
        id,
        study_participation_id,
        stage,
        instrument_key,
        instrument_version,
        content_sha256,
        scenario_key,
        scenario_version,
        scenario_sha256,
        attempt_number,
        idempotency_key
    ) values (
        p_attempt_id,
        p_study_participation_id,
        p_stage,
        p_instrument_key,
        p_instrument_version,
        p_content_sha256,
        p_scenario_key,
        p_scenario_version,
        p_scenario_sha256,
        p_attempt_number,
        p_idempotency_key
    );

    insert into public.study_event(
        study_subject_id,
        study_participation_id,
        assessment_attempt_id,
        sequence_number,
        event_type_code,
        event_schema_version,
        occurred_at,
        idempotency_key
    ) values (
        subject_id,
        p_study_participation_id,
        p_attempt_id,
        public.next_study_event_sequence(subject_id),
        'assessment_started',
        'assessment_started.v1',
        now(),
        p_attempt_id
    );

    return p_attempt_id;
end;
$$;

create or replace function public.submit_assessment_attempt(
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
begin
    if cardinality(p_question_ids) <> 4
       or cardinality(p_construct_codes) <> 4
       or cardinality(p_response_texts) <> 4 then
        raise exception 'Exactly four assessment answers are required';
    end if;

    if exists (
        select 1
        from unnest(p_response_texts) as response_text
        where length(btrim(response_text)) = 0
    ) then
        raise exception 'Assessment answers cannot be blank';
    end if;

    subject_id := public.resolve_study_subject(p_participant_id);

    select attempt.study_participation_id, attempt.submitted_at,
           attempt.status, attempt.stage
    into participation_id, submitted_time, attempt_status, attempt_stage
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
        return submitted_time;
    end if;
    if attempt_status <> 'started' then
        raise exception 'Only a started assessment attempt can be submitted';
    end if;

    submitted_time := now();

    insert into public.assessment_answer(
        assessment_attempt_id,
        question_id,
        construct_code,
        display_order,
        response_text,
        submitted_at
    )
    select
        p_attempt_id,
        p_question_ids[item_index],
        p_construct_codes[item_index],
        item_index::smallint,
        btrim(p_response_texts[item_index]),
        submitted_time
    from generate_subscripts(p_question_ids, 1) as item_index;

    update public.assessment_attempt
    set status = 'submitted', submitted_at = submitted_time
    where id = p_attempt_id;

    update public.study_participation
    set status = case when attempt_stage = 'pretest' then 'tutor' else 'complete' end,
        started_at = coalesce(started_at, submitted_time),
        completed_at = case when attempt_stage = 'posttest'
            then submitted_time else completed_at end
    where id = participation_id;

    insert into public.study_event(
        study_subject_id,
        study_participation_id,
        assessment_attempt_id,
        sequence_number,
        event_type_code,
        event_schema_version,
        occurred_at,
        idempotency_key
    ) values (
        subject_id,
        participation_id,
        p_attempt_id,
        public.next_study_event_sequence(subject_id),
        'assessment_submitted',
        'assessment_submitted.v1',
        submitted_time,
        p_submission_id
    );

    return submitted_time;
end;
$$;

create or replace function public.abandon_assessment_attempt(
    p_attempt_id uuid,
    p_participant_id uuid,
    p_abandonment_id uuid,
    p_reason_code text
)
returns timestamptz
language plpgsql
security definer
set search_path = public
as $$
declare
    subject_id uuid;
    participation_id uuid;
    abandoned_time timestamptz;
begin
    subject_id := public.resolve_study_subject(p_participant_id);
    if length(btrim(p_reason_code)) = 0 then
        raise exception 'Assessment abandonment reason is required';
    end if;

    select attempt.study_participation_id, attempt.abandoned_at
    into participation_id, abandoned_time
    from public.assessment_attempt attempt
    join public.study_participation participation
      on participation.id = attempt.study_participation_id
    where attempt.id = p_attempt_id
      and participation.study_subject_id = subject_id
    for update of attempt;

    if not found then
        raise exception 'Assessment attempt does not belong to participant';
    end if;
    if abandoned_time is not null then
        return abandoned_time;
    end if;
    if exists (
        select 1 from public.assessment_attempt
        where id = p_attempt_id and status <> 'started'
    ) then
        raise exception 'Only a started assessment attempt can be abandoned';
    end if;

    abandoned_time := now();
    update public.assessment_attempt
    set status = 'abandoned',
        abandoned_at = abandoned_time,
        abandonment_reason_code = btrim(p_reason_code)
    where id = p_attempt_id;

    insert into public.study_event(
        study_subject_id, study_participation_id, assessment_attempt_id,
        sequence_number, event_type_code, event_schema_version, occurred_at,
        idempotency_key
    ) values (
        subject_id, participation_id, p_attempt_id,
        public.next_study_event_sequence(subject_id),
        'assessment_abandoned', 'assessment_abandoned.v1', abandoned_time,
        p_abandonment_id
    );
    return abandoned_time;
end;
$$;

create or replace view public.research_participant_outcome as
select
    participation.id as study_participation_id,
    participation.study_subject_id,
    subject.is_test,
    participation.round_number,
    participation.cohort_code,
    participation.transfer_type,
    participation.assigned_condition_code,
    participation.pretest_scenario_key,
    participation.tutor_scenario_key,
    participation.posttest_scenario_key,
    participation.status,
    participation.started_at,
    participation.completed_at
from public.study_participation participation
join public.study_subject subject
  on subject.id = participation.study_subject_id;

create or replace view public.internal_tutor_diagnostic as
select
    session.study_subject_id,
    session.id as tutor_session_id,
    turn.id as tutor_turn_id,
    turn.turn_number,
    session.assigned_condition_code,
    session.runtime_condition_code,
    session.scenario_key,
    session.scenario_version,
    session.scenario_sha256,
    turn.student_message,
    turn.tutor_response,
    turn.status as turn_status,
    turn.phase_before_code,
    turn.phase_after_code,
    turn.started_at,
    turn.completed_at,
    turn.latency_ms,
    turn.model_name,
    turn.tutor_prompt_bundle_key,
    turn.tutor_prompt_bundle_version,
    turn.tutor_prompt_bundle_sha256,
    turn.prompt_sha256,
    turn.application_revision,
    turn.input_tokens,
    turn.output_tokens,
    turn.error_code,
    turn.error_detail,
    evaluation.phase_goal_satisfied,
    evaluation.decision_code as evaluation_decision_code,
    evaluation.reasoning_summary as evaluation_reasoning_summary,
    evaluation.evidence as evaluation_evidence,
    evaluation.learner_contribution,
    evaluation.addressed_question,
    evaluation.unresolved_issue,
    evaluation.follow_up_target,
    evaluation.session_goal_satisfied,
    evaluation.session_unresolved_issue,
    evaluation.session_completion_reason,
    evaluation.evaluator_prompt_sha256,
    route.action_code as routing_action_code,
    route.selected_phase_code,
    route.topic_code as routing_topic_code,
    route.move_type_code as routing_move_type_code,
    route.target as routing_target,
    route.reasoning_summary as routing_reasoning_summary,
    route.router_prompt_sha256
from public.tutor_session session
join public.tutor_turn turn
  on turn.tutor_session_id = session.id
left join public.response_evaluation evaluation
  on evaluation.tutor_turn_id = turn.id
left join public.routing_decision route
  on route.tutor_turn_id = turn.id;

revoke all on public.research_participant_outcome from public, anon, authenticated;
revoke all on public.internal_tutor_diagnostic from public, anon, authenticated;
grant select on public.research_participant_outcome to service_role;
grant select on public.internal_tutor_diagnostic to service_role;

revoke all on function public.resolve_study_subject(uuid) from public, anon, authenticated;
revoke all on function public.next_study_event_sequence(uuid) from public, anon, authenticated;
revoke all on function public.get_current_study_participation(uuid) from public, anon, authenticated;
revoke all on function public.start_tutor_session(
    uuid, uuid, uuid, text, text, text, text, char, text, text, char, char, text,
    text, uuid, text, text
) from public, anon, authenticated;
revoke all on function public.start_tutor_turn(
    uuid, uuid, uuid, text, text, text, text, text, char, char, text
) from public, anon, authenticated;
revoke all on function public.record_tutor_turn(
    uuid, uuid, uuid, text, text, text, text, boolean, timestamptz,
    integer, integer, integer,
    boolean, text, text, text, text, text, text, text, text[], boolean,
    text, text, text, text, char, text, text, text, text, text, text, text,
    text[], text, text, char, text
) from public, anon, authenticated;
revoke all on function public.fail_tutor_turn(
    uuid, uuid, uuid, text, text, integer, integer, integer
) from public, anon, authenticated;

grant execute on function public.resolve_study_subject(uuid) to service_role;
grant execute on function public.next_study_event_sequence(uuid) to service_role;
grant execute on function public.get_current_study_participation(uuid) to service_role;
grant execute on function public.start_tutor_session(
    uuid, uuid, uuid, text, text, text, text, char, text, text, char, char, text,
    text, uuid, text, text
) to service_role;
grant execute on function public.start_tutor_turn(
    uuid, uuid, uuid, text, text, text, text, text, char, char, text
) to service_role;
grant execute on function public.record_tutor_turn(
    uuid, uuid, uuid, text, text, text, text, boolean, timestamptz,
    integer, integer, integer,
    boolean, text, text, text, text, text, text, text, text[], boolean,
    text, text, text, text, char, text, text, text, text, text, text, text,
    text[], text, text, char, text
) to service_role;
grant execute on function public.fail_tutor_turn(
    uuid, uuid, uuid, text, text, integer, integer, integer
) to service_role;
revoke all on function public.start_assessment_attempt(
    uuid, uuid, uuid, text, text, text, char, text, text, char, smallint, uuid
) from public, anon, authenticated;
revoke all on function public.submit_assessment_attempt(
    uuid, uuid, uuid, text[], text[], text[]
) from public, anon, authenticated;
grant execute on function public.start_assessment_attempt(
    uuid, uuid, uuid, text, text, text, char, text, text, char, smallint, uuid
) to service_role;
grant execute on function public.submit_assessment_attempt(
    uuid, uuid, uuid, text[], text[], text[]
) to service_role;
revoke all on function public.abandon_assessment_attempt(
    uuid, uuid, uuid, text
) from public, anon, authenticated;
grant execute on function public.abandon_assessment_attempt(
    uuid, uuid, uuid, text
) to service_role;

commit;
