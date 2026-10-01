-- 004: Add undergraduate/graduate to demographics.
-- Migration 002 is already applied, so this extends it in place.

begin;

alter table public.demographic_response
    add column if not exists academic_level_code text
        check (academic_level_code in ('undergraduate', 'graduate'));

-- Replace the submit function with one that takes the new answer.
drop function if exists public.submit_demographics(
    uuid, smallint, text, boolean, boolean, boolean, boolean, boolean,
    boolean, text, text
);

create or replace function public.submit_demographics(
    p_participant_id uuid,
    p_age smallint,
    p_gender_code text,
    p_academic_level_code text,
    p_race_white_european boolean,
    p_race_black_african boolean,
    p_race_asian boolean,
    p_race_hispanic_latino boolean,
    p_race_middle_eastern_north_african boolean,
    p_race_other boolean,
    p_race_other_description text,
    p_field_of_study text
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
    if p_academic_level_code is null
       or p_academic_level_code not in ('undergraduate', 'graduate') then
        raise exception 'Academic level is required';
    end if;

    subject_id := public.resolve_study_subject(p_participant_id);

    select submitted_at into existing_time
    from public.demographic_response
    where study_subject_id = subject_id;

    select id into participation_id
    from public.study_participation
    where study_subject_id = subject_id
      and status = 'demographics'
    for update;

    if participation_id is null then
        if existing_time is not null then
            return existing_time;
        end if;
        raise exception 'Participant is not at the demographics stage';
    end if;

    if existing_time is null then
        insert into public.demographic_response(
            study_subject_id,
            study_participation_id,
            age,
            gender_code,
            academic_level_code,
            race_white_european,
            race_black_african,
            race_asian,
            race_hispanic_latino,
            race_middle_eastern_north_african,
            race_other,
            race_other_description,
            field_of_study,
            submitted_at
        ) values (
            subject_id,
            participation_id,
            p_age,
            p_gender_code,
            p_academic_level_code,
            p_race_white_european,
            p_race_black_african,
            p_race_asian,
            p_race_hispanic_latino,
            p_race_middle_eastern_north_african,
            p_race_other,
            case when p_race_other
                then nullif(btrim(p_race_other_description), '') end,
            btrim(p_field_of_study),
            submitted_time
        );
    else
        submitted_time := existing_time;
    end if;

    update public.study_participation
    set status = 'pretest',
        started_at = coalesce(started_at, submitted_time)
    where id = participation_id;

    return submitted_time;
end;
$$;

commit;
