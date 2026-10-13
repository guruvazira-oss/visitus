import math

import pytest

from voice_eval.rubric_loader import available_rubrics, load_rubric
from voice_eval.schemas import DIMENSIONS, GATE_IDS


def test_three_versions_exist():
    assert set(available_rubrics()) >= {"v1", "v2", "v3"}


@pytest.mark.parametrize("v", ["v1", "v2", "v3"])
def test_weights_sum_to_one(v):
    r = load_rubric(v)
    assert math.isclose(sum(r.weights.values()), 1.0)
    assert [d.id for d in r.dimensions] == list(DIMENSIONS)
    assert sorted(g.gate_id for g in r.critical_gates) == sorted(GATE_IDS)


@pytest.mark.parametrize("v", ["v1", "v2", "v3"])
def test_every_anchor_defined(v):
    for d in load_rubric(v).dimensions:
        assert sorted(d.anchors) == [0, 1, 2, 3, 4]


def test_versions_immutable_distinct_hashes():
    hashes = {v: load_rubric(v).content_hash for v in ("v1", "v2", "v3")}
    assert len(set(hashes.values())) == 3


def test_changelog_grows():
    assert len(load_rubric("v1").changelog) == 0
    assert len(load_rubric("v2").changelog) >= 1
    assert len(load_rubric("v3").changelog) > len(load_rubric("v2").changelog)


def test_v2_and_v3_parent_links():
    assert load_rubric("v2").parent_version == "v1"
    assert load_rubric("v3").parent_version == "v2"
