"""End-to-end smoke test of the participant study flow against a running backend.

For each fresh test participant it walks:
    pretest -> tutor (until complete) -> posttest -> complete
and asserts the study status after every step, the same way the frontend sees it.
Participants run concurrently to exercise multi-user behavior.

Uses your normal .env (Supabase for provisioning; the backend uses its own keys).

    # backend must be running, e.g. scripts/run_dev.sh
    python -m scripts.smoke_test_study_flow --users 3
    python -m scripts.smoke_test_study_flow --users 3 --base-url https://your-railway-backend
"""

import argparse
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import requests

from scripts.provision_test_participants import create_participant


# Plausible student replies, cycled until the tutor ends the session.
STUDENT_REPLIES = [
    "No, I think there should be more to consider than just citations.",
    "The methods and whether the data is available.",
    "Citations show a paper is popular. People might cite it because it backs up what they want to be true.",
    "idk",
    "I didn't say citations are useless, just that they're not enough on their own.",
    "Yeah.",
    "Maybe the students who do that are just more motivated to begin with.",
    "I'd look at the methods, check if the results hold up, and see if the citing paper uses it honestly.",
    "Newer studies aren't automatically better, but they might use better data.",
    "I'd check whether the people citing it actually tested its claims or just repeated them.",
]

WORD_LIMIT = 60
HARD_WORDS = re.compile(r"\b(establish\w*|central claim|account for|substantiat\w*)\b", re.I)


class Fail(Exception):
    pass


class Client:
    def __init__(self, base_url: str, code: str):
        self.base = base_url.rstrip("/")
        self.headers = {"X-Participant-Code": code}

    def call(self, method: str, path: str, **kwargs):
        response = requests.request(
            method, f"{self.base}{path}", headers=self.headers, timeout=120, **kwargs
        )
        if response.status_code >= 400:
            raise Fail(f"{method} {path} -> {response.status_code}: {response.text[:300]}")
        return response.json()

    def status(self) -> str:
        return self.call("GET", "/auth/me")["study_status"]


def expect_status(client: Client, expected: str, step: str, retries: int = 5) -> None:
    # Mirrors the frontend's short retry after the final tutor turn.
    for attempt in range(retries):
        actual = client.status()
        if actual == expected:
            return
        time.sleep(1)
    raise Fail(f"after {step}: expected status {expected!r}, got {actual!r}")


def do_assessment(client: Client, stage: str) -> None:
    content = client.call("POST", "/assessment/start")
    if content["stage"] != stage:
        raise Fail(f"assessment/start returned stage {content['stage']!r}, expected {stage!r}")
    client.call(
        "POST",
        "/assessment/submit",
        json={
            "instrument_key": content["instrument_key"],
            "instrument_version": content["instrument_version"],
            "attempt_id": content["attempt_id"],
            "content_sha256": content["content_sha256"],
            "stage": content["stage"],
            "scenario_key": content["scenario_key"],
            "answers": [
                {"question_id": q["id"], "value": f"Smoke-test answer for {q['id']}."}
                for q in content["questions"]
            ],
        },
    )


def check_voice(text: str) -> list[str]:
    issues = []
    words = len(text.split())
    if words > WORD_LIMIT:
        issues.append(f"{words} words")
    if text.count("?") > 1:
        issues.append(f"{text.count('?')} questions")
    hard = HARD_WORDS.findall(text)
    if hard:
        issues.append("wording: " + ", ".join(sorted(set(h.lower() for h in hard))))
    return issues


def run_participant(index: int, args) -> dict:
    result = {"index": index, "ok": False, "log": [], "turns": [], "code": None}
    log = result["log"].append

    try:
        created = create_participant(
            round_number=1,
            condition=args.condition,
            cohort_code="smoke",
            pretest_instrument_key="test_near_transfer",
            pretest_scenario_key="test_citation_pre",
            tutor_scenario_key="citation_quality",
            posttest_instrument_key="test_near_transfer",
            posttest_scenario_key="test_citation_post",
            index=index,
        )
        result["code"] = created["participant_code"]
        client = Client(args.base_url, created["participant_code"])

        expect_status(client, "pretest", "provisioning")
        log("PASS provisioned, status=pretest")

        do_assessment(client, "pretest")
        expect_status(client, "tutor", "pretest submit")
        log("PASS pretest submitted, status=tutor")

        start = client.call("GET", "/tutor/start")
        session_id = start["session_id"]
        complete = start["is_complete"]
        turns = 0
        while not complete:
            if turns >= args.max_turns:
                raise Fail(f"tutor did not complete within {args.max_turns} turns")
            reply = STUDENT_REPLIES[turns % len(STUDENT_REPLIES)]
            data = client.call(
                "POST", "/tutor/message", json={"session_id": session_id, "message": reply}
            )
            turns += 1
            complete = data["is_complete"]
            result["turns"].append(
                {
                    "n": turns,
                    "phase": data["current_phase"],
                    "student": reply,
                    "tutor": data["message"],
                    "issues": [] if complete else check_voice(data["message"]),
                }
            )
        log(f"PASS tutor completed in {turns} turns")

        # The frontend relies on this transition happening with the final turn.
        expect_status(client, "posttest", "tutor completion")
        log("PASS status=posttest right after completion")

        do_assessment(client, "posttest")
        expect_status(client, "complete", "posttest submit")
        log("PASS posttest submitted, status=complete")

        result["ok"] = True
    except Fail as exc:
        log(f"FAIL {exc}")
    except Exception as exc:  # provisioning/network errors
        log(f"ERROR {type(exc).__name__}: {exc}")

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--users", type=int, default=3)
    parser.add_argument("--base-url", default=os.getenv("SMOKE_BASE_URL", "http://localhost:8000"))
    parser.add_argument("--condition", default="scenario_questioning")
    parser.add_argument("--max-turns", type=int, default=25)
    parser.add_argument("--show-transcripts", action="store_true")
    args = parser.parse_args()

    print(f"Running {args.users} participant(s) against {args.base_url}\n")
    with ThreadPoolExecutor(max_workers=args.users) as pool:
        results = list(pool.map(lambda i: run_participant(i, args), range(1, args.users + 1)))

    flagged_total = turns_total = 0
    for r in results:
        print(f"Participant {r['index']} ({r['code'] or 'not created'}): {'OK' if r['ok'] else 'FAILED'}")
        for line in r["log"]:
            print(f"  {line}")
        for t in r["turns"]:
            turns_total += 1
            if t["issues"]:
                flagged_total += 1
            if args.show_transcripts or t["issues"]:
                flag = f"  [! {'; '.join(t['issues'])}]" if t["issues"] else ""
                print(f"    turn {t['n']} ({t['phase']}){flag}")
                if args.show_transcripts:
                    print(f"      student: {t['student']}")
                print(f"      tutor:   {t['tutor']}")
        print()

    passed = sum(r["ok"] for r in results)
    print(f"Flow: {passed}/{len(results)} participants passed")
    print(f"Voice: {flagged_total}/{turns_total} tutor turns flagged "
          f"(>{WORD_LIMIT} words, multiple questions, or hard wording)")
    sys.exit(0 if passed == len(results) else 1)


if __name__ == "__main__":
    main()