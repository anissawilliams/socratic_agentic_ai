-- 007: Demographics per research-team answers.
--   * Age is optional (null when skipped).
--   * Gender gets "Prefer not to answer".
--   * Race/ethnicity gets "Prefer not to answer" (exclusive of other choices).

begin;

alter table public.demographic_response
    alter column age drop not null;

alter table public.demographic_response
    add column if not exists race_prefer_not_to_say boolean not null default false;

-- Replace the table's check constraints (auto-named in earlier migrations).
do $$
declare
    constraint_name text;
begin
    for constraint_name in
        select conname
        from pg_constraint
        where conrelid = 'public.demographic_response'::regclass
          and contype = 'c'
    loop
        execute format(
            'alter table public.demographic_response drop constraint %I',
            constraint_name
        );
    end loop;
end;
$$;

alter table public.demographic_response
    add constraint demographic_age_range
        check (age is null or age between 18 and 99),
    add constraint demographic_gender_code
        check (gender_code in ('male', 'female', 'non_binary', 'prefer_not_to_say')),
    add constraint demographic_academic_level_code
        check (academic_level_code in ('undergraduate', 'graduate')),
    add constraint demographic_field_of_study
        check (length(btrim(field_of_study)) between 1 and 100),
    add constraint demographic_race_other_description
        check (
            (race_other and length(btrim(coalesce(race_other_description, ''))) > 0)
            or (not race_other and race_other_description is null)
        ),
    add constraint demographic_race_answered
        check (
            race_white_european or race_black_african or race_asian
            or race_hispanic_latino or race_middle_eastern_north_african
            or race_other or race_prefer_not_to_say
        ),
    add constraint demographic_race_prefer_not_exclusive
        check (
            not race_prefer_not_to_say
            or not (
                race_white_european or race_black_african or race_asian
                or race_hispanic_latino or race_middle_eastern_north_african
                or race_other
            )
        );

-- Replace the submit function (one more race flag; age may be null).
drop function if exists public.submit_demographics(
    uuid, smallint, text, text, boolean, boolean, boolean, boolean,
    boolean, boolean, text, text
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
    p_race_prefer_not_to_say boolean,
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
            race_prefer_not_to_say,
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
            p_race_prefer_not_to_say,
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
