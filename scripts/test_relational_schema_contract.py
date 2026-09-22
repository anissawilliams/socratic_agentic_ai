"""Static contract checks for the tracked relational migration."""

from pathlib import Path
import re

from app.models.evaluation import ResponseEvaluation


MIGRATION = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "001_relational_research_logging.sql"
)
sql = MIGRATION.read_text(encoding="utf-8").lower()

assert " json" not in sql
assert "jsonb" not in sql

required_tables = {
    "study_subject",
    "study_subject_identity_link",
    "study_participation",
    "assessment_attempt",
    "assessment_answer",
    "tutor_session",
    "tutor_turn",
    "response_evaluation",
    "evaluation_avoid_repeating",
    "routing_decision",
    "routing_avoid_repeating",
    "study_event",
}
for table in required_tables:
    assert f"create table if not exists public.{table}" in sql

for field in ResponseEvaluation.model_fields:
    if field == "avoid_repeating":
        continue
    assert field in sql, f"missing typed evaluation field: {field}"

required_functions = {
    "resolve_study_subject",
    "get_current_study_participation",
    "next_study_event_sequence",
    "start_tutor_session",
    "start_tutor_turn",
    "record_tutor_turn",
    "fail_tutor_turn",
    "start_assessment_attempt",
    "submit_assessment_attempt",
    "abandon_assessment_attempt",
}
for function in required_functions:
    assert f"function public.{function}" in sql

for function in required_functions:
    declaration = re.search(
        rf"create or replace function public\.{function}\((.*?)\)\nreturns",
        sql,
        re.DOTALL,
    )
    assert declaration, f"missing declaration for {function}"
    declared_types = [
        parameter.strip().split()[1].replace("(64)", "")
        for parameter in declaration.group(1).split(",")
        if parameter.strip()
    ]
    permission_signatures = re.findall(
        rf"(?:revoke all|grant execute) on function public\.{function}"
        rf"\((.*?)\) (?:from|to)",
        sql,
        re.DOTALL,
    )
    assert len(permission_signatures) == 2, function
    for signature in permission_signatures:
        permission_types = [item.strip() for item in signature.split(",")]
        assert permission_types == declared_types, (
            function,
            declared_types,
            permission_types,
        )

for status in ("started", "completed", "failed"):
    assert f"'{status}'" in sql
assert "unique (study_subject_id, sequence_number)" in sql
assert "generated always as identity" not in sql
assert "tutor_prompt_bundle_sha256" in sql
assert "prompt_sha256 char(64) not null" in sql
assert "evaluator_prompt_sha256 char(64) not null" in sql
assert "router_prompt_sha256 char(64) not null" in sql
assert "status in ('started', 'submitted', 'abandoned')" in sql
assert "assessment_attempt_one_started_idx" in sql
assert "create table if not exists public.demographic_response" not in sql
assert "demographic_response is intentionally deferred" in sql
assert "study_participation_id uuid not null" in sql
assert "p_latency_ms integer" in sql
assert "p_input_tokens integer" in sql
assert "p_output_tokens integer" in sql

required_checks = {
    "check (round_number in (1, 2))",
    "check (stage in ('pretest', 'posttest'))",
    "check (latency_ms >= 0)",
    "check (input_tokens >= 0)",
    "check (output_tokens >= 0)",
    "check (attempt_number >= 1)",
    "check (turn_number >= 1)",
}
for constraint in required_checks:
    assert constraint in sql, f"missing controlled-vocabulary/range constraint: {constraint}"
assert "application_revision" in sql

print("ok")
