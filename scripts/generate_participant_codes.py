"""Generate study codes and their database-ready SHA-256 hashes.

This script is intentionally offline: it never connects to or updates the
participant database. Store the generated plaintext codes securely and copy
only the matching hashes into ``study_participant.access_code_hash``.

Example:
    python -m scripts.generate_participant_codes --count 10 --output codes.csv
"""

import argparse
import csv
import secrets
import sys
from pathlib import Path
from typing import TextIO

from app.db.participants import hash_study_code


CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def generate_study_code(prefix: str = "STUDY") -> str:
    """Return a readable code with ambiguous characters excluded."""
    groups = [
        "".join(secrets.choice(CODE_ALPHABET) for _ in range(4))
        for _ in range(2)
    ]
    return "-".join([prefix.strip().upper(), *groups])


def write_codes(destination: TextIO, count: int, prefix: str) -> None:
    writer = csv.DictWriter(
        destination,
        fieldnames=["participant_code", "access_code_hash"],
    )
    writer.writeheader()

    generated: set[str] = set()
    while len(generated) < count:
        code = generate_study_code(prefix)
        if code in generated:
            continue

        generated.add(code)
        writer.writerow(
            {
                "participant_code": code,
                "access_code_hash": hash_study_code(code),
            }
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate participant study codes and database-ready hashes."
        )
    )
    parser.add_argument(
        "--count",
        type=int,
        default=1,
        help="number of unique codes to generate (default: 1)",
    )
    parser.add_argument(
        "--prefix",
        default="STUDY",
        help="readable code prefix (default: STUDY)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="CSV output path (default: standard output)",
    )
    args = parser.parse_args()

    if args.count < 1:
        parser.error("--count must be at least 1")

    if not args.prefix.strip() or not args.prefix.strip().isalnum():
        parser.error("--prefix must contain only letters and numbers")

    return args


def main() -> None:
    args = parse_args()

    if args.output:
        with args.output.open("x", newline="", encoding="utf-8") as output:
            write_codes(output, args.count, args.prefix)
        print(
            f"Wrote {args.count} participant code(s) to {args.output}",
            file=sys.stderr,
        )
        return

    write_codes(sys.stdout, args.count, args.prefix)


if __name__ == "__main__":
    main()
