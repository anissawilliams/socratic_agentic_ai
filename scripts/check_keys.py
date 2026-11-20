"""Check that every service key works, in about ten seconds.

Uses the same environment variables as the backend and writes nothing:
- OpenAI: one tiny request with each model the app uses
- Supabase: counts rows in study_subject (read only)
- LangSmith: lists one project
- SMTP: logs in, sends nothing

Against production settings (Railway's variables):
    railway run python -m scripts.check_keys
Against your local .env:
    python -m scripts.check_keys
"""

import os
import smtplib
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

results = []


def check(name):
    def wrap(fn):
        try:
            detail = fn()
            results.append((name, True, detail or ""))
        except Exception as exc:  # report every failure, keep going
            results.append((name, False, f"{type(exc).__name__}: {str(exc)[:160]}"))
        return fn
    return wrap


def models():
    main = os.getenv("LLM_MODEL", "")
    names = [main, os.getenv("LLM_MODEL_EVALUATOR") or main, os.getenv("LLM_MODEL_ROUTER") or main]
    return [m for i, m in enumerate(names) if m and m not in names[:i]]


for model in models():
    @check(f"OpenAI ({model})")
    def _(model=model):
        from openai import OpenAI
        reply = OpenAI(api_key=os.environ["OPENAI_API_KEY"]).chat.completions.create(
            model=model, messages=[{"role": "user", "content": "Reply with the word ok."}])
        return f"replied: {reply.choices[0].message.content.strip()[:20]!r}"


@check("Supabase")
def _():
    from supabase import create_client
    client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SECRET_KEY"])
    rows = client.table("study_subject").select("id", count="exact").limit(1).execute()
    return f"study_subject readable ({rows.count} rows)"


@check("LangSmith")
def _():
    if not (os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGCHAIN_API_KEY")):
        raise RuntimeError("no LANGSMITH_API_KEY set")
    from langsmith import Client
    project = next(iter(Client().list_projects(limit=1)), None)
    tracing = os.getenv("LANGSMITH_TRACING") or os.getenv("LANGCHAIN_TRACING_V2") or "unset"
    return f"key accepted (tracing={tracing}; e.g. project {getattr(project, 'name', '-')!r})"


@check("SMTP")
def _():
    host = os.getenv("SMTP_HOST")
    if not host:
        raise RuntimeError("no SMTP_HOST set")
    port = int(os.getenv("SMTP_PORT", "587"))
    with smtplib.SMTP(host, port, timeout=15) as server:
        server.starttls()
        server.login(os.environ["SMTP_USERNAME"], os.environ["SMTP_PASSWORD"])
    return f"login ok ({host})"


width = max(len(n) for n, _, _ in results)
for name, ok, detail in results:
    print(f"{'PASS' if ok else 'FAIL'}  {name:{width}}  {detail}")
sys.exit(0 if all(ok for _, ok, _ in results) else 1)