# SWPP 2026 Fall — Week 3 Agent Lab Code

Two parts, one shared key file: put `GOOGLE_API_KEY` and `TAVILY_API_KEY` in a single
`.env` at this repo's root (`agent-practice/.env`). Every script below loads it via
`load_dotenv()`, which searches upward from its own directory, so one file at the root
covers both `syllabus/` and `react/`.

```
agent-practice/
├── react/                  (1) Code update for slides 39–58
│   ├── simple_react.py     Everything given except build_app() — Exercise 1, slide 55
│   └── 10_plan_execute_nesting.png
│
└── syllabus/               (2) Syllabus Q&A Agent — the tool-design lab
    ├── CONCEPT.md          Tool design concept + lab design — start here
    ├── syllabus_data.py    Real syllabus (swpp_syllabus.pdf) + placeholder assignments/
    │                       due dates/TA email/team size where the PDF has none
    ├── tools_v1.py         Control group: deliberately bad design
    ├── tools_v2.py         Principles 1-2 given; 3-4 are TODO — Exercise 4, slide 80
    ├── agent_raw.py        ReAct loop with no framework (OpenAI SDK, pointed at Gemini's
    │                       OpenAI-compatible endpoint - 40 lines)
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
| `agent_raw.py` | the model | none — OpenAI SDK, via Gemini's OpenAI-compatible endpoint |

Note that `create_agent()` returns a `CompiledStateGraph`. LangChain 1.0 agents are built on
LangGraph, so `agent_langchain.py` uses LangGraph as well — it just does not write the nodes.

## Verification status

| Item | Result |
|---|---|
| `syllabus/test_tools.py` | **18 passed** (no API key needed) |
| `agent_raw.py` / `agent_langchain.py` / `agent_graph.py` | Verified live against `gemini-3.5-flash`: correct tool call + answer |
| `run_eval.py` | Verified live — v1 (one search tool) vs v2 (four typed tools): tool-call accuracy 17% → 75%, refusal accuracy 67% → 92% |
| `react/simple_react.py` | `build_app()` is Exercise 1 (slide 55); everything else verified live, including a full Plan-and-Execute run with a real final report |

## Running it

```bash
cp .env.example .env        # then put your keys in it (.env is gitignored)

cd syllabus
pip install -U openai langchain langgraph langchain-google-genai python-dotenv pytest

# 1) No API key — verify the tools first
pytest -q

# 2) With a key — run an agent (reads ../.env automatically)
python agent_raw.py       "What do we cover in week 6?"
python agent_langchain.py "What do we cover in week 6?"
python agent_graph.py     "What do we cover in week 6?"

# 3) Compare tool design v1 against v2
python run_eval.py                    # LangChain create_agent
python run_eval.py --runtime raw      # no framework
python run_eval.py --runtime graph    # explicit StateGraph
```

```bash
cd react
pip install -U langchain langgraph langchain-google-genai langchain-tavily python-dotenv
python simple_react.py    # reads ../.env automatically
```

## Verified environment

`langchain 1.3.17` · `langgraph 1.2.11` · `langchain-core 1.6.0` · `langchain-google-genai 4.4.0` ·
`langchain-tavily 0.2.18` · `openai 3.3.1` (raw SDK, pointed at Gemini's compat endpoint) · Python 3.13

Pin these in a `requirements.txt` before handing anything to students. `create_agent` is the
LangChain 1.0 replacement for `create_react_agent`, so a floating version breaks the lab on the day.
