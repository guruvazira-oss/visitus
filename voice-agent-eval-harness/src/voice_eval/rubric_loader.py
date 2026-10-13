"""Load and validate immutable, versioned rubric files."""

from __future__ import annotations

import hashlib
import math
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from voice_eval.config import RUBRIC_DIR
from voice_eval.schemas import DIMENSIONS, GATE_IDS


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Anchor(_Model):
    label: str
    observable_behavior: str
    evidence_required: str


class Applicability(_Model):
    always_applicable: bool
    not_applicable_conditions: list[str] = Field(default_factory=list)
    never_not_applicable_when: list[str] = Field(default_factory=list)


class Dimension(_Model):
    id: str
    name: str
    weight: float = Field(gt=0, le=1)
    description: str
    observable_behaviors: list[str]
    evidence_requirements: list[str]
    applicability: Applicability
    anchors: dict[int, Anchor]
    positive_examples: list[str]
    negative_examples: list[str]
    scenario_rules: dict[str, str]
    common_judge_mistakes: list[str]

    @model_validator(mode="after")
    def _anchors(self) -> Dimension:
        if sorted(self.anchors) != [0, 1, 2, 3, 4]:
            raise ValueError(f"{self.id}: anchors must define scores 0,1,2,3,4")
        if self.applicability.always_applicable and self.applicability.not_applicable_conditions:
            raise ValueError(f"{self.id}: always-applicable dimension cannot list N/A conditions")
        return self


class Gate(_Model):
    gate_id: str
    name: str
    severity: str
    applicable_conditions: list[str]
    violation_definition: str
    not_a_violation: list[str] = Field(default_factory=list)
    evidence_requirements: list[str]
    override_behavior: str


class ChangeRecord(_Model):
    change_id: str
    area: str
    previous_definition: str
    updated_definition: str
    motivation: str
    relevant_examples: list[str]
    expected_improvement: str
    measured_effect: str
    potential_regressions: str


class Rubric(_Model):
    rubric_version: str
    status: str
    parent_version: str | None = None
    created: str
    title: str
    description: str
    policy_reference: str
    scale: dict[int, str]
    dimensions: list[Dimension]
    critical_gates: list[Gate]
    heuristic_rules: dict[str, Any] = Field(default_factory=dict)
    changelog: list[ChangeRecord] = Field(default_factory=list)
    content_hash: str = ""

    @model_validator(mode="after")
    def _structure(self) -> Rubric:
        ids = [d.id for d in self.dimensions]
        if ids != list(DIMENSIONS):
            raise ValueError(f"dimensions must be exactly {DIMENSIONS} in order, got {ids}")
        total = sum(d.weight for d in self.dimensions)
        if not math.isclose(total, 1.0, abs_tol=1e-9):
            raise ValueError(f"dimension weights must sum to 1.0, got {total}")
        gate_ids = [g.gate_id for g in self.critical_gates]
        if sorted(gate_ids) != sorted(GATE_IDS):
            raise ValueError(f"rubric must define gates {GATE_IDS}, got {gate_ids}")
        if sorted(self.scale) != [0, 1, 2, 3, 4]:
            raise ValueError("scale must define 0-4")
        return self

    @property
    def weights(self) -> dict[str, float]:
        return {d.id: d.weight for d in self.dimensions}

    def dimension(self, dim_id: str) -> Dimension:
        return next(d for d in self.dimensions if d.id == dim_id)

    def gate(self, gate_id: str) -> Gate:
        return next(g for g in self.critical_gates if g.gate_id == gate_id)


def rubric_path(version: str) -> Path:
    return RUBRIC_DIR / f"rubric_{version}.yaml"


def available_rubrics() -> list[str]:
    return sorted(p.stem.removeprefix("rubric_") for p in RUBRIC_DIR.glob("rubric_v*.yaml"))


def load_rubric_file(path: Path) -> Rubric:
    raw = path.read_bytes()
    data = yaml.safe_load(raw)
    rubric = Rubric.model_validate(data)
    rubric.content_hash = hashlib.sha256(raw).hexdigest()[:16]
    return rubric


@lru_cache(maxsize=8)
def load_rubric(version: str) -> Rubric:
    path = rubric_path(version)
    if not path.exists():
        raise FileNotFoundError(f"rubric {version!r} not found; available: {available_rubrics()}")
    rubric = load_rubric_file(path)
    if rubric.rubric_version != version:
        raise ValueError(f"{path.name} declares version {rubric.rubric_version!r}")
    return rubric
