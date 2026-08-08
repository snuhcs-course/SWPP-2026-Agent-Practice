"""
SWPP 2026 Fall - Week 5
Plan-and-Execute agent with a ReAct sub-agent (LangChain 1.x / LangGraph 1.x)

Slides 39-58, updated to the LangChain 1.0+ API.

What changed from the 2025 version:
  - langgraph.prebuilt.create_react_agent  ->  langchain.agents.create_agent  (deprecated)
  - agent prompt via ChatPromptTemplate    ->  system_prompt= argument
  - MemorySaver                            ->  InMemorySaver  (MemorySaver kept as an alias)
  - langchain_teddynote.messages           ->  app.stream(...)  (standard API)
  - Annotated[..., "description"] in a BaseModel -> Field(description=...)

Run:
    pip install -U langchain langgraph langchain-openai langchain-tavily python-dotenv
    # put OPENAI_API_KEY and TAVILY_API_KEY in .env
    python simple_react.py
"""

import operator
from typing import Annotated, Union

from dotenv import load_dotenv
from typing_extensions import TypedDict
from pydantic import BaseModel, Field

from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableConfig
from langchain_tavily import TavilySearch
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

load_dotenv()

MODEL = "gpt-5-nano"


# ---------------------------------------------------------------- State
class PlanExecute(TypedDict):
    input: Annotated[str, "User's input"]
    plan: Annotated[list[str], "Current plan"]
    past_steps: Annotated[list[tuple], operator.add]
    response: Annotated[str, "Final response"]


# ------------------------------------------------------- Agent and Tool
tools = [TavilySearch(max_results=3)]

# create_agent takes the system prompt as a plain string.
# Do not pass a ChatPromptTemplate the way the 2025 version did.
agent_executor = create_agent(
    model=ChatOpenAI(model=MODEL),
    tools=tools,
    system_prompt="You are a helpful research assistant. Answer in English.",
    # A cap so tool calls cannot run away (no equivalent in the 2025 version)
    middleware=[ModelCallLimitMiddleware(thread_limit=8, exit_behavior="end")],
)


# ----------------------------------------------------------- Planner
planner_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """For the given objective, come up with a simple step-by-step plan. \
This plan should involve individual tasks, that if executed correctly will yield the correct answer. \
Do not add any unnecessary steps. \
The result of the final step should be the final answer. \
Make sure that each step has all the information needed - do not skip steps.
Answer in English. Do not include the answer for each step.""",
        ),
        ("placeholder", "{messages}"),
    ]
)


class Plan(BaseModel):
    steps: list[str] = Field(
        description="Different steps to follow, should be in sorted order"
    )


planner = planner_prompt | ChatOpenAI(model=MODEL).with_structured_output(Plan)


# --------------------------------------------------------- Replanner
replanner_prompt = ChatPromptTemplate.from_template(
    """For the given objective, come up with a simple step-by-step plan. \
This plan should involve individual tasks, that if executed correctly will yield the correct answer. \
Do not add any unnecessary steps. \
The result of the final step should be the final answer. \
Make sure that each step has all the information needed - do not skip steps.

Your objective was this:
{input}

Your original plan was this:
{plan}

You have currently done the following steps:
{past_steps}

Update your plan accordingly. If no more steps are needed and you can return to the user, \
then respond with that. Otherwise, fill out the plan. Only add steps to the plan that still \
NEED to be done. Do not return previously done steps as part of the plan.
Answer in English."""
)


class Response(BaseModel):
    """Final response to the user."""

    response: str


class Act(BaseModel):
    action: Union[Response, Plan] = Field(
        description="Action to perform. If you want to respond to the user, use Response. "
        "If you need to further use tools to get the answer, use Plan."
    )


replanner = replanner_prompt | ChatOpenAI(model=MODEL).with_structured_output(Act)


# ------------------------------------------------------- Final report
final_report_prompt = ChatPromptTemplate.from_template(
    """You are given the objective and the previously done steps. \
Your task is to generate a final report in markdown format.
Final report should be written in a professional tone.

Your objective was this:

{input}

Your previously done steps (question and answer pairs):

{past_steps}

Generate a final report in markdown format. Write your response in English."""
)

final_report = final_report_prompt | ChatOpenAI(model=MODEL) | StrOutputParser()


# ------------------------------------------------------------ Nodes
def plan_step(state: PlanExecute):
    """Generate and return a plan based on user input."""
    plan = planner.invoke({"messages": [("user", state["input"])]})
    return {"plan": plan.steps}


def execute_step(state: PlanExecute):
    """Execute the first task of the plan with the ReAct sub-agent."""
    plan = state["plan"]
    plan_str = "\n".join(f"{i + 1}. {step}" for i, step in enumerate(plan))
    task = plan[0]
    task_formatted = (
        f"For the following plan:\n{plan_str}\n\n"
        f"You are tasked with executing [step 1. {task}]."
    )
    agent_response = agent_executor.invoke({"messages": [("user", task_formatted)]})
    return {"past_steps": [(task, agent_response["messages"][-1].content)]}


def replan_step(state: PlanExecute):
    """Update the plan, or return the final response."""
    output = replanner.invoke(state)
    if isinstance(output.action, Response):
        return {"response": output.action.response}
    next_plan = output.action.steps
    if len(next_plan) == 0:
        return {"response": "No more steps needed."}
    return {"plan": next_plan}


def generate_report(state: PlanExecute):
    """Generate the final report after research is done."""
    past_steps = "\n\n".join(
        f"Question: {q}\n\nAnswer: {a}\n\n####" for q, a in state["past_steps"]
    )
    response = final_report.invoke(
        {"input": state["input"], "past_steps": past_steps}
    )
    return {"response": response}


def should_end(state: PlanExecute):
    """Decide whether to keep executing or write the report."""
    if state.get("response"):
        return "final_report"
    return "execute"


# ------------------------------------------------------------ Graph
def build_app():
    workflow = StateGraph(PlanExecute)

    workflow.add_node("planner", plan_step)
    workflow.add_node("execute", execute_step)
    workflow.add_node("replan", replan_step)
    workflow.add_node("final_report", generate_report)

    workflow.add_edge(START, "planner")
    workflow.add_edge("planner", "execute")
    workflow.add_edge("execute", "replan")
    workflow.add_edge("final_report", END)

    workflow.add_conditional_edges(
        "replan",
        should_end,
        {"execute": "execute", "final_report": "final_report"},
    )

    return workflow.compile(checkpointer=InMemorySaver())


app = build_app()


# ------------------------------------------------------------- Run
if __name__ == "__main__":
    import uuid

    config = RunnableConfig(
        recursion_limit=15,
        configurable={"thread_id": str(uuid.uuid4())},
    )
    inputs = {"input": "What are the pros and cons of Shotgun Surgery in software design?"}

    # Use the standard stream API instead of langchain_teddynote.invoke_graph.
    for chunk in app.stream(inputs, config=config, stream_mode="updates"):
        for node, update in chunk.items():
            print(f"\n=== {node} ===")
            print(update)

    print("\n\n=== FINAL ===")
    print(app.get_state(config).values["response"])
