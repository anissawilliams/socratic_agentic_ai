"""Enroll a class roster: create a study code per student, randomly assign
conditions (balanced), and write one CSV ready for mail merge.

    python -m scripts.enroll_roster roster.csv --cohort spain_2026_fall \
        --output spain_2026_fall_codes.csv

    # Check the roster and the planned split without touching the database:
    python -m scripts.enroll_roster roster.csv --cohort spain_2026_fall \
        --output x.csv --dry-run

Roster CSV: needs a name column and an email column (detected by header, e.g.
"Name"/"Nombre" and "Email"/"Correo"; or pass --name-col/--email-col).

Output CSV: name, email, participant_code, condition. Use name/email/code for
the mail merge. This file is the ONLY link between students and codes (the
database stores only a hash of each code, and no names or emails), so keep it
private and out of git.

Conditions are balanced (for an odd count, the extra slot goes to a randomly
chosen condition) and assigned by a cryptographically random shuffle.
Participants are created with is_test = false and STUDY- codes.
"""

import argparse
import csv
import secrets
import sys
from pathlib import Path

from scripts.provision_test_participants import create_participant

CONDITIONS = ("scenario_questioning", "direct_chat")

NAME_HEADERS = ("name", "nombre", "student")
EMAIL_HEADERS = ("email", "e-mail", "correo", "mail")


def find_column(headers, candidates, explicit, label):
    if explicit:
        if explicit not in headers:
            sys.exit(f"Column {explicit!r} not found. Columns: {headers}")
        return explicit
    for header in headers:
        if any(word in header.lower() for word in candidates):
            return header
    sys.exit(f"No {label} column found in {headers}; pass --{label}-col.")


def read_roster(path: Path, name_col: str | None, email_col: str | None):
    # utf-8-sig handles the byte-order mark Excel adds to CSV exports.
    with path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        headers = [h.strip() for h in (reader.fieldnames or [])]
        reader.fieldnames = headers
        name_col = find_column(headers, NAME_HEADERS, name_col, "name")
        email_col = find_column(headers, EMAIL_HEADERS, email_col, "email")
        students = [
            {"name": (row[name_col] or "").strip(),
             "email": (row[email_col] or "").strip()}
            for row in reader
            if (row[name_col] or "").strip() or (row[email_col] or "").strip()
        ]

    if not students:
        sys.exit("The roster has no students.")
    no_email = [s["name"] or "(blank name)" for s in students if not s["email"]]
    if no_email:
        sys.exit(f"Missing email for: {', '.join(no_email)}")
    emails = [s["email"].lower() for s in students]
    dupes = sorted({e for e in emails if emails.count(e) > 1})
    if dupes:
        sys.exit(f"Duplicate emails in roster: {', '.join(dupes)}")
    return students


def balanced_conditions(count: int) -> list[str]:
    rng = secrets.SystemRandom()
    order = list(CONDITIONS)
    rng.shuffle(order)  # who gets the extra slot on an odd count is random
    conditions = [order[i % len(order)] for i in range(count)]
    rng.shuffle(conditions)
    return conditions


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("roster", type=Path)
    parser.add_argument("--cohort", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--round", type=int, choices=(1, 2), default=1)
    parser.add_argument("--pretest-instrument", default="round1_energy_cooling")
    parser.add_argument("--pretest-scenario", default="energy_assistance")
    parser.add_argument("--tutor-scenario", default="energy_assistance")
    parser.add_argument("--posttest-instrument", default="round1_energy_cooling")
    parser.add_argument("--posttest-scenario", default="cooling_centers")
    parser.add_argument("--name-col")
    parser.add_argument("--email-col")
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate and show the planned split; create nothing.")
    args = parser.parse_args()

    if args.round == 2 and args.pretest_instrument == "round1_energy_cooling":
        parser.error("Round 2 needs explicit far-transfer instrument and scenario keys.")
    if args.output.exists():
        sys.exit(f"{args.output} already exists; refusing to overwrite saved codes.")

    students = read_roster(args.roster, args.name_col, args.email_col)
    conditions = balanced_conditions(len(students))
    split = {c: conditions.count(c) for c in CONDITIONS}

    print(f"{len(students)} students, cohort {args.cohort!r}, round {args.round}")
    print(f"Split: {split}")
    print(f"Pretest {args.pretest_instrument}/{args.pretest_scenario}, "
          f"tutor {args.tutor_scenario}, "
          f"posttest {args.posttest_instrument}/{args.posttest_scenario}")

    if args.dry_run:
        print("\nDry run: nothing was created.")
        return

    # Each row is written and flushed as soon as its participant exists, so a
    # failure partway through never loses a code that is already in the database.
    with args.output.open("x", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["name", "email", "participant_code", "condition"])
        fh.flush()
        for index, (student, condition) in enumerate(zip(students, conditions), 1):
            created = create_participant(
                round_number=args.round,
                condition=condition,
                cohort_code=args.cohort,
                pretest_instrument_key=args.pretest_instrument,
                pretest_scenario_key=args.pretest_scenario,
                tutor_scenario_key=args.tutor_scenario,
                posttest_instrument_key=args.posttest_instrument,
                posttest_scenario_key=args.posttest_scenario,
                index=index,
                is_test=False,
            )
            writer.writerow([student["name"], student["email"],
                             created["participant_code"], condition])
            fh.flush()
            print(f"[{index}/{len(students)}] {created['participant_code']}")

    print(f"\nDone. Codes saved to {args.output}")


if __name__ == "__main__":
    main()
