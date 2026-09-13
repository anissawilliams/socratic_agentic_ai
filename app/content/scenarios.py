"""Load participant-facing scenario content from YAML.

Content lives outside the code so wording can be reviewed and versioned without
touching tutor logic, and so a single file is the answer to "what did this
participant actually see".
"""

from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
from pathlib import Path

import yaml

SCENARIO_DIR = Path(__file__).resolve().parents[2] / "content" / "scenarios"
DEFAULT_SCENARIO_KEY = "citation_quality"

_REQUIRED_FIELDS = (
    "key",
    "version",
    "title",
    "opening_question",
    "learning_objective",
)


@dataclass(frozen=True)
class Scenario:
    key: str
    version: str
    title: str
    opening_question: str
    learning_objective: str

    # Fingerprint of the file as loaded. Version is declared by hand and can be
    # forgotten; this cannot, so a wording change that skipped a version bump is
    # still detectable once sessions record it.
    sha256: str


@lru_cache(maxsize=None)
def load_scenario(key: str = DEFAULT_SCENARIO_KEY) -> Scenario:
    """Read one scenario, failing loudly rather than serving partial content."""
    path = SCENARIO_DIR / f"{key}.yaml"

    if not path.is_file():
        raise FileNotFoundError(f"No scenario content at {path}")

    raw = path.read_bytes()
    data = yaml.safe_load(raw) or {}

    missing = [
        field
        for field in _REQUIRED_FIELDS
        if not str(data.get(field, "")).strip()
    ]
    if missing:
        raise ValueError(
            f"{path.name} is missing required content: {', '.join(missing)}"
        )

    if data["key"] != key:
        raise ValueError(
            f"{path.name} declares key {data['key']!r} but was loaded as {key!r}"
        )

    return Scenario(
        key=data["key"],
        # Quoted so that a version like 1.0 does not arrive as a float.
        version=str(data["version"]),
        title=str(data["title"]).strip(),
        # Folded YAML preserves the line breaks of the source file; the learner
        # should see one paragraph.
        opening_question=" ".join(str(data["opening_question"]).split()),
        learning_objective=" ".join(str(data["learning_objective"]).split()),
        sha256=sha256(raw).hexdigest(),
    )
