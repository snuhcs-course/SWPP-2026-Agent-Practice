"""Compare tool design v1 against v2 on the same evaluation set.

The claim this lab is built to test:
    Change nothing about the prompt. Change only the tool design.
    The accuracy moves anyway.

Three things are measured.
    answer   does the final answer contain the supporting fact   (final-answer eval)
    tool     was the expected tool actually called               (trajectory eval)  <- what
                                                                  final-answer eval misses
    refuse   was a question that should be refused, refused      (safety eval)

Run:
    export OPENAI_API_KEY=...
    python run_eval.py                   # LangChain create_agent (default)
    python run_eval.py --runtime raw     # no framework, plain while loop
    python run_eval.py --runtime graph   # explicit LangGraph StateGraph (slide 69)
"""

import argparse
import json
import pathlib

import tools_v1
import tools_v2

HERE = pathlib.Path(__file__).parent
CASES = json.loads((HERE / "eval_set.json").read_text(encoding="utf-8"))

REFUSAL_MARKERS = [
    "not_found", "syllabus does not", "not in the syllabus", "does not cover",
    "cannot help", "can't help", "outside the scope", "out of scope", "i don't have",
]


def score(case: dict, out: dict) -> dict:
    answer = (out.get("answer") or "").lower()
    traj = out.get("trajectory") or []

    expected = case["expect_contains"]
    answer_ok = (not expected) or any(e.lower() in answer for e in expected)

    want_tool = case["expect_tool"]
    if want_tool is None:
        tool_ok = len(traj) == 0            # calling no tool at all is the correct move
    else:
        tool_ok = want_tool in traj

    refused = any(m in answer for m in REFUSAL_MARKERS)
    refuse_ok = refused if case["should_refuse"] else True

    return {"answer": answer_ok, "tool": tool_ok, "refuse": refuse_ok}


def evaluate(runner, tools, label: str) -> list[dict]:
    rows = []
    print(f"\n{'=' * 68}\n{label}\n{'=' * 68}")
    for case in CASES:
        try:
            out = runner(case["question"], tools=tools, verbose=False)
        except Exception as e:                          # noqa: BLE001
            out = {"answer": f"ERROR: {e}", "trajectory": []}
        s = score(case, out)
        rows.append({"id": case["id"], "kind": case["kind"], **s,
                     "trajectory": out.get("trajectory", [])})
        mark = "".join("O" if s[k] else "X" for k in ("answer", "tool", "refuse"))
        print(f"  {case['id']:<4} {mark}  {case['question'][:40]:<42} {out.get('trajectory')}")
    return rows


def summarize(rows: list[dict], label: str) -> None:
    n = len(rows)
    for key in ("answer", "tool", "refuse"):
        hit = sum(r[key] for r in rows)
        print(f"  {label:<12} {key:<7} {hit}/{n}  ({hit / n:.0%})")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--runtime", choices=["langchain", "raw", "graph"], default="langchain"
    )
    args = ap.parse_args()

    if args.runtime == "raw":
        from agent_raw import run
    elif args.runtime == "graph":
        from agent_graph import run
    else:
        from agent_langchain import run

    rows_v1 = evaluate(run, tools_v1, f"[{args.runtime}] tools_v1  (naive: one search tool)")
    rows_v2 = evaluate(run, tools_v2, f"[{args.runtime}] tools_v2  (designed: 4 typed tools)")

    print(f"\n{'=' * 68}\nSUMMARY  (answer = final-answer eval, tool = trajectory eval)\n{'=' * 68}")
    summarize(rows_v1, "tools_v1")
    summarize(rows_v2, "tools_v2")

    (HERE / "eval_result.json").write_text(
        json.dumps({"v1": rows_v1, "v2": rows_v2}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("\nsaved -> eval_result.json")


if __name__ == "__main__":
    main()
