from app.prompts.socratic import PHASE_CONTENT


def generate_aporia(state: dict) -> dict:
    lines = PHASE_CONTENT["aporia"]
    line = lines[min(state["attempt_count"], len(lines) - 1)]
    return {"messages": [{"role": "assistant", "content": line}]}