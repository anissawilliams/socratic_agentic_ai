"""Confirm every route that spends model budget requires an enrolled participant.

Guards against a new /tutor route being added without the auth dependency, which
would reopen the endpoint to anyone who knows the backend URL.

Run: .venv/bin/python -m scripts.check_auth_guard
"""

import sys
from unittest.mock import patch
from uuid import uuid4

from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from app.api.auth.dependencies import require_participant
from app.api.tutor import _sessions
from app.main import app

REQUIRED_DEPENDENCY = "require_participant"
PUBLIC_PATHS = {"/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc"}


def iter_api_routes(router) -> list[APIRoute]:
    """Walk nested routers.

    FastAPI 0.141 wraps an included router in a _IncludedRouter that exposes the
    real one as `original_router` instead of flattening its routes onto the app.
    """
    found = []
    for route in getattr(router, "routes", []):
        if isinstance(route, APIRoute):
            found.append(route)
            continue

        nested = getattr(route, "original_router", None) or route
        if nested is not route:
            found.extend(iter_api_routes(nested))
    return found


routes = iter_api_routes(app)
failures = []

if not routes:
    failures.append("Found no API routes to inspect; this check is not working")

print("Declared dependencies:")
for route in sorted(routes, key=lambda r: r.path):
    names = [dep.call.__name__ for dep in route.dependant.dependencies]
    guarded = REQUIRED_DEPENDENCY in names
    print(f"  {'/'.join(sorted(route.methods)):8} {route.path:16} {names}")

    if not guarded and route.path not in PUBLIC_PATHS:
        failures.append(f"{route.path} does not require {REQUIRED_DEPENDENCY}")

client = TestClient(app)

cases = [
    ("GET", "/tutor/start", None),
    ("POST", "/tutor/message", {"session_id": str(uuid4()), "message": "hi"}),
    ("GET", "/auth/me", None),
]

with patch(
    "app.api.auth.dependencies.get_participant_by_study_code",
    return_value=None,
):
    for label, headers in [
        ("No credentials", {}),
        ("Bad code", {"X-Participant-Code": "not-a-real-code"}),
    ]:
        print(f"\n{label}:")
        for method, path, body in cases:
            response = client.request(method, path, json=body, headers=headers)
            rejected = response.status_code in (401, 403)
            print(f"  {method:4} {path:16} -> {response.status_code}")

            if not rejected:
                failures.append(
                    f"{label}: {method} {path} returned {response.status_code}"
                )

# A valid code for one participant must not reach another participant's
# session. Overriding the dependency avoids needing a real study code;
# neither request below invokes the graph, so no model call is made.
print("\nCross-participant access:")

session_id = str(uuid4())
_sessions[session_id] = {"participant_id": "participant-a"}

app.dependency_overrides[require_participant] = lambda: {"id": "participant-b"}
intruded = client.post(
    "/tutor/message",
    json={"session_id": session_id, "message": "let me in"},
)
print(f"  B posts to A's session -> {intruded.status_code}")

if intruded.status_code != 404:
    failures.append(
        f"B reached A's session: expected 404, got {intruded.status_code}"
    )

_sessions.pop(session_id, None)

app.dependency_overrides.clear()

if failures:
    print("\nFAILED:")
    for failure in failures:
        print(f"  {failure}")
    sys.exit(1)

print("\nAll routes require an enrolled participant.")
