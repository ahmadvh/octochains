"""
Demo 08 — Security Incident Triage (Anthropic / Claude)

Three security specialists analyse the same incident export in parallel, each in
complete isolation:

  * Security Threat Hunter      — external intrusion, IoCs, ATT&CK tactics
  * Insider Threat Analyst      — misuse by an authenticated user
  * Breach Notification Analyst — regulatory exposure (GDPR Art. 33/34)

A Synthesizer then merges their independent findings into a single incident
triage memo. The LLM is Anthropic's Claude, wired via the official `anthropic`
SDK.

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
    breach_notification_analyst,
    insider_threat_analyst,
    security_threat_hunter,
)

# --- Configuration ---
# Swap for "claude-sonnet-5" or "claude-haiku-4-5" for a cheaper/faster run.
MODEL_NAME = "claude-opus-4-8"

# The Anthropic client reads ANTHROPIC_API_KEY from the environment.
client = anthropic.Anthropic()


def call_claude(prompt: str) -> str:
    """llm_callable for Octochains: takes a prompt string, returns text.

    Adaptive thinking is left on so each specialist reasons before answering; we
    return only the visible text blocks, so any thinking blocks are ignored.
    """
    response = client.messages.create(
        model=MODEL_NAME,
        max_tokens=4096,
        thinking={"type": "adaptive"},
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in response.content if block.type == "text")


if __name__ == "__main__":
    incident_path = os.path.join(os.path.dirname(__file__), "sample_input", "incident_log.txt")
    with open(incident_path, "r", encoding="utf-8") as f:
        incident = f.read()

    print(f"Triaging incident with {MODEL_NAME} across 3 isolated security specialists...\n")

    agents = [
        security_threat_hunter(llm_callable=call_claude),
        insider_threat_analyst(llm_callable=call_claude),
        breach_notification_analyst(llm_callable=call_claude),
    ]

    engine = Engine(
        agents=agents,
        aggregator=Synthesizer(llm_callable=call_claude, show_log=True),
    )

    report = engine.run(problem_data=incident, show_log=True)

    print("\n" + "=" * 60)
    print("INCIDENT TRIAGE MEMO")
    print("=" * 60)
    print(report.consensus.narrative)

    print("\nKey Takeaways:")
    for takeaway in report.consensus.key_takeaways:
        print(f"  - {takeaway}")

    print(f"\nConfidence: {report.consensus.confidence}")
