"""Enroll REAL participants from roster CSVs, with randomized conditions.

- One random access code per student, kept for the whole study.
- Condition by stratified permuted-block randomization: each roster (cohort)
  is shuffled and assigned in blocks of 4 (2 per condition). The seed is
  recorded, so the assignment can be reproduced from the same rosters.
- The roster identifier (student ID or email) is NEVER stored in the
  database. The database gets a placeholder email and the hashed code only.
  The identifier-to-code link exists only in the private --output file.

Dry run (no database writes):

    python -m scripts.enroll_participants \
      --roster rosters/gsu_section_a.csv --cohort gsu_2026_fall_a \
      --roster rosters/gsu_section_b.csv --cohort gsu_2026_fall_b \
      --id-column student_id \
      --instrument round1_hotel_support --pretest-scenario hotel_promotion \
      --tutor-scenario hotel_promotion --posttest-scenario customer_support \
      --seed 20261101 --dry-run

Then the same command with --output rosters/output/gsu_2026_fall_codes.csv
in place of --dry-run. Keep that file private: it links students to codes.
"""

import argparse
import csv
import random
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import yaml

CONDITIONS = ("scenario_questioning", "direct_chat")
CODE_PREFIX = "STUDY"


def read_roster(path: Path, id_column: str) -> list[str]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        columns = {name.strip().lower(): name for name in (reader.fieldnames or [])}
        if id_column.lower() not in columns:
            raise SystemExit(
                f"{path}: no '{id_column}' column (found: {', '.join(reader.fieldnames or [])})"
            )
        source = columns[id_column.lower()]
        ids = [(row.get(source) or "").strip() for row in reader]
    ids = [i for i in ids if i]
    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    if duplicates:
        raise SystemExit(f"{path}: duplicate identifiers: {', '.join(duplicates)}")
    return ids


def assign_conditions(ids: list[str], block_size: int, rng: random.Random):
    """Permuted-block randomization. Returns (identifier, condition, block)."""
    order = sorted(ids)  # result depends only on the seed and who is enrolled
    rng.shuffle(order)
    out = []
    for start in range(0, len(order), block_size):
        block = list(CONDITIONS) * (block_size // len(CONDITIONS))
        rng.shuffle(block)
        for offset, ident in enumerate(order[start:start + block_size]):
            out.append((ident, block[offset], start // block_size + 1))
    return out


def check_content(args) -> None:
    content = Path(__file__).resolve().parents[1] / "content"
    path = content / "assessments" / f"{args.instrument}.yaml"
    if not path.exists():
        raise SystemExit(f"Missing instrument file: {path}")
    instrument = yaml.safe_load(path.read_text(encoding="utf-8"))
    if instrument["pretest"]["scenario_key"] != args.pretest_scenario:
        raise SystemExit("--pretest-scenario does not match the instrument")
    if instrument["posttest"]["scenario_key"] != args.posttest_scenario:
        raise SystemExit("--posttest-scenario does not match the instrument")
    if not (content / "scenarios" / f"{args.tutor_scenario}.yaml").exists():
        raise SystemExit(f"Missing tutor scenario file for {args.tutor_scenario}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Enroll real participants.")
    parser.add_argument("--roster", type=Path, action="append", required=True)
    parser.add_argument("--cohort", action="append", required=True,
                        help="cohort code for each --roster, in the same order")
    parser.add_argument("--id-column", default="student_id",
                        help="roster column with one identifier per student")
    parser.add_argument("--instrument", required=True)
    parser.add_argument("--pretest-scenario", required=True)
    parser.add_argument("--tutor-scenario", required=True)
    parser.add_argument("--posttest-scenario", required=True)
    parser.add_argument("--seed", type=int, required=True,
                        help="randomization seed; record it in your study log")
    parser.add_argument("--block-size", type=int, default=4)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--output", type=Path, help="private codes file to create")
    args = parser.parse_args()

    if len(args.roster) != len(args.cohort):
        parser.error("give one --cohort per --roster")
    if args.block_size % len(CONDITIONS):
        parser.error("--block-size must be a multiple of 2")
    check_content(args)

    rng = random.Random(args.seed)
    plan = []  # (cohort, identifier, condition, block)
    seen = set()
    for roster, cohort in zip(args.roster, args.cohort):
        ids = read_roster(roster, args.id_column)
        clash = seen.intersection(ids)
        if clash:
            raise SystemExit(f"In more than one roster: {', '.join(sorted(clash))}")
        seen.update(ids)
        for ident, condition, block in assign_conditions(ids, args.block_size, rng):
            plan.append((cohort, ident, condition, block))

    print(f"Seed {args.seed}, block size {args.block_size}")
    print(f"Content: {args.instrument} ({args.pretest_scenario} -> "
          f"{args.posttest_scenario}), tutor: {args.tutor_scenario}")
    for cohort in args.cohort:
        rows = [p for p in plan if p[0] == cohort]
        counts = {c: sum(1 for p in rows if p[2] == c) for c in CONDITIONS}
        print(f"  {cohort}: {len(rows)} students -> {counts}")
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
            "student_id", "participant_code", "condition", "cohort", "block",
            "participant_id", "study_participation_id", "seed", "enrolled_at",
        ])
        writer.writeheader()
        for index, (cohort, ident, condition, block) in enumerate(plan, start=1):
            code = generate_study_code(prefix=CODE_PREFIX)
            while client.table("study_participant").select("id").eq(
                "access_code_hash", hash_study_code(code)
            ).execute().data:
                code = generate_study_code(prefix=CODE_PREFIX)

            created = create_participant(
                round_number=1,
                condition=condition,
                cohort_code=cohort,
                pretest_instrument_key=args.instrument,
                pretest_scenario_key=args.pretest_scenario,
                tutor_scenario_key=args.tutor_scenario,
                posttest_instrument_key=args.instrument,
                posttest_scenario_key=args.posttest_scenario,
                index=index,
                participant_code=code,
                is_test=False,
                # Placeholder only: the real identifier never enters the database.
                email=f"participant-{uuid.uuid4().hex[:12]}@study.local",
            )
            writer.writerow({
                "student_id": ident,
                "participant_code": code,
                "condition": condition,
                "cohort": cohort,
                "block": block,
                "participant_id": created["participant_id"],
                "study_participation_id": created["study_participation_id"],
                "seed": args.seed,
                "enrolled_at": datetime.now(timezone.utc).isoformat(),
            })
            handle.flush()  # a crash midway still leaves every created code on disk
            print(f"[{index}/{len(plan)}] {cohort} enrolled")

    print(f"\nEnrolled {len(plan)}. Private codes file: {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()