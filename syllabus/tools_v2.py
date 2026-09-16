"""Tool design v2 - the same job, designed.

Four tools, each demonstrating exactly one design principle.

  get_grading_policy   Principle 1. A tool with zero arguments cannot be called wrong.
  get_course_policy    Principle 2. Use an enum instead of a free-form string.
  get_week_schedule    Principle 3. Validate arguments, and write the failure message
                                    as a prompt - the model is the one who reads it.
                                    TODO - Exercise 4.
  search_syllabus      Principle 4. Keep exactly one fallback, and return "nothing found"
                                    explicitly.
                                    TODO - Exercise 4.

The fifth principle is not in the code:

  Principle 5. Do not build a tool for refusing out-of-scope questions.
               With no weather tool, the model has no choice but to refuse.
               Choosing NOT to build a tool is also design.
"""

from typing import Literal

from syllabus_data import COURSE, GRADING, POLICIES, POLICY_TOPICS, SCHEDULE

PolicyTopic = Literal[
    "late_submission",
    "attendance",
    "academic_integrity",
    "team_formation",
    "office_hours",
]

MIN_WEEK, MAX_WEEK = SCHEDULE[0]["week"], SCHEDULE[-1]["week"]


def get_grading_policy() -> dict:
    """Return the grading breakdown of the SWPP course as {component: percentage}.

    Use this for any question about grades, weights, how the final score is
    computed, or how much an exam or the project is worth.
    Takes no arguments.
    """
    return {"grading": GRADING, "total": sum(GRADING.values())}


def get_course_policy(topic: PolicyTopic) -> str:
    """Return the official course policy text for one topic.

    Use this for questions about rules and procedures, not about dates.
      late_submission    - deadlines, penalties, extensions
      attendance         - absences, how attendance affects the grade
      academic_integrity - cheating, collaboration, AI tool usage
      team_formation     - team size, registration deadline, changing teams
      office_hours       - when and where to meet the instructor or TA
    """
    if topic not in POLICIES:
        # The failure message is read by the model, not by a human.
        # Tell it what is valid and what to do next.
        return (
            f"NOT_FOUND: '{topic}' is not a valid policy topic. "
            f"Valid topics are: {', '.join(POLICY_TOPICS)}."
        )
    return POLICIES[topic]


def get_week_schedule(week: int) -> dict | str:
    """Return the topic, assignment and due date for one week of the course.

    Use this when the question mentions a specific week number, or asks what is
    covered or due in a given week. `week` must be an integer from 1 to 15.
    For questions that are not tied to a week number, use search_syllabus instead.
    """
    # TODO (Exercise 4, principle 3): validate `week` BEFORE searching, and return
    # a NOT_FOUND message that says what was wrong, what is valid, and what to do
    # next (e.g. "call search_syllabus instead"). Without this, an out-of-range or
    # wrong-type `week` silently falls through to the generic message below, which
    # tells the model neither the valid range nor what to try next.
    for row in SCHEDULE:
        if row["week"] == week:
            return row
    return f"NOT_FOUND: no schedule entry for week {week}."


def search_syllabus(
    keyword: str,
    section: Literal["schedule", "policy", "course_info"] = "schedule",
) -> list[dict] | str:
    """Keyword-search one section of the syllabus. Use ONLY when the other tools do not fit.

    Returns at most 5 matches. Returns an explicit NOT_FOUND string when nothing
    matches - in that case the syllabus genuinely does not cover the topic, so say
    so instead of guessing.
    """
    if not keyword or not keyword.strip():
        return "NOT_FOUND: keyword must be a non-empty string."

    kw = keyword.strip().lower()
    hits: list[dict] = []

    if section == "schedule":
        for row in SCHEDULE:
            haystack = f"{row['topic']} {row['assignment'] or ''}".lower()
            if kw in haystack:
                hits.append(row)
    elif section == "policy":
        for topic, text in POLICIES.items():
            if kw in topic.lower() or kw in text.lower():
                hits.append({"topic": topic, "text": text})
    elif section == "course_info":
        for key, value in COURSE.items():
            if kw in key.lower() or kw in str(value).lower():
                hits.append({key: value})

    # TODO (Exercise 4, principle 4): an empty `hits` needs an explicit NOT_FOUND
    # string - [] does not read as "no results" to a model, which then risks
    # answering as if it found something.
    return hits[:5]


TOOLS = [get_grading_policy, get_course_policy, get_week_schedule, search_syllabus]

REGISTRY = {fn.__name__: fn for fn in TOOLS}

# JSON schemas in the same shape as slide 63 ("Tool Definition").
# LangChain derives these automatically from the type hints and docstrings above;
# agent_raw.py, which runs without a framework, uses them directly.
SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_grading_policy",
            "description": get_grading_policy.__doc__.split("\n\n")[0],
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_course_policy",
            "description": get_course_policy.__doc__,
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "enum": list(POLICY_TOPICS)}
                },
                "required": ["topic"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_week_schedule",
            "description": get_week_schedule.__doc__,
            "parameters": {
                "type": "object",
                "properties": {
                    "week": {"type": "integer", "minimum": MIN_WEEK, "maximum": MAX_WEEK}
                },
                "required": ["week"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_syllabus",
            "description": search_syllabus.__doc__,
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {"type": "string"},
                    "section": {
                        "type": "string",
                        "enum": ["schedule", "policy", "course_info"],
                    },
                },
                "required": ["keyword"],
            },
        },
    },
]

SYSTEM_PROMPT = """You are the Q&A assistant for the SWPP course (Software Development \
Principles and Practices, 2026 Fall).

Rules:
1. Answer ONLY from the syllabus tools. Never answer course questions from memory.
2. If a tool returns a string starting with NOT_FOUND, the syllabus does not cover it.
   Say so plainly. Do not guess and do not fill the gap with general knowledge.
3. If the question is not about this course at all (weather, other courses, general
   coding help), refuse in one sentence and say what you can help with instead.
4. Cite what you used: end your answer with a short "(source: <tool name>)".
Answer in the language the student used."""
