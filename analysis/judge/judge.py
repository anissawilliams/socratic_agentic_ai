"""LLM judge for the pre- and posttest answers.

Scores each answer 0-3 on its construct with the rubric in rubric.yaml. The
judge sees only the scenario, the question, the rubric and the answer: never
the condition, class, student, round or whether it is a pre- or posttest.
Answers are scored in random order. Runs are traced to LangSmith when
LANGSMITH_TRACING=true.

Develop on pretests only. Freeze the rubric and model, then score posttests.

    python -m analysis.judge.judge --stage pretest --model <model> --limit 40
    python -m analysis.judge.judge --stage pretest --model <model> --repeats 3
    python -m analysis.judge.judge --stage posttest --model <model> --repeats 3   # after freezing
    python -m analysis.judge.judge --stage pretest --human-sheet 60               # blind sheet for raters

Output (resumable; rows already scored are skipped):
    analysis/data/judge_scores.csv
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from analysis.study_data import load_study  # noqa: E402

RUBRIC_PATH = HERE / "rubric.yaml"
DEFAULT_DATA = ROOT / "analysis" / "data"
DEFAULT_CONTENT = ROOT / "content"
SEED = 20261108  # fixes the scoring order and the human sample

SYSTEM = """You are scoring short written answers from a university study on reasoning about decisions.
Score one answer at a time on a 0-3 scale using the rubric for its question.

Rules:
{rules}

Return JSON only. Quote the words from the answer that your score is based on (or "" if there are none)."""

USER = """SCENARIO
{scenario}

QUESTION
{question}

RUBRIC FOR THIS QUESTION
{levels}

{context}WHAT A STRONG ANSWER TENDS TO NOTICE IN THIS SCENARIO (guidance, not a checklist)
{notes}

STUDENT ANSWER
\"\"\"{answer}\"\"\"
"""

SCHEMA = {
    "name": "answer_score",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "evidence_quote": {"type": "string"},
            "rationale": {"type": "string"},
            "score": {"type": "integer", "enum": [0, 1, 2, 3]},
        },
        "required": ["evidence_quote", "rationale", "score"],
    },
}

FIELDS = ["answer_id", "run", "score", "evidence_quote", "rationale", "model",
          "rubric_version", "rubric_sha256", "prompt_sha256", "scored_at"]


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_rubric(path: Path = RUBRIC_PATH) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    return yaml.safe_load(text), sha(text)


def scenario_texts(content_dir: Path) -> dict[str, str]:
    texts = {}
    for path in sorted((content_dir / "assessments").glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for stage in ("pretest", "posttest"):
            part = data.get(stage) or {}
            if part.get("scenario_key"):
                texts[part["scenario_key"]] = part.get("scenario_text", "")
    return texts


def build_items(data_dir: Path, content_dir: Path, stage: str, rubric: dict) -> pd.DataFrame:
    """One row per answer to score, with only what the judge may see."""
    study = load_study(data_dir)
    answers = study.answers
    answers = answers[(answers["stage"] == stage) & answers["construct_code"].isin(rubric["constructs"])]
    scenario_key = study.attempts.set_index("id")["scenario_key"]
    texts = scenario_texts(content_dir)
    # The student's own recommendation, shown (not scored) when judging the other
    # three answers: a counterargument or an uncertainty is judged against it.
    recs = answers[answers["construct_code"] == "recommendation"].set_index("assessment_attempt_id")["response_text"]
    own_rec = answers["assessment_attempt_id"].map(recs).where(answers["construct_code"] != "recommendation", "")
    items = pd.DataFrame({
        "answer_id": answers["id"].values,
        "own_recommendation": own_rec.fillna("").astype(str).values,
        "construct": answers["construct_code"].values,
        "scenario_key": answers["assessment_attempt_id"].map(scenario_key).values,
        "answer": answers["response_text"].fillna("").astype(str).values,
    })
    missing = sorted(set(items["scenario_key"]) - set(texts))
    if missing:
        raise SystemExit(f"No scenario text in {content_dir}/assessments for: {missing}")
    items["scenario"] = items["scenario_key"].map(texts)
    return items.sample(frac=1, random_state=SEED).reset_index(drop=True)


def messages(item: dict, rubric: dict) -> list[dict]:
    construct = rubric["constructs"][item["construct"]]
    notes = rubric.get("scenario_notes", {}).get(item["scenario_key"]) or []
    return [
        {"role": "system", "content": SYSTEM.format(rules="\n".join(f"- {r}" for r in rubric["general_rules"]))},
        {"role": "user", "content": USER.format(
            scenario=item["scenario"].strip(),
            question=construct["question"],
            levels="\n".join(f"{k}: {v}" for k, v in construct["levels"].items()),
            notes="\n".join(f"- {n}" for n in notes) or "(none written yet)",
            context=(f"THE STUDENT'S OWN RECOMMENDATION (context only; do not score it)\n\"\"\"{item['own_recommendation'].strip()}\"\"\"\n\n"
                     if item.get("own_recommendation", "").strip() else ""),
            answer=item["answer"].strip(),
        )},
    ]


def make_client():
    import os
    from openai import OpenAI
    try:  # read the project's .env (repo root), as the backend does
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env")
    except ImportError:
        pass
    key = os.getenv("OPENAI_API_KEY") or os.getenv("OPEN_AI_KEY")
    if not key:
        raise SystemExit("No OpenAI key found: set OPENAI_API_KEY or OPEN_AI_KEY in .env")
    client = OpenAI(api_key=key)
    try:  # LangSmith tracing, when LANGSMITH_TRACING / LANGSMITH_API_KEY are set
        from langsmith.wrappers import wrap_openai
        client = wrap_openai(client)
    except ImportError:
        pass
    return client


def score_one(client, model: str, msgs: list[dict], temperature: float | None) -> dict:
    kwargs = {"model": model, "messages": msgs,
              "response_format": {"type": "json_schema", "json_schema": SCHEMA}}
    if temperature is not None:
        kwargs["temperature"] = temperature
    reply = client.chat.completions.create(**kwargs)
    return json.loads(reply.choices[0].message.content)


def run(args) -> None:
    rubric, rubric_sha = load_rubric()
    items = build_items(args.data, args.content, args.stage, rubric)
    if args.limit:
        items = items.head(args.limit)
    prompt_sha = sha(SYSTEM + USER + json.dumps(SCHEMA, sort_keys=True))

    out = args.data / "judge_scores.csv"
    done = set()
    if out.exists():
        prev = pd.read_csv(out, dtype=str)
        same = prev[(prev["model"] == args.model) & (prev["rubric_sha256"] == rubric_sha)
                    & (prev["prompt_sha256"] == prompt_sha)]
        done = set(zip(same["answer_id"], same["run"].astype(int)))

    todo = [(it, r) for r in range(1, args.repeats + 1) for it in items.to_dict("records")
            if (it["answer_id"], r) not in done]
    print(f"{args.stage}: {len(items)} answers x {args.repeats} runs; {len(todo)} to score "
          f"(rubric {rubric['version']} {rubric['status']}, model {args.model})")
    if rubric.get("status") != "frozen" and args.stage == "posttest" and not args.allow_draft:
        raise SystemExit("Rubric is not frozen. Posttests are scored only with a frozen rubric.")

    client = args.client or make_client()
    new_file = not out.exists()
    with out.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        if new_file:
            writer.writeheader()
        for n, (item, r) in enumerate(todo, start=1):
            if not item["answer"].strip():
                result = {"score": 0, "evidence_quote": "", "rationale": "blank answer"}
            else:
                result = score_one(client, args.model, messages(item, rubric), args.temperature)
            writer.writerow({
                "answer_id": item["answer_id"], "run": r, **result, "model": args.model,
                "rubric_version": rubric["version"], "rubric_sha256": rubric_sha,
                "prompt_sha256": prompt_sha, "scored_at": datetime.now(timezone.utc).isoformat(),
            })
            handle.flush()
            if n % 25 == 0 or n == len(todo):
                print(f"  {n}/{len(todo)}")
    print(f"Scores: {out}")


def human_sheet(args) -> None:
    """Blind sheet for human raters: same text the judge sees, no condition or stage."""
    rubric, _ = load_rubric()
    items = build_items(args.data, args.content, args.stage, rubric)
    per = max(1, args.human_sheet // len(rubric["constructs"]))
    sample = pd.concat([g.sample(min(len(g), per), random_state=SEED)
                        for _, g in items.groupby("construct")])
    sample = sample.sample(frac=1, random_state=SEED)
    sheet = sample[["answer_id", "scenario_key", "construct", "answer"]].copy()
    sheet["question"] = sheet["construct"].map(lambda c: rubric["constructs"][c]["question"])
    sheet["rater_initials"] = ""
    sheet["score_0_3"] = ""
    sheet["note"] = ""
    out = args.data / f"human_sheet_{args.stage}.csv"
    sheet[["answer_id", "scenario_key", "question", "answer", "rater_initials", "score_0_3", "note"]].to_csv(out, index=False)
    print(f"{len(sheet)} answers -> {out}  (each rater fills in a copy; scenario texts are in content/assessments)")


def main(argv=None, client=None) -> None:
    p = argparse.ArgumentParser(description="Score test answers with the LLM judge.")
    p.add_argument("--stage", choices=["pretest", "posttest"], required=True)
    p.add_argument("--model", help="judge model, e.g. a model different from the tutor's")
    p.add_argument("--repeats", type=int, default=1, help="independent runs per answer (3 for final scoring)")
    p.add_argument("--temperature", type=float, default=0.0,
                   help="use -1 for models that reject a temperature setting")
    p.add_argument("--limit", type=int, help="score only the first N answers (for trying things out)")
    p.add_argument("--data", type=Path, default=DEFAULT_DATA)
    p.add_argument("--content", type=Path, default=DEFAULT_CONTENT)
    p.add_argument("--human-sheet", type=int, metavar="N", help="write a blind sheet of N answers for human raters")
    p.add_argument("--allow-draft", action="store_true", help=argparse.SUPPRESS)
    args = p.parse_args(argv)
    args.client = client
    if args.temperature is not None and args.temperature < 0:
        args.temperature = None
    if args.human_sheet:
        return human_sheet(args)
    if not args.model:
        p.error("--model is required for scoring")
    run(args)


if __name__ == "__main__":
    main()