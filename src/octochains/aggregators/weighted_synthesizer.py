# ==============================================================================
# Copyright (c) 2026 Ahmad Varasteh (octochains). All rights reserved.
#
# Licensed under the Business Source License 1.1 (the "License");
# you may not use this file except in compliance with the License.
#
# ==============================================================================
import logging
from typing import Callable, Dict, Optional

from octochains.base import Aggregator
from octochains.schema import SynthesisResult, WeightedSynthesisResult
from octochains.utils import parse_and_validate_json

logger = logging.getLogger("octochains")


class WeightedSynthesizer(Aggregator):
    """
    An official Octochains aggregator that blends isolated expert reports into a
    single narrative with *proportional emphasis* — higher-weighted perspectives
    drive the framing and conclusions, lower-weighted ones are folded in as
    supporting context.

    This is distinct from conflict resolution (``ConflictChecker``). Weighting
    here is about baseline prominence in the blend, not about resolving
    disagreement — even when all experts fully agree, a heavier weight makes that
    expert the throughline of the narrative.

    Because "weighting qualitative prose" has no literal numeric average, the
    weights shape the *prompt*: each report is annotated with its share and the
    LLM is instructed to structure the narrative accordingly. The audit fields
    on the result (``weights_applied``, ``dominant_perspective``) are computed
    deterministically here, so they always reflect the real configuration rather
    than anything the LLM might hallucinate.

    Args:
        llm_callable: Model-agnostic execution function (prompt: str) -> str.
        weights: Relative emphasis keyed by agent role. Roles present in the
            reports but missing from this dict fall back to ``default_weight``
            (they are never silently dropped). Weights are normalized to sum to
            1.0 for the blend and for ``weights_applied``.
        custom_goal: Optional override for the synthesizer's goal statement.
        default_weight: Weight assigned to any responding role absent from
            ``weights`` (default 1.0 — equal footing).
        show_log: If True, prints progress to stdout.
    """

    def __init__(self,
                 llm_callable: Callable[[str], str],
                 weights: Dict[str, float],
                 custom_goal: Optional[str] = None,
                 default_weight: float = 1.0,
                 show_log: bool = False):

        default_goal = (
            "Review all expert reports and create a unified, comprehensive final response. "
            "Integrate every unique perspective into a cohesive narrative while removing "
            "redundancies — but structure the blend so that higher-weighted perspectives "
            "drive the framing, conclusions, and emphasis, and lower-weighted perspectives "
            "are represented proportionally as supporting context."
        )
        super().__init__(
            role="Weighted Integration Synthesizer",
            goal=custom_goal or default_goal,
            llm_callable=llm_callable
        )

        self.weights = weights or {}
        self.default_weight = default_weight
        self.show_log = show_log

    # =========================================================================
    # WEIGHT RESOLUTION
    # =========================================================================
    def _resolve_weights(self, roles) -> Dict[str, float]:
        """
        Maps each responding role to a normalized weight summing to ~1.0.

        Missing roles get ``default_weight`` (never dropped). If the resolved
        weights are non-positive in total (e.g. all zeros), falls back to an
        equal split so the blend stays well-defined.
        """
        roles = list(roles)
        effective = {role: float(self.weights.get(role, self.default_weight)) for role in roles}

        # Clamp negatives to 0 — a negative emphasis is not meaningful.
        effective = {role: max(0.0, w) for role, w in effective.items()}
        total = sum(effective.values())

        if total <= 0:
            equal = 1.0 / len(roles) if roles else 0.0
            return {role: round(equal, 4) for role in roles}

        return {role: round(w / total, 4) for role, w in effective.items()}

    # =========================================================================
    # EXECUTION
    # =========================================================================
    def execute(self, agent_reports: Dict[str, str]) -> WeightedSynthesisResult:
        if self.show_log:
            print(f"\n[WeightedSynthesizer] Starting execution. Integrating {len(agent_reports)} expert reports...")

        if not agent_reports:
            error_msg = "No valid expert reports received. All upstream specialist agents failed or timed out."
            logger.warning(f"[WeightedSynthesizer] {error_msg}")
            if self.show_log:
                print(f"[WeightedSynthesizer WARNING] {error_msg}")

            return WeightedSynthesisResult(
                narrative=f"Synthesis Aborted: {error_msg}",
                key_takeaways=["Zero specialist reports available", "Check upstream agent logs"],
                confidence=0.0,
                citations={"System": "No valid data to synthesize."},
                weights_applied={},
                dominant_perspective=""
            )

        normalized = self._resolve_weights(agent_reports.keys())
        dominant = max(normalized, key=normalized.get)

        if self.show_log:
            print(f"[WeightedSynthesizer] Resolved weights: {normalized}. Dominant perspective: '{dominant}'.")

        prompt = self._build_prompt(agent_reports, normalized, dominant)

        try:
            raw_output = self.llm_callable(prompt)
            base = parse_and_validate_json(raw_output, SynthesisResult)

            result = WeightedSynthesisResult(
                narrative=base.narrative,
                key_takeaways=base.key_takeaways,
                confidence=base.confidence,
                citations=base.citations,
                weights_applied=normalized,
                dominant_perspective=dominant
            )

            if self.show_log:
                print(f"[WeightedSynthesizer] Success. Narrative structured around '{dominant}' "
                      f"({len(result.key_takeaways)} key takeaways, confidence {result.confidence}).")

            return result

        except Exception as e:
            logger.error(f"WeightedSynthesizer execution failed: {str(e)}")
            if self.show_log:
                print(f"[WeightedSynthesizer ERROR] Execution failed: {str(e)}")

            return WeightedSynthesisResult(
                narrative=f"System Error: The weighted synthesizer failed to generate a structured response. Details: {str(e)}",
                key_takeaways=["Execution failure", "Check system logs"],
                confidence=0.0,
                citations={"System": "LLM or Parser failure"},
                weights_applied=normalized,
                dominant_perspective=dominant
            )

    # =========================================================================
    # PROMPT
    # =========================================================================
    def _build_prompt(self, agent_reports: Dict[str, str], normalized: Dict[str, float], dominant: str) -> str:
        valid_roles = ", ".join([f'"{role}"' for role in agent_reports.keys()])

        # Annotate each report with its weight so the LLM can see the emphasis.
        annotated = []
        for role, report in agent_reports.items():
            pct = round(normalized.get(role, 0.0) * 100, 1)
            annotated.append(f"=== EXPERT REPORT: {role} (emphasis weight: {pct}%) ===\n{report}\n")
        compiled_reports = "\n".join(annotated)

        return f"""
        Role: {self.role}
        Goal: {self.goal}

        INSTRUCTIONS:
        1. Synthesize the expert reports below into a single, comprehensive response.
        2. WEIGHTED EMPHASIS: Each report is annotated with an emphasis weight. Structure the
           narrative so that higher-weighted perspectives drive the framing, conclusions, and
           emphasis. The dominant perspective is "{dominant}" — build the throughline around it.
           Lower-weighted perspectives MUST still be represented, but as proportionally less
           prominent supporting context. Do NOT drop any perspective entirely.
        3. This is emphasis, not conflict resolution: apply the weighting even if all experts agree.
        4. ANTI-HALLUCINATION GUARDRAIL: Synthesize strictly and ONLY from the reports provided.
           Do NOT invent perspectives for missing specialists.

        REPORTS:
        {compiled_reports}

        Return ONLY valid JSON with the exact following structure:
        {{
            "narrative": "A cohesive narrative whose framing and conclusions are driven by the higher-weighted perspectives.",
            "key_takeaways": ["List of actionable insights, ordered so the dominant perspective's points lead."],
            "confidence": 0.0, // Float [0.0 - 1.0] representing your subjective confidence.
            "citations": {{
                "<Insert Actual Agent Role>": "A brief snippet or quote from this agent's report that supports your findings."
            }}
        }}

        CRITICAL DICTIONARY RULES FOR 'citations':
        - The KEYS of the citations dictionary MUST be selected strictly from this list of responding agents: [{valid_roles}].
        - Do NOT literally write "Agent Role" or "<Insert Actual Agent Role>".
        - Do NOT fabricate citation keys for agents that did not provide a report.

        CRITICAL FORMATTING: Do not include any conversational text, markdown formatting, or explanations outside the JSON.
        """
