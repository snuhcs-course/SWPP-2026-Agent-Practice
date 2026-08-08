"""Unit tests for the tools - these run without an API key.

The point: a tool is just a function, so you can test it like any other function.
Get these green before you attach an LLM. Half of agent debugging ends right here.

    pip install pytest
    pytest -q
"""

import json

import pytest

import tools_v1
import tools_v2 as T


# ---------------------------------------------------------- happy path
def test_grading_sums_to_100():
    out = T.get_grading_policy()
    assert out["total"] == 100


def test_week_schedule_returns_the_right_week():
    out = T.get_week_schedule(5)
    assert out["week"] == 5
    assert "Agent" in out["topic"]


def test_policy_lookup():
    assert "10%" in T.get_course_policy("late_submission")
    assert "4" in T.get_course_policy("team_formation")


def test_search_finds_testing_week():
    hits = T.search_syllabus("Testing", section="schedule")
    assert isinstance(hits, list)
    assert any(h["week"] == 6 for h in hits)


# ------------------------------------------------- failure is a contract
# How a tool fails when the model gets it wrong is what drives accuracy.
@pytest.mark.parametrize("bad_week", [0, 16, 20, -1, "five", 3.5])
def test_out_of_range_week_returns_not_found(bad_week):
    out = T.get_week_schedule(bad_week)
    assert isinstance(out, str) and out.startswith("NOT_FOUND")
    # The failure message must tell the model what to do next
    assert "search_syllabus" in out or "between" in out


def test_unknown_policy_topic_lists_valid_options():
    out = T.get_course_policy("refund")           # type: ignore[arg-type]
    assert out.startswith("NOT_FOUND")
    for topic in T.POLICY_TOPICS:
        assert topic in out


def test_search_miss_is_explicit():
    out = T.search_syllabus("quantum computing", section="schedule")
    assert isinstance(out, str) and out.startswith("NOT_FOUND")
    assert "does not cover" in out


def test_empty_keyword_rejected():
    assert T.search_syllabus("   ").startswith("NOT_FOUND")


# ------------------------------------------------------- schema sanity
def test_schemas_match_registry():
    names_in_schema = {s["function"]["name"] for s in T.SCHEMAS}
    assert names_in_schema == set(T.REGISTRY)


def test_every_tool_has_a_description():
    for s in T.SCHEMAS:
        desc = s["function"]["description"]
        assert desc and len(desc) > 30, s["function"]["name"]


def test_enum_arguments_are_actually_enums():
    """A free-form string invites the model to get it wrong. Assert it is an enum."""
    by_name = {s["function"]["name"]: s for s in T.SCHEMAS}
    props = by_name["get_course_policy"]["function"]["parameters"]["properties"]
    assert "enum" in props["topic"]


def test_schemas_are_json_serializable():
    json.dumps(T.SCHEMAS)


# ----------------------------------------------- v1 is deliberately bad
def test_v1_cannot_signal_a_miss():
    """v1 returns the whole document even for a miss, so the model thinks it found it."""
    out = tools_v1.search_syllabus("quantum computing")
    assert "NOT_FOUND" not in out
    assert len(out) > 1000        # a full dump: wasted context, and a source of hallucination
