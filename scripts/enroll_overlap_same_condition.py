"""Enroll students who are already in another cohort, keeping their condition.

Each student in --roster must appear in one of the --existing codes files.
They get a new code for the new cohort, in the SAME condition as before,
so nobody experiences both conditions. Not randomized: record this cohort as
excluded from the new class's analysis.

    python -m scripts.enroll_overlap_same_condition \
      --roster rosters/gsu_invoice_overlap.csv --cohort gsu_invoice_overlap \
      --existing rosters/output/gsu_2026_fall_codes.csv \
      --existing rosters/output/gsu_2026_fall_late_codes.csv \
      --instrument round1_invoice_access --pretest-scenario invoice_reconciliation \
      --tutor-scenario invoice_reconciliation --posttest-scenario <posttest_key> \
      --dry-run

Then the same command with --output rosters/output/gsu_invoice_overlap_codes.csv
in place of --dry-run.
"""

import argparse
import csv
import sys
from datetime import datetime, timezone
from pathlib import Path

from scripts.enroll_participants import check_content, read_roster

CODE_PREFIX = "STUDY"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--roster", type=Path, required=True)
    p.add_argument("--cohort", required=True)
    p.add_argument("--existing", type=Path, action="append", required=True)
    p.add_argument("--id-column", default="student_id")
    p.add_argument("--instrument", required=True)
    p.add_argument("--pretest-scenario", required=True)
    p.add_argument("--tutor-scenario", required=True)
    p.add_argument("--posttest-scenario", required=True)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--output", type=Path)
    args = p.parse_args()
    check_content(args)

    previous = {}
    for path in args.existing:
        for row in csv.DictReader(path.open(newline="", encoding="utf-8")):
            previous[row["student_id"]] = row["condition"]

    ids = read_roster(args.roster, args.id_column)
    missing = [i for i in ids if i not in previous]
    if missing:
        raise SystemExit(f"Not in any existing codes file (enroll them normally): {', '.join(missing)}")

    plan = [(i, previous[i]) for i in ids]
    counts = {c: sum(1 for _, x in plan if x == c) for c in {x for _, x in plan}}
    print(f"{args.cohort}: {len(plan)} students, same condition as before -> {counts}")
    print(f"Content: {args.instrument} ({args.pretest_scenario} -> {args.posttest_scenario})")
    if args.dry_run:
        print("\nDry run: nothing written.")
        return

    from app.db.participants import hash_study_code
    from app.services.supabase import get_supabase_client
    from scripts.provision_test_participants import create_participant, generate_study_code

    client = get_supabase_client()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=[
            "student_id", "participant_code", "condition", "cohort",
            "participant_id", "study_participation_id", "note", "enrolled_at",
        ])
        writer.writeheader()
        for index, (ident, condition) in enumerate(plan, start=1):
            code = generate_study_code(prefix=CODE_PREFIX)
            while client.table("study_participant").select("id").eq(
                "access_code_hash", hash_study_code(code)
            ).execute().data:
                code = generate_study_code(prefix=CODE_PREFIX)
            created = create_participant(
                round_number=1,
                condition=condition,
                cohort_code=args.cohort,
                pretest_instrument_key=args.instrument,
                pretest_scenario_key=args.pretest_scenario,
                tutor_scenario_key=args.tutor_scenario,
                posttest_instrument_key=args.instrument,
                posttest_scenario_key=args.posttest_scenario,
                index=index,
                participant_code=code,
                is_test=False,
            )
            writer.writerow({
                "student_id": ident,
                "participant_code": code,
                "condition": condition,
                "cohort": args.cohort,
                "participant_id": created.get("participant_id", ""),
                "study_participation_id": created.get("study_participation_id", ""),
                "note": "already enrolled in another cohort; same condition kept; exclude from this cohort's analysis",
                "enrolled_at": datetime.now(timezone.utc).isoformat(),
            })
            handle.flush()
            print(f"[{index}/{len(plan)}] enrolled ({condition})")
    print(f"\nEnrolled {len(plan)}. Private codes file: {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
