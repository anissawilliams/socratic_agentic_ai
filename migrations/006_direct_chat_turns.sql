-- 006: Record control-condition (direct chat) turns.
--
-- Same tutor_turn row and turn-completed event as the Socratic condition,
-- but no evaluation or routing rows, and a turn never ends the session
-- (control sessions end by the timer or by the participant after the
-- minimum time).

begin;

create or replace function public.record_direct_chat_turn(
    p_turn_id uuid,
    p_session_id uuid,
    p_participant_id uuid,
    p_tutor_response text,
    p_completed_at timestamptz,
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
begin
    subject_id := public.resolve_study_subject(p_participant_id);

    select study_participation_id into participation_id
    from public.tutor_session
    where id = p_session_id
      and study_subject_id = subject_id
      and runtime_condition_code = 'direct_chat'
    for update;

    if not found then
        raise exception 'Unknown direct-chat session';
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
        is_session_complete = false,
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

    update public.tutor_session
    set updated_at = now()
    where id = p_session_id;

    insert into public.study_event(
        study_subject_id, study_participation_id, tutor_session_id,
        tutor_turn_id, sequence_number, event_type_code,
        event_schema_version, occurred_at, idempotency_key
    ) values (
        subject_id, participation_id, p_session_id,
        p_turn_id, public.next_study_event_sequence(subject_id),
        'tutor_turn_completed', 'tutor_turn_completed.v1',
        coalesce(p_completed_at, now()), gen_random_uuid()
    );
end;
$$;

commit;
