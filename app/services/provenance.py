"""Deterministic provenance for the model prompt and routing policy bundle."""

from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
from pathlib import Path

import yaml

from app.config import APPLICATION_REVISION


APP_ROOT = Path(__file__).resolve().parents[1]
PROMPT_MANIFEST = APP_ROOT.parent / "content" / "prompts" / "tutor_prompt_bundle.yaml"
_MANIFEST_PATH = Path("../content/prompts/tutor_prompt_bundle.yaml")
_SHARED_PATHS = (
    Path("socratic/definitions.py"),
    Path("socratic/context.py"),
)
_TUTOR_PROMPT_PATHS = (
    _MANIFEST_PATH,
    *_SHARED_PATHS,
    Path("socratic/prompts/base.py"),
    Path("socratic/prompts/elenchus.py"),
    Path("socratic/prompts/aporia.py"),
    Path("socratic/prompts/maieutics.py"),
    Path("socratic/prompts/dialectic.py"),
)
_EVALUATOR_PROMPT_PATHS = (
    _MANIFEST_PATH,
    *_SHARED_PATHS,
    Path("socratic/prompts/evaluator.py"),
    Path("graph/evaluate/evaluator.py"),
)
_ROUTER_PROMPT_PATHS = (
    _MANIFEST_PATH,
    *_SHARED_PATHS,
    Path("socratic/prompts/router.py"),
    Path("graph/next_move.py"),
)
_BUNDLE_PATHS = tuple(
    dict.fromkeys(
        _TUTOR_PROMPT_PATHS
        + _EVALUATOR_PROMPT_PATHS
        + _ROUTER_PROMPT_PATHS
    )
)


@dataclass(frozen=True)
class PromptBundleProvenance:
    key: str
    version: str
    sha256: str
    tutor_prompt_sha256: str
    evaluator_prompt_sha256: str
    router_prompt_sha256: str
    evaluator_prompt_version: str
    router_prompt_version: str
    application_revision: str


def _hash_paths(paths: tuple[Path, ...]) -> str:
    digest = sha256()
    for relative_path in paths:
        path = APP_ROOT / relative_path
        digest.update(str(relative_path).encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


@lru_cache(maxsize=1)
def prompt_bundle_provenance() -> PromptBundleProvenance:
    manifest = yaml.safe_load(PROMPT_MANIFEST.read_text(encoding="utf-8")) or {}
    key = str(manifest.get("key", "")).strip()
    version = str(manifest.get("version", "")).strip()
    components = manifest.get("components")
    required_components = {
        "shared_context",
        "base",
        "elenchus",
        "aporia",
        "maieutics",
        "dialectic",
        "evaluator",
        "router",
    }
    if not key or not version:
        raise ValueError("Tutor prompt bundle manifest requires key and version")
    if not isinstance(components, dict) or set(components) != required_components:
        raise ValueError("Tutor prompt bundle manifest has invalid components")
    if any(not str(value).strip() for value in components.values()):
        raise ValueError("Tutor prompt component versions cannot be blank")

    return PromptBundleProvenance(
        key=key,
        version=version,
        sha256=_hash_paths(_BUNDLE_PATHS),
        tutor_prompt_sha256=_hash_paths(_TUTOR_PROMPT_PATHS),
        evaluator_prompt_sha256=_hash_paths(_EVALUATOR_PROMPT_PATHS),
        router_prompt_sha256=_hash_paths(_ROUTER_PROMPT_PATHS),
        evaluator_prompt_version=str(components["evaluator"]).strip(),
        router_prompt_version=str(components["router"]).strip(),
        application_revision=APPLICATION_REVISION,
    )
