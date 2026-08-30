from app.prompts.socratic import PHASE_CONTENT


def generate_elenchus(state: dict) -> dict:
    lines = PHASE_CONTENT["elenchus"]
    line = lines[min(state["attempt_count"], len(lines) - 1)]
    return {"messages": [{"role": "assistant", "content": line}]}