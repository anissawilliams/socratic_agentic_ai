# YAML assessment scaffold

Pre-test and post-test content lives in versioned YAML under
`content/assessments/`. This keeps the open-source research instrument
reviewable without putting participant responses in Git.

The draft scaffold provides:

- exactly four open-text questions at each stage;
- different pre-test and post-test scenarios;
- stable question and construct identifiers for later scoring;
- declared instrument and content versions;
- a SHA-256 fingerprint to identify the exact wording shown; and
- a reusable form with no AI feedback or evaluation.

The template is marked `draft`. The loader refuses to serve non-active content
unless a caller explicitly opts into draft loading. Nothing is mounted in
`App.jsx`, so the current tutor remains available without assessment gating.

## Runtime boundaries

- YAML stores scenarios, question wording, versions, and cohort/transfer labels.
- The database stores participant assignments, progress, and submitted answers
  in explicit relational columns and child rows, never generic JSON payloads.
- The backend derives participant identity from `require_participant`.
- Pre-test answers are persisted but never passed to the tutor graph or prompts.
- Scoring runs later and is not part of submission.

## Before integration

1. Replace the bracketed draft content with approved instrument wording.
2. Add the far-transfer instrument and any cohort-specific near-transfer files.
3. Decide scenario assignment and counterbalancing rules.
4. Add idempotent authenticated content/submission endpoints.
5. Add assessment persistence keyed to a pseudonymous study-subject ID.
6. Test the optional flow before making any stage required.

## Attempt lifecycle

Pre-test and post-test are required study stages; the application does not
support silently skipping either one. An accepted attempt starts in `started`.
A valid four-answer submission moves it to `submitted`. If a participant exits
or a researcher terminates an unfinished attempt, it moves to `abandoned` with
a reason code and remains available for attrition/reliability analysis. A retry
is a new row with the next `attempt_number`; abandoned answers are never copied
into it. At most one started attempt may exist per participation and stage.

## Demographics gate

`demographic_response` is deliberately deferred because the approved survey
questions and response vocabularies have not been supplied. The migration does
not create guessed demographic columns. Formal enrollment must not begin until
the approved instrument is represented by explicit typed columns, its content
version/hash are recorded, and its submit-once workflow is tested. No JSON or
generic answer payload is an acceptable temporary substitute.

## Assignment provisioning

The application never randomizes or invents an assignment at login. The
version-controlled service resolves one precomputed `study_participation` and
fails closed when none exists or when its condition/stage does not match the
tutor request. `scripts/import_test_study_assignments.py` validates a reviewed
CSV and is deliberately limited to subjects marked `is_test = true`. Formal
assignment import remains blocked by the demographics gate above. Assignment
CSVs are ignored by Git and must not contain study codes or email addresses;
they use participant UUIDs.

See `RELATIONAL_DATA_MODEL.md` for the normalized persistence and logging
design shared by assessments, demographics, and tutor interactions.
