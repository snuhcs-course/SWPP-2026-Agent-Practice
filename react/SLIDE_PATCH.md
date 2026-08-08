# Code update for slides 39–58 (LangChain 1.x / LangGraph 1.x)

Verified against `langchain 1.3.14`, `langgraph 1.2.10`, `langchain-core 1.5.3`,
`langchain-openai 1.4.2`, `langchain-tavily 0.2.18`.
The full working file is `simple_react.py`. Graph compilation and topology were checked
for real, and no `DeprecationWarning` is raised.

---

## Summary — 8 places to change

| Slide | Now | Change to | Why |
|---|---|---|---|
| **30** | `pip install langgraph` | `pip install -U langchain langgraph langchain-openai langchain-tavily` | `create_agent` lives in the `langchain` package |
| **41** | `from langgraph.prebuilt import create_react_agent` | `from langchain.agents import create_agent` | **Deprecated**; replaced in LangChain 1.0 |
| **41** | `prompt=ChatPromptTemplate(...)` | `system_prompt="..."` (a plain string) | New API. The `("user","{messages}")` placeholder pattern goes away with it |
| **42** | `result['messages'][1].content` | `result['messages'][-1].content` | Index 1 is not the final answer once a tool call is in the list |
| **44** | `steps: Annotated[List[str], "description"]` | `steps: list[str] = Field(description="...")` | In a Pydantic model, the description must go through `Field` to reach the schema |
| **55·57** | `MemorySaver` | `InMemorySaver` | Renamed (`MemorySaver` remains as an alias, so it still runs) |
| **58** | `from langchain_teddynote.messages import invoke_graph, random_uuid` | `app.stream(...)` + `uuid.uuid4()` | A third-party community package with no install instructions; the standard API is enough |
| **39–58 titles** | "ReAct Agent" | "Plan-and-Execute Agent" | See below |

---

## A naming problem — this is not ReAct, it is Plan-and-Execute

What slides 39–58 build is a `planner → execute → replan → final_report` graph, i.e.
**Plan-and-Execute**. ReAct is the **sub-agent** running inside the `execute` node.
A student who just learned ReAct on slides 21–23 gets stuck on "how is this different from that?"

Recommendation: retitle 39–58 as `Plan-and-Execute Agent (1/n)` and add a **nesting diagram**
on slide 38 (`10_plan_execute_nesting.png`, included here).
Not a line of code changes — only one sentence is added: *outer is Plan-Execute, inner is ReAct.*

---

## Replacement code, slide by slide

### Slide 30 — LangGraph Installation

```
pip install -U langchain langgraph langchain-openai langchain-tavily python-dotenv
```

> `create_agent` is in `langchain`, not `langgraph`. You need both.

---

### Slide 41 — Agent and Tool (1/2)

**Title**: `Plan-and-Execute - Sub-agent and Tool (1/2)`
**Caption**: ~~`create_react_agent() first`~~ → `create_agent() first`

```python
from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch

# Define LLM
llm = ChatOpenAI(model='gpt-5-nano')

# Initialize Tavily search tool
tools = [TavilySearch(max_results=3)]

# Create the ReAct sub-agent
agent_executor = create_agent(
    model=llm,
    tools=tools,
    system_prompt="You are a helpful research assistant. Answer in English.",
    middleware=[ModelCallLimitMiddleware(thread_limit=8, exit_behavior="end")],
)
```

Three changes, all of them **worth calling out in class**:

1. `ChatPromptTemplate` is gone. The system prompt is just a string.
   (The old `("user", "{messages}")` placeholder was always opaque anyway.)
2. `middleware=` is new. `ModelCallLimitMiddleware` is **the cap that stops runaway tool calls**.
   → If you told students "an agent can loop forever", this is where the remedy appears in code.
3. Other middleware plugs into the same slot: `HumanInTheLoopMiddleware` (approval gate),
   `SummarizationMiddleware` (context compaction), `PIIMiddleware` (redaction),
   `ToolRetryMiddleware`, `ToolCallLimitMiddleware`.
   **If you add the security and context-engineering slides, take the examples straight from here.**

---

### Slide 42 — Smoke test

```python
result = agent_executor.invoke(
    {"messages": [("user", "Explain about Software Design Principles")]}
)
print(result["messages"][-1].content)   # [-1], not [1]
```

---

### Slide 44 — Planner (2/3)

```python
from pydantic import BaseModel, Field

class Plan(BaseModel):
    steps: list[str] = Field(
        description="Different steps to follow, should be in sorted order"
    )

planner = planner_prompt | ChatOpenAI(model='gpt-5-nano').with_structured_output(Plan)
```

> `Annotated[List[str], "description"]` is legal Python, but **that description string never
> reaches the model.** In structured output, a field description is part of the prompt the model
> reads, so it has to go through `Field(description=...)`.
> Also switch `List` → `list` and `Dict` → `dict` while you are here (Python 3.9+).

---

### Slide 47 — Replanner (2/2)

Adding a one-line docstring to `Response` helps the model tell the two options apart.

```python
class Response(BaseModel):
    """Final response to the user."""
    response: str
```

The rest can stay as it is.

---

### Slides 55 / 57 — Create graph

```python
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver   # MemorySaver -> InMemorySaver

# ... (nodes and edges unchanged) ...

app = workflow.compile(checkpointer=InMemorySaver())
```

> The graph itself (4 nodes, 1 conditional edge) is unchanged, so the graph image on slide 38
> is still correct.

---

### Slide 58 — Run graph

```python
import uuid
from langchain_core.runnables import RunnableConfig

config = RunnableConfig(
    recursion_limit=15,
    configurable={"thread_id": str(uuid.uuid4())},
)

inputs = {"input": "What are the pros and cons of Shotgun Surgery in software design?"}

# Print what each node updated as it finishes
for chunk in app.stream(inputs, config=config, stream_mode="updates"):
    for node, update in chunk.items():
        print(f"\n=== {node} ===")
        print(update)

print(app.get_state(config).values["response"])
```

> `langchain_teddynote` is a Korean community package. It is imported with no install
> instructions, which makes this the line most likely to throw `ModuleNotFoundError` on the day.
> The standard `stream()` is enough. `stream_mode="updates"` gives each node's output;
> `"values"` gives the full state at every step.

---

## Note on the Colab notebook (`AgentOrchestrationAndWorkflowDesign.ipynb`)

I read it. Four things.

1. **Its ReAct is not newer than the slides — it is older in approach.**
   Cell 23 **parses `"Thought:" / "Action:" / "Final Answer:"` out of the model's text.**
   That is the 2022 implementation from the ReAct paper, before native tool calling existed;
   today it is replaced by `tool_calls`. It contradicts slide 62 ("all the model does is emit
   JSON"), so I would **not port that approach into the deck.**

2. **One thing there is good** — the `step_count >= 10` cap in `should_continue`.
   The slide code has no such guard. `ModelCallLimitMiddleware` on slide 41 plays the same role,
   as does `MAX_STEPS` in `../syllabus/agent_raw.py`.

3. **Cell 23 contains the same code twice** (looks like a copy-paste accident). Worth cleaning
   before it goes out to students.

4. The notebook uses **Gemini + DuckDuckGo**; the slides use **OpenAI + Tavily**. Pick one, or
   students end up creating two sets of API keys.

**What is worth taking from the notebook** is not the parsing style but the idea of
**writing the loop yourself without a framework.** `../syllabus/agent_raw.py` is that idea
rewritten with native tool calling, in 40 lines.
