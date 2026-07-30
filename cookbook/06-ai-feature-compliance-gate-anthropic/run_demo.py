"""
Demo 06 — AI Feature Launch Compliance Gate (Anthropic / Claude)

Four regulatory specialists review the same feature dossier in parallel, each in
complete isolation, then a Synthesizer merges their findings into one go / no-go
compliance memo. The LLM is Anthropic's Claude, wired via the official
`anthropic` SDK.

Run:
    export ANTHROPIC_API_KEY=sk-ant-...
    pip install -r requirements.txt
    python run_demo.py
"""
import os

import anthropic

from octochains.engine import Engine
from octochains.aggregators import Synthesizer
from octochains.agents.presets import (
    data_sovereignty_auditor,
    ai_risk_assessor,
    phi_sanitizer,
    licensing_reviewer,
)

# --- Configuration ---
# Swap this for "claude-sonnet-5" or "claude-haiku-4-5" if you want a cheaper/faster run.
MODEL_NAME = "claude-opus-4-8"

# The Anthropic client reads ANTHROPIC_API_KEY from the environment.
client = anthropic.Anthropic()


def call_claude(prompt: str) -> str:
    """
    Model-agnostic llm_callable for Octochains: takes a prompt string, returns text.

    Adaptive thinking is left on (recommended on current Claude models) so the
    specialists reason before answering; we return only the visible text blocks,
    so any thinking blocks are transparently ignored.
    """
    response = client.messages.create(
        model=MODEL_NAME,
        max_tokens=4096,
        thinking={"type": "adaptive"},
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in response.content if block.type == "text")


# =====================================================================
# Run the parallel-isolated compliance council
# =====================================================================
if __name__ == "__main__":
    dossier_path = os.path.join(os.path.dirname(__file__), "sample_input", "feature_dossier.txt")
    with open(dossier_path, "r", encoding="utf-8") as f:
        feature_dossier = f.read()

    print(f"Reviewing feature dossier with {MODEL_NAME} across 4 isolated compliance specialists...\n")

    agents = [
        data_sovereignty_auditor(llm_callable=call_claude),
        ai_risk_assessor(llm_callable=call_claude),
        phi_sanitizer(llm_callable=call_claude),
        licensing_reviewer(llm_callable=call_claude),
    ]

    engine = Engine(
        agents=agents,
        aggregator=Synthesizer(llm_callable=call_claude, show_log=True),
    )

    report = engine.run(problem_data=feature_dossier, show_log=True)

    print("\n" + "=" * 60)
    print("FINAL COMPLIANCE MEMO")
    print("=" * 60)
    print(report.consensus.narrative)

    print("\nKey Takeaways:")
    for takeaway in report.consensus.key_takeaways:
        print(f"  - {takeaway}")

    print(f"\nConfidence: {report.consensus.confidence}")
