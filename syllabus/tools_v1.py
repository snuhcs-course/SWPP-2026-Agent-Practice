"""Tool design v1 - the "natural" first attempt.

Deliberately bad. This is the control group we compare v2 against.
In the slides it is the exhibit for "what breaks if you write it this way".
"""

import json

from syllabus_data import COURSE, GRADING, POLICIES, SCHEDULE

_ALL_TEXT = json.dumps(
    {"course": COURSE, "schedule": SCHEDULE, "grading": GRADING, "policies": POLICIES},
    ensure_ascii=False,
)


def search_syllabus(query: str) -> str:
    """Search the syllabus."""
    # Flaw 1: one free-form string argument - the model cannot tell what to put in it.
    # Flaw 2: a miss still returns something, so the model believes it found an answer.
    # Flaw 3: the whole document comes back, burning context and burying the one line
    #         that mattered.
    # Flaw 4: it answers off-topic questions too ("tomorrow's weather"), which removes
    #         any ground for refusing.
    if query and query.lower() in _ALL_TEXT.lower():
        return _ALL_TEXT
    return _ALL_TEXT


TOOLS = [search_syllabus]

REGISTRY = {"search_syllabus": search_syllabus}

SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "search_syllabus",
            "description": "Search the syllabus.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    }
]

SYSTEM_PROMPT = "You are a helpful assistant for the SWPP course. Answer the student's question."
