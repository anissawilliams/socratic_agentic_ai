-- 008: Final survey grows to 6 Likert items and 2 required open questions.
--
-- New columns are nullable only so any earlier TEST survey rows stay valid;
-- the submit function below requires every answer for new submissions.
-- Run once in the Supabase SQL editor. Wrapped in a transaction.

begin;

alter table public.survey_response
    add column if not exists likert_5 smallint check (likert_5 between 1 and 5),
    add column if not exists likert_6 smallint check (likert_6 between 1 and 5),
    add column if not exists open_response_2 text;

-- Replace the 4-item function with the 6-item, 2-open version.
drop function if exists public.submit_final_survey(
    uuid, text, text, smallint, smallint, smallint, smallint, text
);

create or replace function public.submit_final_survey(
    p_participant_id uuid,
    p_instrument_key text,
    p_instrument_version text,
    p_likert_1 smallint,
    p_likert_2 smallint,
    p_likert_3 smallint,
    p_likert_4 smallint,
    p_likert_5 smallint,
    p_likert_6 smallint,
    p_open_response text,
    p_open_response_2 text
)
returns timestamptz
language plpgsql
security definer
set search_path = public
as $$
declare
    subject_id uuid;
    participation_id uuid;
    existing_time timestamptz;
    submitted_time timestamptz := now();
begin
    subject_id := public.resolve_study_subject(p_participant_id);

    select id into participation_id
    from public.study_participation
    where study_subject_id = subject_id
      and status = 'survey'
    for update;

    if participation_id is null then
        select response.submitted_at into existing_time
        from public.survey_response response
        where response.study_subject_id = subject_id
        order by response.submitted_at desc
        limit 1;

        if existing_time is not null then
            return existing_time;  -- already submitted; nothing to do
        end if;
        raise exception 'Participant is not at the survey stage';
    end if;

    if p_likert_5 is null or p_likert_6 is null
       or length(btrim(coalesce(p_open_response, ''))) = 0
       or length(btrim(coalesce(p_open_response_2, ''))) = 0 then
        raise exception 'All survey questions are required';
    end if;

    insert into public.survey_response(
        study_participation_id,
        study_subject_id,
        instrument_key,
        instrument_version,
        likert_1, likert_2, likert_3, likert_4, likert_5, likert_6,
        open_response,
        open_response_2,
        submitted_at
    ) values (
        participation_id,
        subject_id,
        p_instrument_key,
        p_instrument_version,
        p_likert_1, p_likert_2, p_likert_3, p_likert_4, p_likert_5, p_likert_6,
        btrim(p_open_response),
        btrim(p_open_response_2),
        submitted_time
    )
    on conflict (study_participation_id) do nothing;

    update public.study_participation
    set status = 'complete',
        completed_at = submitted_time
    where id = participation_id;

    return submitted_time;
end;
$$;

commit;
