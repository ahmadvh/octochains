import os
import json
from dotenv import load_dotenv

from octochains.base import Aggregator
from octochains.engine import Engine
from octochains.aggregators import WeightedSynthesizer
from octochains.agents.presets import cfo_agent, cto_agent, cro_agent, cpo_agent, cmo_agent
from openai import OpenAI


# ==============================================================================
# 1. Load API Key
# ==============================================================================
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "your-key-here")
openai_client = OpenAI()


def call_openai(prompt: str) -> str:
    """Helper function to call OpenAI directly for deterministic analysis."""
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content


class PassthroughAggregator(Aggregator):
    """No LLM call. Returns the isolated agent reports unchanged."""

    def __init__(self):
        super().__init__(role="Passthrough", goal="Pass reports through unchanged.")

    def execute(self, agent_reports):
        return agent_reports


# Weight Profiles
# Same five experts, same dossier — but who should shape the narrative depends entirely on WHY you're reading this report. Neither profile is more "correct" than the other; they're different lenses on identical evidence.

WEIGHT_PROFILES = {
    "acquihire": {
        "label": "Acquihire Framing — buying for engineering talent & architecture",
        "weights": {
            "Chief Technology Officer (CTO)": 0.55,
            "Chief Product Officer (CPO)": 0.20,
            "Chief Financial Officer (CFO)": 0.10,
            "Chief Revenue Officer (CRO)": 0.075,
            "Chief Marketing Officer (CMO)": 0.075,
        },
    },
    "growth_equity": {
        "label": "Growth-Equity Framing — buying for revenue trajectory & efficiency",
        "weights": {
            "Chief Financial Officer (CFO)": 0.40,
            "Chief Marketing Officer (CMO)": 0.25,
            "Chief Revenue Officer (CRO)": 0.20,
            "Chief Technology Officer (CTO)": 0.10,
            "Chief Product Officer (CPO)": 0.05,
        },
    },
}


def main():
    print("Loading Confidential Target Dossier...")
    input_path = "cookbook/07-weighted-due-diligence/sample_input/target_dossier.txt"
    output_path = "cookbook/07-weighted-due-diligence/results/output.txt"

    try:
        with open(input_path, "r") as f:
            dossier_data = f.read()
    except FileNotFoundError:
        print(f"Error: {input_path} not found.")
        return

    # Initialize the parallel workers using OFFICIAL PRESETS — the full
    # Startup Due-Diligence Council.
    agents = [
        cfo_agent(llm_callable=call_openai),
        cto_agent(llm_callable=call_openai),
        cro_agent(llm_callable=call_openai),
        cpo_agent(llm_callable=call_openai),
        cmo_agent(llm_callable=call_openai),
    ]


    # PHASE 1: Run the isolated council ONCE. To get the report
    engine = Engine(agents=agents, aggregator=PassthroughAggregator())
    report = engine.run(problem_data=dossier_data, show_log=True)

    valid_reports = {
        trace.agent_role: trace.output
        for trace in report.traces
        if trace.status == "success"
    }

    if len(valid_reports) < len(agents):
        failed = [t.agent_role for t in report.traces if t.status == "error"]
        print(f"⚠️  Warning: {len(failed)} agent(s) failed and will be excluded: {failed}")

    
    # PHASE 2: Reweight the SAME isolated reports under two different lenses.
    # No agent is re-queried between profiles — only the aggregator changes.
    output_lines = [
        "Octochains: Weighted Due-Diligence — Same Reports, Two Verdicts\n",
        "=" * 70,
        " PHASE 1: ISOLATED EXPERT FINDINGS (unchanged across both profiles)",
        "=" * 70,
    ]
    for trace in report.traces:
        output_lines.append(f"\n[{trace.agent_role}]")
        output_lines.append(trace.output if trace.status == "success" else f"Error: {trace.error_message}")

    for profile in WEIGHT_PROFILES.values():
        print(f"\n[Demo] Synthesizing under profile: {profile['label']}")

        boss = WeightedSynthesizer(
            llm_callable=call_openai,
            weights=profile["weights"],
            show_log=True,
        )
        result = boss.execute(valid_reports)

        output_lines.extend([
            "\n" + "=" * 70,
            f" {profile['label']}",
            "=" * 70,
            f"Dominant Perspective: {result.dominant_perspective}",
            f"Weights Applied: {json.dumps(result.weights_applied, indent=2)}",
            f"\nNarrative:\n{result.narrative}",
            "\nKey Takeaways:",
        ])
        output_lines.extend(f"  - {t}" for t in result.key_takeaways)
        output_lines.append(f"\nConfidence: {result.confidence}")

    # ==========================================================================
    # 4. Save Output
    # ==========================================================================
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))

    print(f"\n✅ Weighted due-diligence comparison saved to {output_path}")


if __name__ == "__main__":
    main()
