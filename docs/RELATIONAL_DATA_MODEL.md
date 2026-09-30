# Relational research-data model

The target study schema uses explicit typed columns and relational child tables.
Research data must not be stored in generic JSON/JSONB payloads. YAML remains
the source for public instrument and scenario content; PostgreSQL stores
assignments, responses, tutor interactions, and provenance.

The current production tables `tutor_sessions.state` and `tutor_events.data`
are JSON-based and must be migrated before formal data collection.

## Identity separation

### `study_subject`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | UUID PK | Pseudonymous research identifier |
| `created_at` | TIMESTAMPTZ | Server generated |
| `is_test` | BOOLEAN | Exclude pilots from research exports |
| `next_event_sequence` | BIGINT | Next subject-local audit sequence, allocated atomically |

### `study_subject_identity_link`

Access-restricted table kept outside analysis exports.

| Column | Type | Notes |
| --- | --- | --- |
| `study_subject_id` | UUID PK/FK | References `study_subject.id` |
| `participant_id` | UUID UNIQUE/FK | References authentication record |
| `linked_at` | TIMESTAMPTZ | Server generated |
| `detached_at` | TIMESTAMPTZ NULL | Set when identity is removed |

No research table stores email, study code, code hash, or authorization data.

## Assignment and progress

### `study_participation`

| Column | Type |
| --- | --- |
| `id` | UUID PK |
| `study_subject_id` | UUID FK |
| `round_number` | SMALLINT |
| `cohort_code` | TEXT |
| `transfer_type` | TEXT |
| `assigned_condition_code` | TEXT |
| `pretest_instrument_key` | TEXT |
| `pretest_scenario_key` | TEXT |
| `tutor_scenario_key` | TEXT |
| `posttest_instrument_key` | TEXT |
| `posttest_scenario_key` | TEXT |
| `status` | TEXT |
| `started_at` | TIMESTAMPTZ NULL |
| `completed_at` | TIMESTAMPTZ NULL |

Unique constraint: `(study_subject_id, round_number)`.

## One-time demographics

### `demographic_response`

Final columns depend on the approved survey. Each fixed question receives an
explicit typed column, for example:

| Column | Type |
| --- | --- |
| `id` | UUID PK |
| `study_subject_id` | UUID UNIQUE/FK |
| `instrument_version` | TEXT |
| `content_sha256` | CHAR(64) |
| `age_range_code` | TEXT NULL |
| `gender_code` | TEXT NULL |
| `race_ethnicity_code` | TEXT NULL |
| `discipline_code` | TEXT NULL |
| `academic_level_code` | TEXT NULL |
| `started_at` | TIMESTAMPTZ |
| `submitted_at` | TIMESTAMPTZ |

Optional questions use nullable columns. “Prefer not to answer” remains an
explicit code rather than being conflated with null or missing data.

This table is intentionally deferred from migration 001 because the approved
question set is not yet available. Formal participant enrollment is blocked
until a follow-up migration defines these typed columns and the one-time survey
workflow is tested. The implementation must not use JSON as an interim store.

## Pre/post assessments

### `assessment_attempt`

| Column | Type |
| --- | --- |
| `id` | UUID PK |
| `study_participation_id` | UUID FK |
| `stage` | TEXT (`pretest`, `posttest`) |
| `instrument_key` | TEXT |
| `instrument_version` | TEXT |
| `content_sha256` | CHAR(64) |
| `scenario_key` | TEXT |
| `scenario_version` | TEXT |
| `scenario_sha256` | CHAR(64) |
| `attempt_number` | SMALLINT |
| `idempotency_key` | UUID UNIQUE |
| `status` | TEXT (`started`, `submitted`, `abandoned`) |
| `started_at` | TIMESTAMPTZ |
| `submitted_at` | TIMESTAMPTZ NULL |
| `abandoned_at` | TIMESTAMPTZ NULL |
| `abandonment_reason_code` | TEXT NULL |

Unique constraint: `(study_participation_id, stage, attempt_number)`.
Only one `started` attempt may exist for a participation/stage. Required stages
cannot be skipped. An abandoned attempt remains immutable and a retry receives
the next attempt number.

### `assessment_answer`

One row per open-text response.

| Column | Type |
| --- | --- |
| `id` | UUID PK |
| `assessment_attempt_id` | UUID FK |
| `question_id` | TEXT |
| `construct_code` | TEXT |
| `display_order` | SMALLINT |
| `response_text` | TEXT |
| `submitted_at` | TIMESTAMPTZ |

Unique constraint: `(assessment_attempt_id, question_id)`.

Future scoring belongs in separate versioned tables; it never overwrites the
learner's original text.

## Tutor session

### `tutor_session`

| Column | Type |
| --- | --- |
| `id` | UUID PK |
| `study_participation_id` | UUID FK |
| `assigned_condition_code` | TEXT |
| `runtime_condition_code` | TEXT |
| `scenario_key` | TEXT |
| `scenario_version` | TEXT |
| `scenario_sha256` | CHAR(64) |
| `tutor_prompt_bundle_key` | TEXT |
| `tutor_prompt_bundle_version` | TEXT |
| `tutor_prompt_bundle_sha256` | CHAR(64) |
| `prompt_sha256` | CHAR(64) |
| `application_revision` | TEXT |
| `model_name` | TEXT |
| `status` | TEXT |
| `current_phase_code` | TEXT NULL |
| `started_at` | TIMESTAMPTZ |
| `updated_at` | TIMESTAMPTZ |
| `completed_at` | TIMESTAMPTZ NULL |

### `tutor_turn`

One row represents one attempted learner/tutor exchange and replaces message
and event JSON. A turn begins when the learner message is accepted and the
`started` row is committed. It ends when the corresponding tutor response is
committed (`completed`) or when processing terminates with an error (`failed`).

The evaluation and routing records attached to a turn describe processing of
that turn's learner message and selection of that turn's tutor response. They
do not describe or prepare the next numbered turn. For example, turn 7 owns:

- `tutor_turn.turn_number = 7`, including its `student_message`;
- the `response_evaluation` whose `tutor_turn_id` references turn 7;
- the `routing_decision` whose `tutor_turn_id` references turn 7; and
- turn 7's `tutor_response`.

| Column | Type |
| --- | --- |
| `id` | UUID PK |
| `tutor_session_id` | UUID FK |
| `turn_number` | INTEGER |
| `student_message` | TEXT |
| `status` | TEXT (`started`, `completed`, `failed`) |
| `tutor_response` | TEXT NULL |
| `phase_before_code` | TEXT NULL |
| `phase_after_code` | TEXT NULL |
| `started_at` | TIMESTAMPTZ |
| `completed_at` | TIMESTAMPTZ NULL |
| `failed_at` | TIMESTAMPTZ NULL |
| `latency_ms` | INTEGER NULL |
| `model_name` | TEXT |
| `tutor_prompt_bundle_key` | TEXT |
| `tutor_prompt_bundle_version` | TEXT |
| `tutor_prompt_bundle_sha256` | CHAR(64) |
| `prompt_sha256` | CHAR(64) |
| `application_revision` | TEXT |
| `input_tokens` | INTEGER NULL |
| `output_tokens` | INTEGER NULL |
| `error_code` | TEXT NULL |
| `error_detail` | TEXT NULL |

Unique constraint: `(tutor_session_id, turn_number)`.

A learner submission creates the turn as `started` before model execution.
Exactly one terminal transition follows: `started -> completed` after the
tutor reply and diagnostics have been committed atomically, or `started ->
failed` when invocation/persistence raises an error. A row left `started`
after process termination is an incomplete/abandoned attempt and can be
identified operationally by age. Failed and incomplete rows remain available
for reliability analysis but are excluded from conversation reconstruction.
`turn_number` counts attempts, including failed/incomplete ones; it is not a
count of successful exchanges.

`started_at` is the time the learner message was durably accepted.
`completed_at` is the time the response and same-turn diagnostics were
committed. `failed_at` is the time the attempt was terminally marked failed.
Exactly one of `completed_at` and `failed_at` is populated for a terminal
turn; both remain null while a turn is incomplete.

`latency_ms` measures wall-clock graph execution from immediately before the
first model call through completion or failure. `input_tokens` and
`output_tokens` are the sums of provider-reported usage across evaluator,
router (including retries), and tutor-generation calls in that turn. They are
null—not zero—when the provider supplies no usage metadata. A zero value means
usage metadata was supplied and reported zero.

### `response_evaluation`

One-to-one with `tutor_turn`; every current Pydantic field becomes a column.
It evaluates the learner message in that same turn number.

| Column | Type |
| --- | --- |
| `tutor_turn_id` | UUID PK/FK |
| `phase_goal_satisfied` | BOOLEAN |
| `decision_code` | TEXT |
| `reasoning_summary` | TEXT |
| `evidence` | TEXT |
| `learner_contribution` | TEXT |
| `addressed_question` | TEXT |
| `unresolved_issue` | TEXT NULL |
| `follow_up_target` | TEXT NULL |
| `session_goal_satisfied` | BOOLEAN |
| `session_unresolved_issue` | TEXT NULL |
| `session_completion_reason` | TEXT NULL |
| `evaluator_model_name` | TEXT |
| `evaluator_prompt_version` | TEXT |
| `evaluator_prompt_sha256` | CHAR(64) |
| `application_revision` | TEXT |
| `evaluated_at` | TIMESTAMPTZ |

### `evaluation_avoid_repeating`

| Column | Type |
| --- | --- |
| `tutor_turn_id` | UUID FK |
| `item_order` | SMALLINT |
| `content` | TEXT |

Primary key: `(tutor_turn_id, item_order)`.

### `routing_decision`

One-to-one with `tutor_turn`. It records the phase/move selected to generate
the tutor response in that same turn number, not the following turn.

| Column | Type |
| --- | --- |
| `tutor_turn_id` | UUID PK/FK |
| `action_code` | TEXT |
| `selected_phase_code` | TEXT |
| `topic_code` | TEXT |
| `move_type_code` | TEXT |
| `target` | TEXT |
| `reasoning_summary` | TEXT |
| `router_model_name` | TEXT |
| `router_prompt_version` | TEXT |
| `router_prompt_sha256` | CHAR(64) |
| `application_revision` | TEXT |
| `routed_at` | TIMESTAMPTZ |

### `routing_avoid_repeating`

| Column | Type |
| --- | --- |
| `tutor_turn_id` | UUID FK |
| `item_order` | SMALLINT |
| `content` | TEXT |

Primary key: `(tutor_turn_id, item_order)`.

Phase and routing history are derived by ordering `tutor_turn.turn_number`.
They are not duplicated as arrays or JSON snapshots.

## Typed audit envelope

### `study_event`

This table records lifecycle ordering, not arbitrary payloads.

| Column | Type |
| --- | --- |
| `id` | UUID PK |
| `study_subject_id` | UUID FK |
| `study_participation_id` | UUID FK NULL |
| `assessment_attempt_id` | UUID FK NULL |
| `tutor_session_id` | UUID FK NULL |
| `tutor_turn_id` | UUID FK NULL |
| `event_type_code` | TEXT |
| `event_schema_version` | TEXT |
| `sequence_number` | BIGINT |
| `occurred_at` | TIMESTAMPTZ |
| `recorded_at` | TIMESTAMPTZ |
| `idempotency_key` | UUID UNIQUE |

Event-specific values live in their typed tables above. `study_event` contains
no payload column.

`sequence_number` is a gap-free-at-commit, monotonically increasing sequence
within one `study_subject_id`, allocated inside the same transaction as the
event. It orders all recorded lifecycle events for that subject across rounds,
assessments, sessions, and event types. It has no meaning across different
subjects, does not encode elapsed time, and does not replace `occurred_at` or
`recorded_at`. The unique key is `(study_subject_id, sequence_number)`.

Prompt provenance identifies the exact executable prompt/policy bundle. The
key names the bundle, the human-managed version supports release reporting,
the SHA-256 is computed deterministically from all prompt, evaluator, and
routing source files, and `application_revision` identifies the deployed app
revision. The hash—not the version label—is the integrity check.

`tutor_prompt_bundle_version` means the version of the complete configured
tutor system, not the version of whichever phase happened to generate one
response. The version-controlled manifest at
`content/prompts/tutor_prompt_bundle.yaml` maps that bundle version to explicit
versions for shared context, base, Elenchus, Aporia, Maieutics, Dialectic,
evaluator, and router components. The manifest itself is included in every
relevant hash, so changing a component version changes provenance even before
prompt text changes.

Component hashes make consequential changes independently traceable:
`prompt_sha256` covers shared context plus tutor-generation prompts;
`evaluator_prompt_sha256` covers shared context plus evaluator prompt and
policy code; and `router_prompt_sha256` covers shared context plus router
prompt and policy code. The bundle hash covers the union of all three. Thus a
router-only change alters the router and bundle hashes without falsely
claiming that the tutor-generation prompt itself changed.

## Migration strategy

1. Add version-controlled relational migrations; remove the blanket `*.sql`
   ignore rule or use a dedicated tracked migration directory.
2. Create typed v2 tables without changing current reads.
3. Dual-write typed records while production remains available.
4. Backfill existing test rows from JSON once, retaining a reconciliation log.
5. Compare row counts, required fields, hashes, and session reconstruction.
6. Switch reads and exports to typed tables.
7. Stop JSON writes, archive the old tables, then remove them after verification.

Writes spanning multiple tables must run in a PostgreSQL transaction, ideally
through a database function or direct transactional connection rather than a
sequence of independent REST calls.
