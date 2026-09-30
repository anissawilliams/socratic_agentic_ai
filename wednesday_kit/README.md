# Wednesday kit: demographics (Round 1) + final survey (Round 2)

Folders mirror the repo, so each file goes to the same path in your project.

## Status flow

    Round 1: demographics -> pretest -> tutor -> posttest -> complete
    Round 2:                 pretest -> tutor -> posttest -> survey -> complete

## Apply, in order

1. New branch from main:
       git checkout main && git pull && git checkout -b feature/demographics-survey

2. Database: copy `01_migration/002_demographics_and_survey.sql` to
   `migrations/`, then run it once in the Supabase SQL editor.
   First confirm the existing constraint name (the migration replaces it):

       select conname from pg_constraint
       where conrelid = 'public.study_participation'::regclass and contype = 'c';

   If it isn't `study_participation_status_check`, change that name in step 1
   of the migration.

3. Backend: copy into the repo
       02_backend/app/api/study_forms.py        -> app/api/study_forms.py
       02_backend/app/main.py                   -> app/main.py   (adds one router)
       02_backend/content/surveys/final_survey.yaml -> content/surveys/final_survey.yaml

4. Frontend: copy into frontend/
       03_frontend/src/api/studyFormsClient.js
       03_frontend/src/components/DemographicsForm.jsx
       03_frontend/src/components/SurveyForm.jsx
       03_frontend/src/App.jsx                  (adds the two new screens)
   Append 03_frontend/src/components/StudyForms.css to the end of
   src/components/AssessmentForm.css (don't copy it as its own file).

5. Scripts: copy both files in 04_scripts/ over the ones in scripts/.
   - Provisioning: Round 1 now starts at `demographics`; `--real` sets
     is_test = false (and requires --output).
   - Smoke test: now covers the demographics step.

6. Restart backend + frontend, then:
       python -m scripts.smoke_test_study_flow --users 1 --max-turns 20

## Before launch: check with the team / IRB

- Age bounds (18-99) in: migration, study_forms.py, DemographicsForm.jsx.
- Demographics match the approved list (age in years, gender, race/ethnicity
  select-all with write-in, field of study as free text). If the team drops age or race, tell Claude: it is
  a small change in the same three files.
- Survey items in final_survey.yaml are PLACEHOLDERS. Replace them with the
  adapted Java Tutor items and bump `version`.

## Verified

- Migration run on real Postgres: demographics -> pretest, duplicate submits
  ignored, Round 1 still ends at complete, Round 2 posttest -> survey -> complete.
- Endpoints tested with a stubbed database (validation, wrong-stage 409s).
- Frontend builds; new files lint clean.
- Not tested against your live Supabase: that's step 6.
