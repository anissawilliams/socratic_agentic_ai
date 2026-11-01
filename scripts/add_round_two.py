"""Add Round 2 to participants already enrolled in Round 1.

Students keep their Round 1 code and their Round 1 condition. After their
Round 1 is complete, signing in with the same code opens Round 2.

Dry run first (reads the database, writes nothing):

    python -m scripts.add_round_two --codes rosters/output/spain_rerandomized_codes.csv \
      --instrument round2_packaging_painting --pretest-scenario packaging_waste \
      --tutor-scenario packaging_waste --posttest-scenario historical_painting \
      --dry-run

Then run the same command without --dry-run.
"""

import argparse
import csv
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Add Round 2 to enrolled participants.")
    parser.add_argument("--codes", type=Path, required=True,
                        help="the private codes CSV from enroll_participants.py")
    parser.add_argument("--instrument", required=True)
    parser.add_argument("--pretest-scenario", required=True)
    parser.add_argument("--tutor-scenario", required=True)
    parser.add_argument("--posttest-scenario", required=True)
    parser.add_argument("--cohort-suffix", default="",
                        help="optional suffix for Round 2 cohort codes")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.pretest_scenario == args.posttest_scenario:
        parser.error("pretest and posttest scenarios must differ")
    return args


def main() -> None:
    args = parse_args()

    import yaml
    from app.db.participants import hash_study_code
    from app.services.supabase import get_supabase_client

    # Fail early if the Round 2 content isn't in place.
    content = Path(__file__).resolve().parents[1] / "content"
    instrument_path = content / "assessments" / f"{args.instrument}.yaml"
    if not instrument_path.exists():
        raise SystemExit(f"Missing instrument file: {instrument_path}")
    instrument = yaml.safe_load(instrument_path.read_text(encoding="utf-8"))
    if instrument["pretest"]["scenario_key"] != args.pretest_scenario:
        raise SystemExit("--pretest-scenario does not match the instrument")
    if instrument["posttest"]["scenario_key"] != args.posttest_scenario:
        raise SystemExit("--posttest-scenario does not match the instrument")
    if not (content / "scenarios" / f"{args.tutor_scenario}.yaml").exists():
        raise SystemExit(f"Missing tutor scenario file for {args.tutor_scenario}")

    client = get_supabase_client()
    with args.codes.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    added = skipped = 0
    for row in rows:
        code = row["participant_code"]
        participant = (
            client.table("study_participant").select("id")
            .eq("access_code_hash", hash_study_code(code)).limit(1).execute().data
        )
        if not participant:
            print(f"SKIP {code}: no such participant")
            skipped += 1
            continue

        subject_id = client.rpc(
            "resolve_study_subject", {"p_participant_id": participant[0]["id"]}
        ).execute().data
        if isinstance(subject_id, list):
            subject_id = subject_id[0]
        if isinstance(subject_id, dict):
            subject_id = next(iter(subject_id.values()))

        rounds = (
            client.table("study_participation")
            .select("round_number,assigned_condition_code,cohort_code,status")
            .eq("study_subject_id", subject_id).execute().data or []
        )
        round1 = next((r for r in rounds if r["round_number"] == 1), None)
        if round1 is None:
            print(f"SKIP {code}: no Round 1 participation")
            skipped += 1
            continue
        if any(r["round_number"] == 2 for r in rounds):
            print(f"SKIP {code}: Round 2 already added")
            skipped += 1
            continue

        record = {
            "study_subject_id": subject_id,
            "round_number": 2,
            "cohort_code": round1["cohort_code"] + args.cohort_suffix,
            "transfer_type": "far",
            # Same condition as Round 1 (within-subjects consistency).
            "assigned_condition_code": round1["assigned_condition_code"],
            "pretest_instrument_key": args.instrument,
            "pretest_scenario_key": args.pretest_scenario,
            "tutor_scenario_key": args.tutor_scenario,
            "posttest_instrument_key": args.instrument,
            "posttest_scenario_key": args.posttest_scenario,
            "status": "pretest",  # Round 2 has no demographics
        }
        note = "" if round1["status"] == "complete" else f" (Round 1 still {round1['status']})"
        if args.dry_run:
            print(f"WOULD ADD {code}: {record['assigned_condition_code']}{note}")
        else:
            client.table("study_participation").insert(record).execute()
            print(f"ADDED {code}: {record['assigned_condition_code']}{note}")
        added += 1

    verb = "would add" if args.dry_run else "added"
    print(f"\n{verb} {added}, skipped {skipped}")


if __name__ == "__main__":
    main()