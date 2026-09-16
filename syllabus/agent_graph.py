"""The same tools, wired as an explicit LangGraph StateGraph.

This is the version drawn on slide 69: classify -> route -> lookup / refuse -> answer.
The developer fixes the path in code; the model only fills in the classification and
the wording. Compare against agent_langchain.py, where the model picks the path itself.

Why bother, when create_agent() already returns a CompiledStateGraph?
Because here you can *see* and *constrain* the path:
  - an out-of-scope question can never reach a tool, by construction
  - you always know which node ran, without reading a trace
  - the retry loop is a real edge with a real counter, not a hope

Run:
    pip install -U langchain langgraph langchain-google-genai
    export GOOGLE_API_KEY=...
    python agent_graph.py "What do we cover in week 5?"
"""

import sys
from typing import Literal, Optional

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

import tools_v2 as T

load_dotenv()   # reads ../.env - a real env var still overrides it. Must run
                 # before the module-level ChatGoogleGenerativeAI(...) calls below.

MODEL = "gemini-3.5-flash"
MAX_RETRIES = 2


# ------------------------------------------------------------ State
class State(TypedDict):
    question: str
    category: Optional[str]
    evidence: Optional[str]
    tools_used: list[str]
    retries: int
    answer: Optional[str]
    # hints parsed by classify(), consumed by lookup()
    hint_week: Optional[int]
    hint_keyword: Optional[str]


# -------------------------------------------------------- Classifier
class QuestionType(BaseModel):
    """Route a student question to the branch that can answer it."""

    category: Literal["schedule", "policy", "grading", "course_info", "out_of_scope"] = (
        Field(
            description=(
                "schedule=about a week, topic, assignment or due date; "
                "policy=about rules such as late submission, attendance, teams, integrity; "
                "grading=about score weights; "
                "course_info=about the instructor, room, time or TA contact; "
                "out_of_scope=not about this course at all"
            )
        )
    )
    week: Optional[int] = Field(
        default=None, description="The week number, only if the student named one."
    )
    keyword: str = Field(description="One or two words to search the syllabus with.")


classifier = ChatPromptTemplate.from_messages(
    [
        ("system", "You route questions for the SWPP course Q&A bot. Classify only; never answer."),
        ("user", "{question}"),
    ]
) | ChatGoogleGenerativeAI(model=MODEL).with_structured_output(QuestionType)


# ------------------------------------------------------------ Nodes
def classify(state: State) -> dict:
    r = classifier.invoke({"question": state["question"]})
    return {
        "category": r.category,
        "evidence": None,
        "tools_used": state.get("tools_used", []),
        "retries": state.get("retries", 0),
        # stash the parsed hints on the state so lookup can use them
        "hint_week": r.week,
        "hint_keyword": r.keyword,
    }


def lookup(state: State) -> dict:
    """Call the tool the classification points at. No LLM involved here."""
    category = state["category"]
    week = state.get("hint_week")
    keyword = state.get("hint_keyword") or state["question"]
    used = list(state.get("tools_used", []))

    if category == "grading":
        evidence, name = T.get_grading_policy(), "get_grading_policy"
    elif category == "schedule" and isinstance(week, int):
        evidence, name = T.get_week_schedule(week), "get_week_schedule"
    elif category == "policy":
        topic = next((t for t in T.POLICY_TOPICS if t.split("_")[0] in keyword.lower()), None)
        if topic:
            evidence, name = T.get_course_policy(topic), "get_course_policy"
        else:
            evidence, name = T.search_syllabus(keyword, section="policy"), "search_syllabus"
    else:
        section = "course_info" if category == "course_info" else "schedule"
        evidence, name = T.search_syllabus(keyword, section=section), "search_syllabus"

    used.append(name)
    return {"evidence": str(evidence), "tools_used": used}


def refuse(state: State) -> dict:
    return {
        "answer": "That is outside the scope of this course assistant. "
                  "I can answer questions about the SWPP schedule, grading and course policies.",
        "tools_used": state.get("tools_used", []),
    }


answerer = ChatPromptTemplate.from_messages(
    [
        ("system",
         "Answer the student using ONLY the evidence below. If the evidence starts with "
         "NOT_FOUND, say the syllabus does not cover it. End with '(source: syllabus)'.\n\n"
         "Evidence:\n{evidence}"),
        ("user", "{question}"),
    ]
) | ChatGoogleGenerativeAI(model=MODEL)


def answer(state: State) -> dict:
    msg = answerer.invoke({"question": state["question"], "evidence": state["evidence"]})
    # .text, not .content: Gemini's AIMessage.content is a list of content
    # blocks, not a plain string. .text is the cross-provider str-subclass
    # accessor LangChain 1.x added for exactly this difference.
    return {"answer": msg.text}


# --------------------------------------------------- Conditional edges
def route(state: State) -> Literal["lookup", "refuse"]:
    """The whole point of the graph version: out_of_scope can never reach a tool."""
    return "refuse" if state["category"] == "out_of_scope" else "lookup"


def check_evidence(state: State) -> Literal["answer", "retry"]:
    """Retry once with a broader search if the tool found nothing."""
    thin = (state.get("evidence") or "").startswith("NOT_FOUND")
    if thin and state.get("retries", 0) < MAX_RETRIES:
        return "retry"
    return "answer"


def widen(state: State) -> dict:
    """The retry node: search the whole syllabus instead of one section."""
    used = list(state.get("tools_used", []))
    evidence = T.search_syllabus(state["question"].split()[0], section="policy")
    used.append("search_syllabus")
    return {
        "evidence": str(evidence),
        "tools_used": used,
        "retries": state.get("retries", 0) + 1,
    }


# ------------------------------------------------------------ Graph
def build():
    g = StateGraph(State)
    g.add_node("classify", classify)
    g.add_node("lookup", lookup)
    g.add_node("widen", widen)
    g.add_node("refuse", refuse)
    g.add_node("answer", answer)

    g.add_edge(START, "classify")
    g.add_conditional_edges("classify", route, {"lookup": "lookup", "refuse": "refuse"})
    g.add_conditional_edges("lookup", check_evidence, {"answer": "answer", "retry": "widen"})
    g.add_edge("widen", "answer")
    g.add_edge("answer", END)
    g.add_edge("refuse", END)
    return g.compile()


app = build()


def run(question: str, tools=T, verbose: bool = True) -> dict:
    """Same signature as agent_raw.run / agent_langchain.run, so run_eval.py can use it."""
    out = app.invoke({"question": question, "tools_used": [], "retries": 0})
    traj = out.get("tools_used", [])
    if verbose:
        print(f"  category = {out.get('category')}")
        for name in traj:
            print(f"  -> {name}")
    return {"answer": out.get("answer") or "", "trajectory": traj, "steps": len(traj)}


if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "How much is the final exam worth?"
    print(f"Q: {q}")
    r = run(q)
    print(f"\nA: {r['answer']}")
    print(f"\ntrajectory: {r['trajectory']}")
