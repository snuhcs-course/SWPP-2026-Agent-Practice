# How to Design a Tool

> SWPP 2026 Fall · Week 5 · Syllabus Q&A Agent — lab design note

## 0. In one sentence

**Designing a tool is API design. The only difference is that the caller is non-deterministic.**

With an ordinary API, the caller is code a human wrote: it reads the docs and calls correctly.
With a tool, the caller is an LLM. It reads the docs (that is, the `description`) and calls
**probabilistically**. So one design goal is added — **make the mistakes the model could make
impossible in the first place.**

This note states that as five principles, and points at where each one shows up in the code.

---

## 1. Why "just one search tool" does not work

This is almost always the first tool a student writes. (`tools_v1.py`)

```python
def search_syllabus(query: str) -> str:
    """Search the syllabus."""
    return WHOLE_SYLLABUS_JSON
```

Four things break at once.

| Problem | Consequence |
|---|---|
| One free-form string argument | The model cannot tell what to put in it. `"week 5"`? `"5"`? `"agents"`? |
| A miss still returns something | The model **believes it found the answer** and builds on top of it |
| The whole document comes back | Burns context, and buries the one line that mattered |
| Off-topic questions are served too | "Tomorrow's weather" gets the syllabus, so there is no ground for refusing |

**Most hallucination is not the model lying. It is a tool failing ambiguously.**
That is the one sentence students should take away from this lab.

---

## 2. Five design principles

### Principle 1 — A tool with zero arguments is the safest tool

```python
def get_grading_policy() -> dict:
    """Return the grading breakdown as {component: percentage}. Takes no arguments."""
```

If there is no argument to fill, there is no way to fill it wrong.
Ask first: **"does the model really have to decide this argument?"**
Grade weights, the room number, the TA's email — anything with exactly one answer takes no argument.

### Principle 2 — An enum instead of a free-form string

```python
PolicyTopic = Literal["late_submission", "attendance",
                      "academic_integrity", "team_formation", "office_hours"]

def get_course_policy(topic: PolicyTopic) -> str: ...
```

With `topic: str` the model invents `"late"`, `"handing in late"`, `"deadline stuff"` — and the
match fails. With `Literal`, **the set of values it can get wrong is finite**; it becomes an
`enum` in the schema and the model cannot pick outside it.

> LangChain converts a `Literal` hint into `{"enum": [...]}` automatically.
> Check it with `convert_to_openai_tool(get_course_policy)`.

### Principle 3 — The failure message is read by the model, not by a human

```python
return (f"NOT_FOUND: week must be an integer between 1 and 15, got {week!r}. "
        f"If the student did not mention a week number, call search_syllabus instead.")
```

`raise ValueError("invalid week")` either kills the loop or dumps a stack trace into the context.
A good failure message carries three things: **what was wrong · what is valid · what to do next.**
This is not error handling. It is prompt writing.

### Principle 4 — Always return "nothing found" explicitly

```python
if not hits:
    return (f"NOT_FOUND: no entry in section '{section}' matches '{keyword}'. "
            f"The syllabus does not cover this. Tell the student it is not in the syllabus.")
```

An empty list `[]` or an empty string `""` frequently does not read as "no results" to a model.
Start the string with a **loud token** like `NOT_FOUND:` and pin down what that token means in
the system prompt.

### Principle 5 — Choosing not to build a tool is also design

The diagram has a `refuse` node, but **refusal is not implemented as a tool.**
Give the model a `refuse_out_of_scope()` and it will over-use it.
Instead, **do not build a weather tool.** With no tool, the model has no choice but to refuse.

> The tool list *is* the agent's permission scope. This is where the lab meets the week-5
> security material (the lethal trifecta).

---

## 3. The four tools in this lab

| Tool | Argument | Principle it shows |
|---|---|---|
| `get_grading_policy()` | none | 1 — zero arguments |
| `get_course_policy(topic)` | `Literal`, 5 values | 2 — enum |
| `get_week_schedule(week)` | `int` 1–15, validated | 3 — the failure message is a prompt |
| `search_syllabus(keyword, section)` | fallback | 4 — explicit NOT_FOUND |
| *(no weather or general-coding tool)* | — | 5 — not building is design |

**Three specific tools plus one fallback** is a good default skeleton.
Specific tools are accurate and cheap; the fallback covers the rest. Fallback only gives you v1;
specific tools only leaves questions you cannot answer.

### How finely should you split tools?

One rule.

> **If the model has to guess in order to fill an argument, the tool is too big.**
> **If one question needs more than three tool calls, the tools are too small.**

---

## 4. Lab structure — the judgement the student makes

The point of this lab is not to type code along. It is to **change the design and measure the result.**

```
                 tools_v1.py                    tools_v2.py
                 (one search tool)              (3 specific + 1 fallback)
                      │                              │
     ┌────────────────┼──────────────────┬───────────┴────────────┐
agent_graph.py   agent_langchain.py   agent_raw.py          (one eval set)
explicit graph   create_agent         no framework           eval_set.json
developer routes model routes         model routes           12 questions
```

**Not one character of the prompt changes. Only the tool design does.** Then compare the scores.

```bash
python run_eval.py                    # LangChain create_agent
python run_eval.py --runtime raw      # no framework, plain while loop
python run_eval.py --runtime graph    # explicit LangGraph StateGraph (slide 69)
```

The eval set has 12 questions in three kinds.

- **7 normal** — you only get them right by picking the correct tool
- **3 ambiguous** — no week number given; a topic the syllabus does not cover; an out-of-range argument
- **2 out-of-scope** — refusing is the correct answer

Scored on three axes.

| Axis | What it measures |
|---|---|
| `answer` | Does the final answer contain the supporting fact (final-answer eval) |
| `tool` | **Was the expected tool called** (trajectory eval) |
| `refuse` | Was a question that should be refused, refused (safety eval) |

The `tool` axis is the point of the lab. It **separates a lucky answer from a sourced one**, and it
is the concrete form of slide 73: "agent evaluation cannot look only at the final answer; it has to
look at the trajectory."

---

## 5. Three runtimes, one set of tools

The three agent files differ only in **who decides the path**. The tools are byte-for-byte identical.

| | `agent_graph.py` | `agent_langchain.py` | `agent_raw.py` |
|---|---|---|---|
| Routing decided by | the developer, in conditional edges | the model | the model |
| Framework | LangGraph, hand-written | LangChain `create_agent` | none (OpenAI SDK) |
| Lines of orchestration | ~60 | ~10 | ~40 |
| Can an out-of-scope question reach a tool? | **No — structurally impossible** | Yes, in principle | Yes, in principle |
| Do you know which node ran? | Always | Only from the trace | Only from the trace |
| Adding a new tool | edit nodes and edges | add a function | add a function + schema |

Note that `create_agent()` returns a `CompiledStateGraph` — **LangChain 1.0 agents are built on
LangGraph.** So `agent_langchain.py` uses LangGraph too; it just does not write the nodes by hand.
The difference between the columns is not "framework or not". It is **who fixes the path.**

**That is exactly the Workflow ↔ Agent spectrum from slides 21–26.**
Running all three on the same eval set turns that spectrum from a diagram into numbers on the
student's own score table. This is the best possible closing for the session.

---

## 6. Files

| File | Contents |
|---|---|
| `syllabus_data.py` | Mock syllabus. Swap in the real one and nothing else changes |
| `tools_v1.py` | Control group. Deliberately bad design |
| `tools_v2.py` | The four principles applied + hand-written JSON schemas |
| `agent_raw.py` | ReAct loop with no framework (OpenAI SDK only, 40 lines) |
| `agent_langchain.py` | The same tools via `create_agent` (10 lines) |
| `agent_graph.py` | The same tools as an explicit `StateGraph` (slide 69) |
| `eval_set.json` | 12-question eval set |
| `run_eval.py` | v1 vs v2, scored on answer / trajectory / refusal |
| `test_tools.py` | 18 unit tests that **run without an API key** |

---

## 7. Suggested order in class

1. **Run `pytest -q` first** (2 min, no API key)
   → "A tool is just a function. Get these green before you attach an LLM."
   Students feel that half of agent debugging ends right here.
2. **Read `agent_raw.py`** (5 min)
   → See that what a framework does is these 40 lines.
3. **Run the eval on v1** (5 min) → the score is low. Why?
4. **Finish `tools_v2.py`** (15 min) — students fill in principles 3 and 4 themselves (marked `TODO`)
5. **Run the eval again on v2** (5 min) → compare. **Point out that the prompt never changed.**
6. **Swap the runtime** (5 min) → `--runtime graph` vs `--runtime langchain`.
   Same tools, different routing authority. Where do the scores differ, and why?

**Deliverables**: `tools_v2.py`, `eval_result.json`, and a three-sentence `REPORT.md` on
*which questions v1 got wrong and why*.
