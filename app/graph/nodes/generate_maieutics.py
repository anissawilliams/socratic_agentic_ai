from app.prompts.socratic import PHASE_CONTENT


def generate_maieutics(state: dict) -> dict:
    lines = PHASE_CONTENT["maieutics"]
    line = lines[min(state["attempt_count"], len(lines) - 1)]
    return {"messages": [{"role": "assistant", "content": line}]}