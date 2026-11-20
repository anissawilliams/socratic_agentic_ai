-- 010: optional "What is your primary language?" in Round 1 demographics.
-- Nullable column, so every demographics row already submitted stays valid.
-- submit_demographics is unchanged; the API saves this answer to the row the
-- function creates. Asked from 2026-11-20 (Germany and later cohorts).
-- Run once in the Supabase SQL editor.

begin;

alter table public.demographic_response
    add column if not exists primary_language text;

alter table public.demographic_response
    drop constraint if exists demographic_response_primary_language_length;

alter table public.demographic_response
    add constraint demographic_response_primary_language_length
    check (primary_language is null or char_length(btrim(primary_language)) between 1 and 100);

-- Undo the survey version of this question (009), if it was run. The column
-- was never used.
alter table public.survey_response
    drop constraint if exists survey_response_primary_language_length;
alter table public.survey_response
    drop column if exists primary_language;

commit;
