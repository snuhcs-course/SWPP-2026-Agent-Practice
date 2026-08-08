"""A ReAct loop with no framework - this is all of it.

Runs on the OpenAI SDK alone: no LangChain, no LangGraph.
The heart of it is a 40-line while loop, and that is essentially what a framework
does for you as well.

The ReAct cell in the Colab notebook parses "Thought:" / "Action:" out of the model's
text. That was how you did it in 2022, before native tool calling existed. Use
tool_calls, as below, and the parsing disappears - and so do the parsing bugs.

Run:
    pip install openai
    export OPENAI_API_KEY=...
    python agent_raw.py "What do we cover in week 5?"
"""

import json
import sys

from openai import OpenAI

import tools_v2 as T   # swap in tools_v1 to compare

MODEL = "gpt-5-nano"
MAX_STEPS = 6          # Without a cap, the loop will eventually spin. Not "might".

client = OpenAI()


def run(question: str, tools=T, verbose: bool = True) -> dict:
    messages = [
        {"role": "system", "content": tools.SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    # Which tools were called, in what order. This is half of the evaluation.
    trajectory: list[str] = []

    for step in range(MAX_STEPS):
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools.SCHEMAS,
        )
        msg = response.choices[0].message
        messages.append(msg.model_dump(exclude_none=True))

        # No tool call means this is the final answer -> leave the loop.
        if not msg.tool_calls:
            return {
                "answer": msg.content or "",
                "trajectory": trajectory,
                "steps": step + 1,
            }

        for call in msg.tool_calls:
            name = call.function.name
            try:
                args = json.loads(call.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}

            fn = tools.REGISTRY.get(name)
            if fn is None:
                # The model can call a tool that does not exist. Guarding is our job.
                result = f"NOT_FOUND: tool '{name}' does not exist."
            else:
                try:
                    result = fn(**args)
                except TypeError as e:
                    # Wrong arguments must not kill the loop; tell the model how to fix it.
                    result = f"NOT_FOUND: bad arguments for {name}: {e}"

            trajectory.append(name)
            if verbose:
                print(f"  [{step + 1}] {name}({args}) -> {str(result)[:90]}")

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(result, ensure_ascii=False, default=str),
                }
            )

    return {
        "answer": "STOPPED: step limit reached.",
        "trajectory": trajectory,
        "steps": MAX_STEPS,
    }


if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "How much is the final exam worth?"
    print(f"Q: {q}")
    out = run(q)
    print(f"\nA: {out['answer']}")
    print(f"\ntrajectory: {out['trajectory']}  ({out['steps']} steps)")
