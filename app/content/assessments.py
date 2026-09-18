"""Load versioned pre/post-test instruments from YAML."""

from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
import json
from pathlib import Path
from typing import Literal

import yaml


ASSESSMENT_DIR = Path(__file__).resolve().parents[2] / "content" / "assessments"
AssessmentStage = Literal["pretest", "posttest"]


@dataclass(frozen=True)
class AssessmentQuestion:
    id: str
    construct: str
    prompt: str


@dataclass(frozen=True)
class AssessmentStageContent:
    stage: AssessmentStage
    scenario_key: str
    scenario_version: str
    scenario_sha256: str
    scenario_title: str
    scenario_text: str
    questions: tuple[AssessmentQuestion, ...]


@dataclass(frozen=True)
class AssessmentInstrument:
    key: str
    version: str
    status: str
    transfer_type: str
    cohort: str
    tutor_scenario_key: str
    pretest: AssessmentStageContent
    posttest: AssessmentStageContent
    sha256: str


def _required_text(data: dict, field: str, context: str) -> str:
    value = str(data.get(field, "")).strip()
    if not value:
        raise ValueError(f"{context} is missing required field {field!r}")
    return " ".join(value.split())


def _load_stage(data: dict, stage: AssessmentStage) -> AssessmentStageContent:
    context = f"{stage} content"
    questions_data = data.get("questions")
    if not isinstance(questions_data, list) or len(questions_data) != 4:
        raise ValueError(f"{context} must contain exactly four questions")

    questions = tuple(
        AssessmentQuestion(
            id=_required_text(question, "id", f"{context} question"),
            construct=_required_text(
                question,
                "construct",
                f"{context} question",
            ),
            prompt=_required_text(
                question,
                "prompt",
                f"{context} question",
            ),
        )
        for question in questions_data
    )
    ids = [question.id for question in questions]
    if len(set(ids)) != len(ids):
        raise ValueError(f"{context} question IDs must be unique")

    scenario_key = _required_text(data, "scenario_key", context)
    scenario_version = _required_text(data, "scenario_version", context)
    scenario_title = _required_text(data, "scenario_title", context)
    scenario_text = _required_text(data, "scenario_text", context)
    scenario_canonical = json.dumps(
        {
            "key": scenario_key,
            "version": scenario_version,
            "title": scenario_title,
            "text": scenario_text,
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")

    return AssessmentStageContent(
        stage=stage,
        scenario_key=scenario_key,
        scenario_version=scenario_version,
        scenario_sha256=sha256(scenario_canonical).hexdigest(),
        scenario_title=scenario_title,
        scenario_text=scenario_text,
        questions=questions,
    )


@lru_cache(maxsize=None)
def load_assessment_instrument(
    key: str,
    *,
    allow_draft: bool = False,
) -> AssessmentInstrument:
    path = ASSESSMENT_DIR / f"{key}.yaml"
    if not path.is_file():
        raise FileNotFoundError(f"No assessment instrument at {path}")

    raw = path.read_bytes()
    data = yaml.safe_load(raw) or {}
    if data.get("key") != key:
        raise ValueError(
            f"{path.name} declares key {data.get('key')!r} but was loaded as {key!r}"
        )

    status = _required_text(data, "status", path.name).lower()
    if status != "active" and not allow_draft:
        raise ValueError(f"Assessment instrument {key!r} is not active")

    pretest = _load_stage(data.get("pretest") or {}, "pretest")
    posttest = _load_stage(data.get("posttest") or {}, "posttest")
    if pretest.scenario_key == posttest.scenario_key:
        raise ValueError("Pre-test and post-test must use different scenarios")

    return AssessmentInstrument(
        key=key,
        version=_required_text(data, "version", path.name),
        status=status,
        transfer_type=_required_text(data, "transfer_type", path.name),
        cohort=_required_text(data, "cohort", path.name),
        tutor_scenario_key=_required_text(
            data,
            "tutor_scenario_key",
            path.name,
        ),
        pretest=pretest,
        posttest=posttest,
        sha256=sha256(raw).hexdigest(),
    )
