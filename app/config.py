import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
# Per-role models. The tutor voices and the control assistant always use
# LLM_MODEL (so both conditions share one model). The evaluator and router
# are behind-the-scenes judges and may use a different model.
LLM_MODEL_EVALUATOR = os.getenv("LLM_MODEL_EVALUATOR") or LLM_MODEL
LLM_MODEL_ROUTER = os.getenv("LLM_MODEL_ROUTER") or LLM_MODEL
# Optional reasoning effort per role, for reasoning models only
# ("minimal", "low", "medium", "high"). Empty = provider default.
# The evaluator and router are classification-style judges and are the
# biggest share of turn latency; "low" is usually enough for them.
LLM_REASONING_EFFORT = os.getenv("LLM_REASONING_EFFORT") or None
LLM_REASONING_EFFORT_EVALUATOR = os.getenv("LLM_REASONING_EFFORT_EVALUATOR") or None
LLM_REASONING_EFFORT_ROUTER = os.getenv("LLM_REASONING_EFFORT_ROUTER") or None
# Comma-separated models that reject a temperature setting (some reasoning
# models). Leave empty unless a model errors on temperature.
LLM_NO_TEMPERATURE_MODELS = {
    name.strip()
    for name in os.getenv("LLM_NO_TEMPERATURE_MODELS", "").split(",")
    if name.strip()
}
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
APPLICATION_REVISION = (
    os.getenv("RAILWAY_GIT_COMMIT_SHA")
    or os.getenv("GIT_COMMIT_SHA")
    or "development"
)
# Per-phase minimum and maximum times, in seconds. Change with environment
# variables (local .env / Railway); no code change needed.
# Demographics and the survey are untimed.

PHASE_MIN_SECONDS = {
    "pretest": int(os.getenv("PRETEST_MIN_SECONDS", "420")),     # 7 min
    "tutor": int(os.getenv("TUTOR_MIN_SECONDS", "840")),         # 14 min
    "posttest": int(os.getenv("POSTTEST_MIN_SECONDS", "420")),   # 7 min
}

PHASE_TIME_LIMITS_SECONDS = {
    "pretest": int(os.getenv("PRETEST_SECONDS", "540")),         # 9 min
    "tutor": int(os.getenv("TUTOR_SECONDS", "1080")),            # 18 min
    "posttest": int(os.getenv("POSTTEST_SECONDS", "540")),       # 9 min
}

