"""The same tools, run on LangChain 1.x.

The 40-line loop in agent_raw.py collapses into one call to create_agent.
The point is that the tool definitions in tools_v2.py do not change by a single
character - only the runtime around them does.

Run:
    pip install -U langchain langchain-google-genai
    export GOOGLE_API_KEY=...
    python agent_langchain.py "What do we cover in week 5?"
"""

import sys

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware
from langchain_core.messages import AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI

import tools_v2 as T   # swap in tools_v1 to compare

load_dotenv()   # reads ../.env - a real env var still overrides it

MODEL = "gemini-3.5-flash"


def build(tools=T):
    return create_agent(
        model=ChatGoogleGenerativeAI(model=MODEL),
        tools=tools.TOOLS,                 # plain Python functions, passed straight in
        system_prompt=tools.SYSTEM_PROMPT,
        # The equivalent of MAX_STEPS in agent_raw.py
        middleware=[ModelCallLimitMiddleware(thread_limit=6, exit_behavior="end")],
    )


def run(question: str, tools=T, verbose: bool = True) -> dict:
    agent = build(tools)
    result = agent.invoke({"messages": [("user", question)]})

    trajectory = [
        call["name"]
        for m in result["messages"]
        if isinstance(m, AIMessage)
        for call in (m.tool_calls or [])
    ]
    if verbose:
        for name in trajectory:
            print(f"  -> {name}")

    return {
        # .text, not .content: Gemini's AIMessage.content is a list of content
        # blocks, not a plain string. .text is the cross-provider str-subclass
        # accessor LangChain 1.x added for exactly this difference.
        "answer": result["messages"][-1].text,
        "trajectory": trajectory,
        "steps": len(trajectory),
    }


if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "How much is the final exam worth?"
    print(f"Q: {q}")
    out = run(q)
    print(f"\nA: {out['answer']}")
    print(f"\ntrajectory: {out['trajectory']}")
