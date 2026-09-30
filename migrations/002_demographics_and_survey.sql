-- 002: Round 1 demographics and Round 2 final survey.
--
-- Status flow after this migration:
--   Round 1: demographics -> pretest -> tutor -> posttest -> complete
--   Round 2:                 pretest -> tutor -> posttest -> survey -> complete
--
-- Typed columns only (no untyped payloads), per the note in migration 001.
-- Run once in the Supabase SQL editor. Wrapped in a transaction.

begin;

-- 1. Allow the 'survey' status. -------------------------------------------
alter table public.study_participation
    drop constraint if exists study_participation_status_check;

alter table public.study_participation
    add constraint study_participation_status_check check (
        status in (
            'not_started',
            'demographics',
            'pretest',
            'tutor',
            'posttest',
            'survey',
            'complete'
        )
    );

-- 2. Demographics: once per study subject (collected in Round 1 only). ------
-- Mirrors the approved question list: age in years, gender, and
-- race/ethnicity (select all that apply, with a write-in), and field of
-- study (free text).
create table if not exists public.demographic_response (
    study_subject_id uuid primary key
        references public.study_subject(id) on delete cascade,
    study_participation_id uuid not null
        references public.study_participation(id) on delete cascade,
    age smallint not null check (age between 18 and 99),
    gender_code text not null check (
        gender_code in ('male', 'female', 'non_binary')
    ),
    race_white_european boolean not null default false,
    race_black_african boolean not null default false,
    race_asian boolean not null default false,
    race_hispanic_latino boolean not null default false,
    race_middle_eastern_north_african boolean not null default false,
    race_other boolean not null default false,
    race_other_description text,
    field_of_study text not null check (
        length(btrim(field_of_study)) between 1 and 100
    ),
    submitted_at timestamptz not null default now(),
    check (
        (race_other and length(btrim(coalesce(race_other_description, ''))) > 0)
        or (not race_other and race_other_description is null)
    ),
    check (
        race_white_european or race_black_african or race_asian
        or race_hispanic_latino or race_middle_eastern_north_african
        or race_other
    )
);

alter table public.demographic_response enable row level security;

-- 3. Final survey: once per participation (Round 2 only). ----------------
create table if not exists public.survey_response (
    study_participation_id uuid primary key
        references public.study_participation(id) on delete cascade,
    study_subject_id uuid not null
        references public.study_subject(id) on delete cascade,
    instrument_key text not null,
    instrument_version text not null,
    likert_1 smallint not null check (likert_1 between 1 and 5),
    likert_2 smallint not null check (likert_2 between 1 and 5),
    likert_3 smallint not null check (likert_3 between 1 and 5),
    likert_4 smallint not null check (likert_4 between 1 and 5),
    open_response text,
    submitted_at timestamptz not null default now()
);

alter table public.survey_response enable row level security;

-- 4. Round 2: finishing the post-test goes to 'survey', not 'complete'. ----
-- A trigger keeps the existing assessment-submit function untouched.
create or replace function public.route_round2_posttest_to_survey()
returns trigger
language plpgsql
as $$
begin
    if old.status = 'posttest'
       and new.status = 'complete'
       and new.round_number = 2 then
        new.status := 'survey';
        new.completed_at := null;
    end if;
    return new;
end;
$$;

drop trigger if exists route_round2_posttest_to_survey
    on public.study_participation;

create trigger route_round2_posttest_to_survey
    before update of status on public.study_participation
    for each row
    execute function public.route_round2_posttest_to_survey();

-- 5. Submit demographics (idempotent). -------------------------------------
create or replace function public.submit_demographics(
    p_participant_id uuid,
    p_age smallint,
    p_gender_code text,
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
            return existing_time;  -- already submitted; nothing to do
        end if;
        raise exception 'Participant is not at the demographics stage';
    end if;

    if existing_time is null then
        insert into public.demographic_response(
            study_subject_id,
            study_participation_id,
            age,
            gender_code,
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
        -- Demographics already on file (e.g., re-enrolled): just move on.
        submitted_time := existing_time;
    end if;

    update public.study_participation
    set status = 'pretest',
        started_at = coalesce(started_at, submitted_time)
    where id = participation_id;

    return submitted_time;
end;
$$;

-- 6. Submit final survey (idempotent). -------------------------------------
create or replace function public.submit_final_survey(
    p_participant_id uuid,
    p_instrument_key text,
    p_instrument_version text,
    p_likert_1 smallint,
    p_likert_2 smallint,
    p_likert_3 smallint,
    p_likert_4 smallint,
    p_open_response text
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
            return existing_time;
        end if;
        raise exception 'Participant is not at the survey stage';
    end if;

    insert into public.survey_response(
        study_participation_id,
        study_subject_id,
        instrument_key,
        instrument_version,
        likert_1, likert_2, likert_3, likert_4,
        open_response,
        submitted_at
    ) values (
        participation_id,
        subject_id,
        p_instrument_key,
        p_instrument_version,
        p_likert_1, p_likert_2, p_likert_3, p_likert_4,
        nullif(btrim(p_open_response), ''),
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
