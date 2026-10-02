"""Compare candidate evaluator models on real, already-recorded tutor turns.

Each recorded Socratic turn is rebuilt exactly as the evaluator saw it (scenario
context, conversation so far, current phase, the student's message) and sent
to every candidate model. Nothing is written to the database.

    python -m scripts.compare_evaluator_models \
      --models gpt-5.6-sol gpt-6-sol gpt-6.1-sol --limit 40

Outputs (in --out-dir, default ./evaluator_comparison):
  summary.txt        agreement with the recorded decisions, latency, tokens
  turns.csv          every turn x model: decisions, latency, tokens
  disagreements.csv  turns where the candidates disagree: read these yourself

If a model rejects temperature, add it to LLM_NO_TEMPERATURE_MODELS in .env.
"""

import argparse
import csv
import statistics
import time
from pathlib import Path

from langchain_core.messages import AIMessage, HumanMessage

from app.content.scenarios import load_scenario
from app.graph.evaluate.evaluator import evaluate_response
from app.services.llm import collect_llm_usage
from app.services.scenario_context import scenario_context_message
from app.services.supabase import get_supabase_client
from app.socratic.phases import SocraticPhase

FIELDS = ("session_goal_satisfied", "phase_goal_satisfied", "decision")


def recent_turns(client, limit: int) -> list[dict]:
    """Most recent completed Socratic turns that have a recorded evaluation."""
    evaluations = (
        client.table("response_evaluation")
        .select("tutor_turn_id,decision_code,phase_goal_satisfied,session_goal_satisfied,evaluator_model_name")
        .order("evaluated_at", desc=True)
        .limit(limit)
        .execute()
        .data
        or []
    )
    return evaluations


def rebuild_inputs(client, turn_id: str, cache: dict) -> dict | None:
    turn = (
        client.table("tutor_turn")
        .select("id,tutor_session_id,turn_number,student_message,phase_before_code")
        .eq("id", turn_id).limit(1).execute().data
    )
    if not turn or not turn[0]["phase_before_code"]:
        return None
    turn = turn[0]
    session_id = turn["tutor_session_id"]

    if session_id not in cache:
        session = (
            client.table("tutor_session")
            .select("scenario_key,study_participation_id")
            .eq("id", session_id).limit(1).execute().data[0]
        )
        participation = (
            client.table("study_participation")
            .select("pretest_instrument_key")
            .eq("id", session["study_participation_id"]).limit(1).execute().data[0]
        )
        history = (
            client.table("tutor_turn")
            .select("turn_number,student_message,tutor_response,status")
            .eq("tutor_session_id", session_id)
            .order("turn_number").execute().data or []
        )
        context, _ = scenario_context_message(participation["pretest_instrument_key"])
        cache[session_id] = {
            "scenario": load_scenario(session["scenario_key"]),
            "context": context,
            "history": [h for h in history if h["status"] == "completed"],
        }

    info = cache[session_id]
    messages = [info["context"], AIMessage(content=info["scenario"].opening_question)]
    for earlier in info["history"]:
        if earlier["turn_number"] >= turn["turn_number"]:
            break
        messages.append(HumanMessage(content=earlier["student_message"]))
        messages.append(AIMessage(content=earlier["tutor_response"] or ""))
    messages.append(HumanMessage(content=turn["student_message"]))

    return {
        "turn": turn,
        "messages": messages,
        "phase": SocraticPhase(turn["phase_before_code"]),
        "goal": info["scenario"].learning_objective,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--models", nargs="+", required=True)
    parser.add_argument("--limit", type=int, default=40, help="number of recent turns")
    parser.add_argument("--out-dir", type=Path, default=Path("evaluator_comparison"))
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    client = get_supabase_client()
    cache: dict = {}
    rows = []
    stats = {m: {"latency": [], "tokens": [], "agree": 0, "errors": 0} for m in args.models}

    recorded = recent_turns(client, args.limit)
    print(f"Replaying {len(recorded)} turns through {len(args.models)} models...")
    for index, rec in enumerate(recorded, start=1):
        inputs = rebuild_inputs(client, rec["tutor_turn_id"], cache)
        if inputs is None:
            continue
        row = {
            "turn_id": rec["tutor_turn_id"],
            "turn_number": inputs["turn"]["turn_number"],
            "phase": inputs["phase"].value,
            "student_message": inputs["turn"]["student_message"],
            "recorded_model": rec["evaluator_model_name"],
            "recorded_session_goal": rec["session_goal_satisfied"],
            "recorded_phase_goal": rec["phase_goal_satisfied"],
            "recorded_decision": rec["decision_code"],
        }
        for model in args.models:
            start = time.perf_counter()
            try:
                with collect_llm_usage() as usage:
                    result = evaluate_response(
                        messages=inputs["messages"],
                        current_phase=inputs["phase"],
                        last_student_message=inputs["turn"]["student_message"],
                        session_goal=inputs["goal"],
                        model=model,
                    )
                seconds = time.perf_counter() - start
                decision = getattr(result.decision, "value", result.decision)
                row[f"{model}:session_goal"] = result.session_goal_satisfied
                row[f"{model}:phase_goal"] = result.phase_goal_satisfied
                row[f"{model}:decision"] = decision
                row[f"{model}:seconds"] = round(seconds, 2)
                row[f"{model}:tokens"] = (usage.input_tokens or 0) + (usage.output_tokens or 0)
                row[f"{model}:reasoning"] = result.reasoning_summary
                stats[model]["latency"].append(seconds)
                stats[model]["tokens"].append(row[f"{model}:tokens"])
                if (result.session_goal_satisfied == rec["session_goal_satisfied"]
                        and result.phase_goal_satisfied == rec["phase_goal_satisfied"]):
                    stats[model]["agree"] += 1
            except Exception as exc:  # keep going; report per model
                row[f"{model}:error"] = f"{type(exc).__name__}: {exc}"[:300]
                stats[model]["errors"] += 1
        rows.append(row)
        print(f"  {index}/{len(recorded)}")

    if not rows:
        raise SystemExit("No recorded Socratic turns with evaluations were found.")

    columns = list(dict.fromkeys(key for row in rows for key in row))
    with (args.out_dir / "turns.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

    def verdicts(row, model):
        return (row.get(f"{model}:session_goal"), row.get(f"{model}:phase_goal"))

    disagreements = [
        row for row in rows
        if len({verdicts(row, m) for m in args.models if f"{m}:session_goal" in row}) > 1
    ]
    with (args.out_dir / "disagreements.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(disagreements)

    lines = [f"Turns compared: {len(rows)}   Turns where candidates disagree: {len(disagreements)}", ""]
    lines.append(f"{'model':<18}{'agree w/ recorded':>18}{'median s':>10}{'slowest s':>11}{'avg tokens':>12}{'errors':>8}")
    for model in args.models:
        s = stats[model]
        done = len(s["latency"])
        agree = f"{s['agree']}/{done}" if done else "-"
        med = f"{statistics.median(s['latency']):.1f}" if done else "-"
        slow = f"{max(s['latency']):.1f}" if done else "-"
        tok = f"{statistics.mean(s['tokens']):.0f}" if done else "-"
        lines.append(f"{model:<18}{agree:>18}{med:>10}{slow:>11}{tok:>12}{s['errors']:>8}")
    lines += ["", "Agreement = same session-goal and phase-goal verdicts as the recorded evaluator.",
              "Read disagreements.csv to judge which model is right; agreement alone isn't quality."]
    (args.out_dir / "summary.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
