"""See the complexity ladder run, without an API key.

    uv run agent/demo.py                    # a post from the corpus
    uv run agent/demo.py --id 48915735

Every code path here is the real one — the LangGraph graph, the middleware, the tools, the
structured-output parsing, the trajectory capture. Only the model is scripted, and it is scripted
to make one specific mistake: inventing a company the post never names.

That mistake is the point. It's what separates the configs:

    A  single call        no verification exists, so the fabrication survives
    W  workflow           I call verify_claim unconditionally, catch it, revise once
    C  agent              the model may call verify_claim — if it chooses to

With a real model, whether C catches it is a measurement. Here it's scripted both ways so the
mechanism is visible.

**This is a demonstration, not a result.** It cannot tell you which config is better; a scripted
model proves nothing about Claude. It proves the harness distinguishes them.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage

from agent import workflow
from agent.extract_agent import extract as agent_extract
from ingest.corpus import by_id, latest, to_text
from ingest.schema import Extraction

FABRICATED = {"company": "Google", "salary_min": 500000, "salary_max": 600000}


class ToolCallingFake(GenericFakeChatModel):
    def bind_tools(self, tools, **kwargs):
        return self


class StructuredFake:
    """A duck-typed stand-in, not a BaseChatModel subclass.

    The workflow only ever calls `with_structured_output`, so a real model class buys nothing
    and costs something: pydantic model fields can't hold per-instance mutable state cleanly,
    and a shared class attribute would leak scripted responses between tests.
    """

    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls: list = []

    def with_structured_output(self, schema, **kwargs):
        outer = self

        class Runner:
            def invoke(self, prompt, **_):
                outer.calls.append(prompt)
                idx = min(len(outer.calls) - 1, len(outer.responses) - 1)
                return outer.responses[idx]

        return Runner()


def structured_msg(**args):
    base = {"company": None, "role_titles": [], "location": None, "remote": None,
            "salary_min": None, "salary_max": None, "salary_currency": None,
            "salary_period": None, "skills": [], "seniority": None, "visa_sponsor": None}
    return AIMessage(content="", tool_calls=[
        {"name": "Extraction", "id": "s1", "args": {**base, **args}}])


def show(label: str, extraction: Extraction, cost: dict, note: str) -> None:
    d = extraction.model_dump(exclude_defaults=True)
    bad = [k for k in ("company", "salary_min") if k in d and d[k] == FABRICATED.get(k)]
    verdict = "\033[31mFABRICATION SURVIVED\033[0m" if bad else "\033[32mclean\033[0m"
    print(f"\n\033[1m{label}\033[0m")
    print(f"  extracted : {json.dumps(d, default=str)[:96]}")
    print(f"  cost      : {cost}")
    print(f"  outcome   : {verdict}   {note}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--id", help="a comment id; defaults to the first post of the latest thread")
    args = ap.parse_args()

    post = by_id([args.id])[0] if args.id else latest()["comments"][0]
    text = to_text(post.get("comment_text"))

    print("=" * 78)
    print(f"post {post['objectID']}")
    print("=" * 78)
    print(text[:380] + ("..." if len(text) > 380 else ""))
    print(f"\nThe scripted model will claim company={FABRICATED['company']!r} and "
          f"salary={FABRICATED['salary_min']}. Neither appears above.")

    # A — one call, nothing checks it.
    r = agent_extract(text, "A", chat_model=ToolCallingFake(
        messages=iter([structured_msg(**FABRICATED, skills=["Python"])])))
    show("A  single call", r.extraction,
         {"model_calls": r.trajectory.steps, "tools": r.trajectory.n_tool_calls},
         "no verification step exists")

    # W — fixed path. verify_claim runs whether the model likes it or not.
    m = StructuredFake(Extraction(**FABRICATED, skills=["Python"]),
                       Extraction(skills=["Python"]))
    out, trace = workflow.extract(text, chat_model=m)
    show("W  workflow (fixed path)", out,
         {"model_calls": trace.model_calls, "tools": len(trace.tool_calls),
          "revised": trace.revised},
         f"caught {trace.verify_failures} ungrounded values, revised once")

    # C — agent, scripted to actually use its verification tool.
    r = agent_extract(text, "C", chat_model=ToolCallingFake(messages=iter([
        AIMessage(content="", tool_calls=[{"name": "verify_claim", "id": "t1",
                  "args": {"value": FABRICATED["company"], "text": text}}]),
        structured_msg(skills=["Python"]),
    ])))
    show("C  agent (model-directed)", r.extraction,
         {"model_calls": r.trajectory.steps, "tools": r.trajectory.n_tool_calls},
         "model chose to verify — with a real model this is a coin toss, and measuring it "
         "is the experiment")

    print("\n" + "-" * 78)
    print("W and C reached the same answer. W spent a fixed 2 calls; C's cost depends on what")
    print("the model decides to do. Whether the loop is worth that is what labels answer.")


if __name__ == "__main__":
    main()
