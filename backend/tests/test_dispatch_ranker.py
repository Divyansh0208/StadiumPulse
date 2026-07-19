"""Unit tests for the deterministic dispatch scoring — pure function, no DB/network."""
import pytest
from types import SimpleNamespace

from backend.orchestrator.app.dispatch_ranker import score_volunteer, REQUIRED_SKILL_BY_CATEGORY


def make_volunteer(zone_id, skills):
    return SimpleNamespace(zone_id=zone_id, skills=skills, name="test", id=1)


def test_same_zone_matching_skill_scores_highest():
    v = make_volunteer("Z1", ["medical"])
    score = score_volunteer(v, target_zone="Z1", needed_skill="medical")
    assert score == 10.0  # 0 hops (proximity=10) + matching skill (10), avg = 10


def test_far_zone_no_skill_scores_low():
    v = make_volunteer("Z3", ["general"])
    score = score_volunteer(v, target_zone="Z1", needed_skill="medical")
    assert score < 5.0


def test_proximity_beats_distance_with_same_skill():
    close = make_volunteer("Z5", ["crowd_control"])  # 1 hop from any gate
    far = make_volunteer("Z3", ["crowd_control"])
    close_score = score_volunteer(close, target_zone="Z1", needed_skill="crowd_control")
    far_score = score_volunteer(far, target_zone="Z1", needed_skill="crowd_control")
    assert close_score > far_score


@pytest.mark.parametrize(
    "category,expected_skill",
    [
        ("medical", "medical"),
        ("security", "crowd_control"),
        ("crowd_crush", "crowd_control"),
        ("facility", "general"),
        ("unknown_category", "general"),  # falls back to default
    ],
)
def test_category_skill_mapping(category, expected_skill):
    assert REQUIRED_SKILL_BY_CATEGORY.get(category, "general") == expected_skill
