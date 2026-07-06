# ==============================================================================
# Copyright (c) 2026 Ahmad Varasteh (octochains). All rights reserved.
#
# Licensed under the Business Source License 1.1 (the "License");
# you may not use this file except in compliance with the License.
#
# ==============================================================================
import logging
from typing import Any, Callable, Optional
from octochains.base import Aggregator
from octochains.schema import SynthesisResult
from octochains.utils import parse_and_validate_json

logger = logging.getLogger("octochains")

class Synthesizer(Aggregator):
    """
    An official Octochains aggregator designed to merge multiple 
    isolated expert reports into a single, cohesive narrative.
    """
    def __init__(self, 
                 llm_callable: Callable[[str], str], 
                 custom_goal: Optional[str] = None,
                 show_log: bool = False):
        
        default_goal = (
            "Review all expert reports and create a unified, comprehensive final response. "
            "Integrate all unique perspectives into a cohesive narrative while explicitly "
            "removing redundancies and overlapping information."
        )
        super().__init__(
            role="Chief Integration Synthesizer",
            goal=custom_goal or default_goal,
            llm_callable=llm_callable
        )
        
        self.show_log = show_log

    def execute(self, agent_reports: dict[str, str]) -> SynthesisResult:
        if self.show_log:
            print(f"\n[Synthesizer] Starting execution. Integrating {len(agent_reports)} expert reports...")

        if not agent_reports:
            error_msg = "No valid expert reports received. All upstream specialist agents failed or timed out."
            logger.warning(f"[Synthesizer] {error_msg}")
            if self.show_log:
                print(f"[Synthesizer WARNING] {error_msg}")
            
            return SynthesisResult(
                narrative=f"Synthesis Aborted: {error_msg}",
                key_takeaways=["Zero specialist reports available", "Check upstream agent logs"],
                confidence=0.0,
                citations={"System": "No valid data to synthesize."}
            )


        compiled_reports = self._format_reports(agent_reports)
        valid_roles = ", ".join([f'"{role}"' for role in agent_reports.keys()])

        prompt = f"""
        Role: {self.role}
        Goal: {self.goal}
        
        INSTRUCTIONS:
        1. Synthesize the provided expert reports into a single, comprehensive response.
        2. Resolve redundancies and highlight the most critical takeaways.
        3. ANTI-HALLUCINATION GUARDRAIL: Synthesize strictly and ONLY from the reports provided below. Do NOT assume, infer, or fabricate perspectives for any missing domain specialists.
        
        REPORTS:
        {compiled_reports}
        
        Return ONLY valid JSON with the exact following structure:
        {{
            "narrative": "A cohesive narrative merging all unique expert perspectives.",
            "key_takeaways": ["List of actionable insights."],
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
        
        if self.show_log:
            print("[Synthesizer] Prompt constructed. Dispatching integration call to LLM...")

        try:
            # 1. Execute LLM call (Can raise API/Network exceptions)
            raw_output = self.llm_callable(prompt)
            
            # 2. Extract and validate JSON (Can raise ValueError from utils.py)
            result = parse_and_validate_json(raw_output, SynthesisResult)
            
            if self.show_log:
                print(f"[Synthesizer] Success. Generated narrative with {len(result.key_takeaways)} key takeaways (Confidence: {result.confidence}).")
                
            return result
            
        except Exception as e:
            # 3. Catch ALL errors and return the safe Schema object
            logger.error(f"Synthesizer execution failed: {str(e)}")
            
            if self.show_log:
                print(f"[Synthesizer ERROR] Execution failed: {str(e)}")
                
            return SynthesisResult(
                narrative=f"System Error: The synthesizer failed to generate a structured response. Details: {str(e)}",
                key_takeaways=["Execution failure", "Check system logs"],
                confidence=0.0,
                citations={"System": "LLM or Parser failure"}
            )