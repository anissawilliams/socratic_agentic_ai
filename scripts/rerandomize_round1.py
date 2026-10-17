"""Re-randomize Round 1 before anyone has started (one student withdrew).

Codes do NOT change. The condition is updated in both places it is stored
(study_participant.condition and study_participation.assigned_condition_code),
and only for students whose Round 1 is still at 'demographics'. Rows are found
by participant code, so the codes file only needs email and participant_code. The withdrawn student's
row is left untouched (not reassigned, not deleted) and is listed in the
new file as excluded.

Dry run first (no writes):
    python -m scripts.rerandomize_round1 --codes ~/Private/ds9101_codes.csv \
      --exclude student@cofc.edu --seed <NEW_SEED> --dry-run

Then for real:
    python -m scripts.rerandomize_round1 --codes ~/Private/ds9101_codes.csv \
      --exclude student@cofc.edu --seed <NEW_SEED> \
      --output ~/Private/ds9101_codes_rerandomized.csv
"""

import argparse
import csv
import random
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

CONDITIONS = ("scenario_questioning", "direct_chat")


def assign(emails, block_size, rng):
    order = sorted(emails)  # result depends only on seed + who is included
    rng.shuffle(order)
    out = {}
    for start in range(0, len(order), block_size):
        block = list(CONDITIONS) * (block_size // len(CONDITIONS))
        rng.shuffle(block)
        for offset, email in enumerate(order[start:start + block_size]):
            out[email] = (block[offset], start // block_size + 1)
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--codes", type=Path, required=True)
    p.add_argument("--exclude", action="append", required=True, help="email of withdrawn student")
    p.add_argument("--seed", type=int, required=True, help="NEW seed; record it with the old one")
    p.add_argument("--block-size", type=int, default=4)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--output", type=Path)
    a = p.parse_args()

    rows = list(csv.DictReader(a.codes.open(newline="", encoding="utf-8")))
    need = {"email", "participant_code"}
    if not rows or need - set(rows[0]):
        sys.exit(f"Codes file needs columns: {', '.join(sorted(need))}")

    excluded = {e.strip().lower() for e in a.exclude}
    found = {r["email"].strip().lower() for r in rows}
    if excluded - found:
        sys.exit(f"Not in codes file: {', '.join(sorted(excluded - found))}")

    keep = [r for r in rows if r["email"].strip().lower() not in excluded]
    plan = assign([r["email"].strip().lower() for r in keep], a.block_size, random.Random(a.seed))

    print(f"Seed {a.seed}: {len(keep)} re-randomized, {len(excluded)} excluded")
    print("  new split:", dict(Counter(c for c, _ in plan.values())))
    if a.dry_run:
        return

    from app.services.supabase import get_supabase_client
    client = get_supabase_client()

    from app.db.participants import hash_study_code

    def lookup(email, code):
        part = client.table("study_participant").select("id,is_test") \
            .eq("access_code_hash", hash_study_code(code.strip())).execute().data or []
        if len(part) != 1 or part[0]["is_test"]:
            sys.exit(f"STOPPED, nothing changed: code for {email} not found once as a real participant")
        subject = client.rpc("resolve_study_subject", {"p_participant_id": part[0]["id"]}).execute().data
        if isinstance(subject, list):
            subject = subject[0]
        if isinstance(subject, dict):
            subject = next(iter(subject.values()))
        sp = client.table("study_participation").select("id,status") \
            .eq("study_subject_id", subject).eq("round_number", 1).execute().data or []
        if len(sp) != 1:
            sys.exit(f"STOPPED, nothing changed: no single Round 1 row for {email}")
        return part[0]["id"], sp[0]["id"], sp[0]["status"]

    found_ids = {}
    for r in keep:
        email = r["email"].strip().lower()
        pid, spid, status = lookup(email, r["participant_code"])
        if status != "demographics":
            sys.exit(f"STOPPED, nothing changed: {email} has already started ({status})")
        found_ids[email] = (pid, spid)

    now = datetime.now(timezone.utc).isoformat()
    with a.output.open("x", newline="", encoding="utf-8") as h:
        w = csv.DictWriter(h, fieldnames=[
            "email", "participant_code", "condition", "block", "status_note",
            "study_participation_id", "old_condition", "seed", "rerandomized_at"])
        w.writeheader()
        for r in rows:
            email = r["email"].strip().lower()
            base = {"email": r["email"], "participant_code": r["participant_code"],
                    "study_participation_id": found_ids.get(email, ("", ""))[1],
                    "old_condition": r.get("condition", ""), "seed": a.seed,
                    "rerandomized_at": now}
            if email in excluded:
                w.writerow({**base, "condition": "", "block": "",
                            "status_note": "withdrew before start; excluded"})
                continue
            cond, block = plan[email]
            pid, spid = found_ids[email]
            client.table("study_participation").update(
                {"assigned_condition_code": cond}
            ).eq("id", spid).eq("status", "demographics").execute()
            client.table("study_participant").update({"condition": cond}).eq("id", pid).execute()
            w.writerow({**base, "condition": cond, "block": block, "status_note": ""})
            h.flush()

    print(f"Done. New file: {a.output}")


if __name__ == "__main__":
    main()
