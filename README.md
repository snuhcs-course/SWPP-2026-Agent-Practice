# SWPP 2026 Fall — Week 5 Agent Lab Code

Two parts.

```
agent-practice/
├── react/                  (1) Code update for slides 39–58
│   ├── SLIDE_PATCH.md      Slide-by-slide before/after — start here
│   ├── simple_react.py     Full working code on the LangChain 1.x API
│   └── 10_plan_execute_nesting.png
│
└── syllabus/               (2) Syllabus Q&A Agent — the tool-design lab
    ├── CONCEPT.md          Tool design concept + lab design — start here
    ├── syllabus_data.py    Mock syllabus (swap in the real one)
    ├── tools_v1.py         Control group: deliberately bad design
    ├── tools_v2.py         The four design principles applied
    ├── agent_raw.py        ReAct loop with no framework (OpenAI SDK only, 40 lines)
    ├── agent_langchain.py  The same tools via create_agent (10 lines)
    ├── agent_graph.py      The same tools as an explicit LangGraph StateGraph (slide 69)
    ├── eval_set.json       12-question eval set
    ├── run_eval.py         v1 vs v2, scored on answer / trajectory / refusal
    └── test_tools.py       18 unit tests that run without an API key
```

## Three runtimes, one set of tools

The three agent files differ only in **who decides the path**; `tools_v2.py` is identical for all
three. That contrast is the Workflow ↔ Agent spectrum from slides 21–26, made runnable.

| File | Routing decided by | Framework |
|---|---|---|
| `agent_graph.py` | the developer, in conditional edges | LangGraph, hand-written |
| `agent_langchain.py` | the model | LangChain `create_agent` (LangGraph underneath) |
| `agent_raw.py` | the model | none — OpenAI SDK only |

Note that `create_agent()` returns a `CompiledStateGraph`. LangChain 1.0 agents are built on
LangGraph, so `agent_langchain.py` uses LangGraph as well — it just does not write the nodes.

## Verification status

| Item | Result |
|---|---|
| `react/simple_react.py` | Imports and compiles. No `DeprecationWarning` |
| Graph topology | `planner → execute → replan ⇢ {execute, final_report} → END` — matches the slide diagram |
| `syllabus/test_tools.py` | **18 passed** (no API key needed) |
| `agent_raw.py` loop | Stub-tested: survives bad arguments and unknown tools, stops at `MAX_STEPS` |
| `agent_langchain.py` | Builds; `Literal` → `enum` schema conversion confirmed |
| `agent_graph.py` | Compiles (5 nodes, 2 conditional edges); both branches stub-tested end to end |

Anything that calls a live LLM (`run_eval.py`) was **not** run here — no API key in this
environment. Add a key and run the commands below.

## Running it

```bash
cd syllabus
pip install -U openai langchain langgraph langchain-openai pytest

# 1) No API key — verify the tools first
pytest -q

# 2) With a key — run an agent
export OPENAI_API_KEY=...
python agent_raw.py       "What do we cover in week 5?"
python agent_langchain.py "What do we cover in week 5?"
python agent_graph.py     "What do we cover in week 5?"

# 3) Compare tool design v1 against v2
python run_eval.py                    # LangChain create_agent
python run_eval.py --runtime raw      # no framework
python run_eval.py --runtime graph    # explicit StateGraph
```

```bash
cd react
pip install -U langchain langgraph langchain-openai langchain-tavily python-dotenv
# put OPENAI_API_KEY and TAVILY_API_KEY in .env
python simple_react.py
```

## Verified environment

`langchain 1.3.14` · `langgraph 1.2.10` · `langchain-core 1.5.3` · `langchain-openai 1.4.2` ·
`langchain-tavily 0.2.18` · Python 3.13

Pin these in a `requirements.txt` before handing anything to students. `create_agent` is the
LangChain 1.0 replacement for `create_react_agent`, so a floating version breaks the lab on the day.
