from dotenv import load_dotenv
load_dotenv()

from datetime import datetime, timedelta, timezone

import pandas as pd
from langsmith import Client

client = Client()
PROJECT_NAME = "socratic-tutor-app"
since = datetime.now(timezone.utc) - timedelta(hours=3)

rows = []
for run in client.list_runs(project_name=PROJECT_NAME, run_type="llm", start_time=since):
    meta = (run.extra or {}).get("metadata", {})
    rows.append({
        "model": meta.get("model") or meta.get("ls_model_name"),
        "name": run.name,                      # e.g. evaluator, router, tutor voice
        "latency_s": (run.end_time - run.start_time).total_seconds()
                     if run.end_time and run.start_time else None,
        "prompt_tokens": run.prompt_tokens,
        "completion_tokens": run.completion_tokens,
        "prompt_cost": getattr(run, "prompt_cost", None),
        "completion_cost": getattr(run, "completion_cost", None),
        "total_cost": getattr(run, "total_cost", None),
        "error": run.error,
    })

df = pd.DataFrame(rows)
print(df.groupby(["model", "name"])["latency_s"].describe(percentiles=[0.5, 0.9]).round(2))
print(df.groupby(["model", "name"])["total_cost"].agg(["count", "mean", "sum"]).round(5))
df.to_csv("llm_call_latency.csv", index=False)