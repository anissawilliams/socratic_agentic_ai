"""Confirm the relational research tables are queryable after migration."""

import sys

from app.services.supabase import get_supabase_client


TABLES = (
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
)


client = get_supabase_client()
failures = []
for table in TABLES:
    try:
        client.table(table).select("*", count="exact").limit(0).execute()
        print(f"ok: {table}")
    except Exception as exc:
        failures.append(f"{table}: {exc}")

if failures:
    print("Relational schema check failed:")
    for failure in failures:
        print(f"  {failure}")
    sys.exit(1)

print("All relational research tables are available.")
