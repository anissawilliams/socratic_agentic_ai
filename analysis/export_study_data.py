"""Export the study tables from Supabase to CSV, complete (no 100-row limit).

Writes one CSV per table into a dated folder, e.g.
    rosters/output/exports/2026-11-08/export_tutor_turn.csv

Everything is exported as stored, test participants included; the analysis
filters to real participants. The folder holds research data: keep it in
rosters/ (git-ignored) and in approved storage only.

    python -m scripts.export_study_data
    python -m scripts.export_study_data --out rosters/output/exports/manual
"""

import argparse
import csv
from datetime import date
from pathlib import Path

from app.services.supabase import get_supabase_client

TABLES = [
    "study_subject",
    "study_participation",
    "demographic_response",
    "assessment_attempt",
    "assessment_answer",
    "tutor_session",
    "tutor_turn",
    "survey_response",
]
# Per-turn evaluator and router records (Socratic only). The table names are
# looked up at run time; to confirm them, run in the Supabase SQL editor:
#   select distinct table_name from information_schema.columns
#   where table_schema = 'public' and column_name in ('evaluated_at', 'routed_at', 'decision_code');
# and put the names in here.
OPTIONAL_TABLES = [
    "response_evaluation",
    "evaluation_avoid_repeating",
    "routing_decision",
    "routing_avoid_repeating",
]
PAGE = 1000


def fetch_all(client, table: str) -> list[dict]:
    rows, start = [], 0
    while True:
        batch = client.table(table).select("*").range(start, start + PAGE - 1).execute().data or []
        rows += batch
        if len(batch) < PAGE:
            return rows
        start += PAGE


def main() -> None:
    parser = argparse.ArgumentParser(description="Export study tables to CSV.")
    parser.add_argument("--out", type=Path,
                        default=Path("rosters/output/exports") / date.today().isoformat())
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    client = get_supabase_client()
    for table in TABLES + OPTIONAL_TABLES:
        try:
            rows = fetch_all(client, table)
        except Exception:
            if table in OPTIONAL_TABLES:
                continue  # no table by that name
            raise
        path = args.out / f"export_{table}.csv"
        if not rows:
            path.write_text("", encoding="utf-8")
            print(f"{table:24s}      0 rows  (empty file)")
            continue
        fields = list(dict.fromkeys(key for row in rows for key in row))
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        print(f"{table:24s} {len(rows):6d} rows")
    print(f"\nWrote files to {args.out}")


if __name__ == "__main__":
    main()