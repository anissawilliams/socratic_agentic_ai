from app.prompts.socratic import PHASE_CONTENT


def generate_reflection_exit(state: dict) -> dict:
    lines = PHASE_CONTENT["reflection_exit"]
    line = lines[min(state["attempt_count"], len(lines) - 1)]
    return {"messages": [{"role": "assistant", "content": line}]}