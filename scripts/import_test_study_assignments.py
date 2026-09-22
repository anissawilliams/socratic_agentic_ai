"""Validate and optionally import precomputed assignments for test subjects only."""

import argparse
import csv
from pathlib import Path

from app.services.condition import tutor_condition_for_participant
from app.services.supabase import get_supabase_client


FIELDS = (
    "participant_id",
    "round_number",
    "cohort_code",
    "transfer_type",
    "assigned_condition_code",
    "pretest_instrument_key",
    "pretest_scenario_key",
    "tutor_scenario_key",
    "posttest_instrument_key",
    "posttest_scenario_key",
    "status",
)
STATUSES = {"not_started", "demographics", "pretest", "tutor", "posttest", "complete"}


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        missing = [field for field in FIELDS if field not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"Assignment CSV is missing columns: {', '.join(missing)}")
        rows = [{field: (row.get(field) or "").strip() for field in FIELDS} for row in reader]

    seen: set[tuple[str, int]] = set()
    for line_number, row in enumerate(rows, start=2):
        if any(not row[field] for field in FIELDS):
            raise ValueError(f"Assignment CSV row {line_number} contains a blank field")
        round_number = int(row["round_number"])
        if round_number not in (1, 2):
            raise ValueError(f"Assignment CSV row {line_number} has invalid round_number")
        if row["transfer_type"] not in {"near", "far"}:
            raise ValueError(f"Assignment CSV row {line_number} has invalid transfer_type")
        expected_transfer = "near" if round_number == 1 else "far"
        if row["transfer_type"] != expected_transfer:
            raise ValueError(
                f"Assignment CSV row {line_number} must use {expected_transfer!r} "
                f"for round {round_number}"
            )
        if row["status"] not in STATUSES:
            raise ValueError(f"Assignment CSV row {line_number} has invalid status")
        tutor_condition_for_participant(
            {"id": row["participant_id"], "condition": row["assigned_condition_code"]}
        )
        key = (row["participant_id"], round_number)
        if key in seen:
            raise ValueError(f"Duplicate participant/round assignment at row {line_number}")
        seen.add(key)
    return rows


def _subject_for_test_participant(client, participant_id: str) -> str:
    response = client.rpc(
        "resolve_study_subject",
        {"p_participant_id": participant_id},
    ).execute()
    subject_id = response.data
    if isinstance(subject_id, list):
        subject_id = subject_id[0] if subject_id else None
    if isinstance(subject_id, dict):
        subject_id = next(iter(subject_id.values()), None)
    if not subject_id:
        raise ValueError(f"Could not resolve participant {participant_id}")
    subject = (
        client.table("study_subject")
        .select("id,is_test")
        .eq("id", str(subject_id))
        .single()
        .execute()
        .data
    )
    if not subject or not subject.get("is_test"):
        raise ValueError(
            f"Refusing formal enrollment for participant {participant_id}; "
            "demographics are explicitly deferred"
        )
    return str(subject_id)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    rows = _rows(args.csv_path)
    print(f"Validated {len(rows)} assignment rows.")
    if not args.apply:
        print("Dry run only; pass --apply to insert test assignments.")
        return

    client = get_supabase_client()
    for row in rows:
        subject_id = _subject_for_test_participant(client, row["participant_id"])
        payload = {field: row[field] for field in FIELDS if field != "participant_id"}
        payload["round_number"] = int(row["round_number"])
        payload["study_subject_id"] = subject_id
        client.table("study_participation").insert(payload).execute()
    print(f"Inserted {len(rows)} test assignment rows.")


if __name__ == "__main__":
    main()
