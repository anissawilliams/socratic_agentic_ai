"""Provision test participants and study assignments.

Creates:
- study_participant
- study_subject (via resolve_study_subject RPC)
- study_subject_identity_link (via resolve_study_subject RPC)
- study_participation

Does NOT create:
- assessment attempts
- tutor sessions
- study events

Those must be created by the real application flow so they can be tested.

To provision the three codes reserved for the next Round 1 test:
    python -m scripts.provision_test_participants \
      --code TEST-2S65-BCNL \
      --code TEST-396D-T7RM \
      --code TEST-PKCU-VMFG \
      --output new_test_participants.csv
"""

import argparse
import csv
import re
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path

from app.db.participants import hash_study_code, normalize_study_code
from app.services.supabase import get_supabase_client


CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def generate_study_code(prefix: str = "TEST") -> str:
    groups = [
        "".join(secrets.choice(CODE_ALPHABET) for _ in range(4))
        for _ in range(2)
    ]
    return "-".join([prefix.strip().upper(), *groups])


def make_test_email(index: int) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    return f"test-{timestamp}-{index}@study.local"


def create_participant(
    *,
    round_number: int,
    condition: str,
    cohort_code: str,
    pretest_instrument_key: str,
    pretest_scenario_key: str,
    tutor_scenario_key: str,
    posttest_instrument_key: str,
    posttest_scenario_key: str,
    index: int,
    participant_code: str | None = None,
) -> dict:
    supabase = get_supabase_client()

    participant_code = participant_code or generate_study_code()
    access_code_hash = hash_study_code(participant_code)
    email = make_test_email(index)

    # 1. Create authentication participant.
    participant_response = (
        supabase
        .table("study_participant")
        .insert(
            {
                "email": email,
                "condition": condition,
                "access_code_hash": access_code_hash,
                "is_test": True,
            }
        )
        .execute()
    )

    if not participant_response.data:
        raise RuntimeError("Failed to create study_participant")

    participant = participant_response.data[0]
    participant_id = participant["id"]

    # 2. Resolve/create pseudonymous research subject + identity link.
    subject_response = (
        supabase
        .rpc(
            "resolve_study_subject",
            {"p_participant_id": participant_id},
        )
        .execute()
    )

    if not subject_response.data:
        raise RuntimeError(
            f"Failed to resolve study_subject for participant {participant_id}"
        )

    study_subject_id = subject_response.data

    # Some Supabase responses may wrap scalar values.
    if isinstance(study_subject_id, list):
        if not study_subject_id:
            raise RuntimeError("resolve_study_subject returned an empty result")
        study_subject_id = study_subject_id[0]
    if isinstance(study_subject_id, dict):
        study_subject_id = next(iter(study_subject_id.values()), None)
    if not study_subject_id:
        raise RuntimeError("resolve_study_subject returned no subject ID")

    # Round determines transfer type under the current schema constraint.
    transfer_type = "near" if round_number == 1 else "far"

    # Start at pretest for now.
    # When demographics is implemented for Round 1, this can become
    # "demographics" for Round 1 participants.
    starting_status = "pretest"

    # 3. Create assignment/progress row.
    participation_response = (
        supabase
        .table("study_participation")
        .insert(
            {
                "study_subject_id": study_subject_id,
                "round_number": round_number,
                "cohort_code": cohort_code,
                "transfer_type": transfer_type,
                "assigned_condition_code": condition,
                "pretest_instrument_key": pretest_instrument_key,
                "pretest_scenario_key": pretest_scenario_key,
                "tutor_scenario_key": tutor_scenario_key,
                "posttest_instrument_key": posttest_instrument_key,
                "posttest_scenario_key": posttest_scenario_key,
                "status": starting_status,
            }
        )
        .execute()
    )

    if not participation_response.data:
        raise RuntimeError(
            f"Failed to create study_participation for participant {participant_id}"
        )

    participation = participation_response.data[0]

    return {
        "participant_code": participant_code,
        "participant_id": participant_id,
        "study_subject_id": study_subject_id,
        "study_participation_id": participation["id"],
        "round_number": round_number,
        "condition": condition,
        "email": email,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Provision fresh test participants."
    )

    code_source = parser.add_mutually_exclusive_group()
    code_source.add_argument("--count", type=int, default=None)
    code_source.add_argument(
        "--code",
        action="append",
        dest="codes",
        help="an exact unused TEST-XXXX-XXXX code; repeat for multiple users",
    )
    parser.add_argument("--round", type=int, choices=(1, 2), default=1)
    parser.add_argument("--condition", default="scenario_questioning")

    parser.add_argument(
        "--cohort",
        default="test",
        help="study_participation.cohort_code",
    )

    parser.add_argument("--pretest-instrument", default="test_near_transfer")
    parser.add_argument("--pretest-scenario", default="test_citation_pre")
    parser.add_argument("--tutor-scenario", default="citation_quality")
    parser.add_argument("--posttest-instrument", default="test_near_transfer")
    parser.add_argument("--posttest-scenario", default="test_citation_post")

    parser.add_argument(
        "--output",
        type=Path,
        help="optional CSV file for plaintext test credentials",
    )

    args = parser.parse_args()

    if args.count is not None and args.count < 1:
        parser.error("--count must be at least 1")

    if args.codes:
        invalid = [
            code for code in args.codes
            if not re.fullmatch(r"TEST-[A-HJ-NP-Z2-9]{4}-[A-HJ-NP-Z2-9]{4}", code)
        ]
        if invalid:
            parser.error(f"Invalid test code(s): {', '.join(invalid)}")
        if len({normalize_study_code(code) for code in args.codes}) != len(args.codes):
            parser.error("--code values must be unique")

    if args.round == 2 and args.pretest_instrument == "test_near_transfer":
        parser.error("Round 2 requires an explicit far-transfer instrument and scenarios")

    if args.pretest_scenario == args.posttest_scenario:
        parser.error(
            "--pretest-scenario and --posttest-scenario must be different"
        )

    return args


def main() -> None:
    args = parse_args()

    if args.output and args.output.exists():
        raise FileExistsError(
            f"{args.output} already exists; refusing to create participants without saving their codes"
        )

    if args.codes:
        hashes = [hash_study_code(code) for code in args.codes]
        existing = (
            get_supabase_client()
            .table("study_participant")
            .select("id,access_code_hash")
            .in_("access_code_hash", hashes)
            .execute()
            .data
        )
        if existing:
            raise RuntimeError(
                "One or more supplied codes already belong to a participant; "
                "no new users were created."
            )

    created = []

    codes = args.codes or [None] * (args.count or 1)
    for index, code in enumerate(codes, start=1):
        participant = create_participant(
            round_number=args.round,
            condition=args.condition,
            cohort_code=args.cohort,
            pretest_instrument_key=args.pretest_instrument,
            pretest_scenario_key=args.pretest_scenario,
            tutor_scenario_key=args.tutor_scenario,
            posttest_instrument_key=args.posttest_instrument,
            posttest_scenario_key=args.posttest_scenario,
            index=index,
            participant_code=code,
        )

        created.append(participant)

        print(
            f"[{index}] "
            f"{participant['participant_code']} "
            f"(participant={participant['participant_id']}, "
            f"participation={participant['study_participation_id']})"
        )

    if args.output:
        with args.output.open("x", newline="", encoding="utf-8") as output:
            writer = csv.DictWriter(
                output,
                fieldnames=[
                    "participant_code",
                    "participant_id",
                    "study_subject_id",
                    "study_participation_id",
                    "round_number",
                    "condition",
                    "email",
                ],
            )
            writer.writeheader()
            writer.writerows(created)

        print(
            f"\nWrote test credentials to {args.output}",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
