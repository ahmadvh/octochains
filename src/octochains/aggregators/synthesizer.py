import logging
from typing import Any, Callable, Optional
from octochains.base import Aggregator
from octochains.schema import SynthesisResult
from octochains.utils import parse_and_validate_json

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

        compiled_reports = self._format_reports(agent_reports)
        
        prompt = f"""
        Role: {self.role}
        Goal: {self.goal}
        
        INSTRUCTIONS:
        1. Synthesize the provided expert reports into a single, comprehensive response.
        2. Resolve redundancies and highlight the most critical takeaways.
        
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
        - The KEYS of the citations dictionary MUST be the exact names/roles of the agents who provided the reports (e.g., "Global Inventory Analyst", "Director of Logistics").
        - Do NOT literally write "Agent Role" or "<Insert Actual Agent Role>". Use the real roles.

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
            logging.error(f"Synthesizer execution failed: {str(e)}")
            
            if self.show_log:
                print(f"[Synthesizer ERROR] Execution failed: {str(e)}")
                
            return SynthesisResult(
                narrative=f"System Error: The synthesizer failed to generate a structured response. Details: {str(e)}",
                key_takeaways=["Execution failure", "Check system logs"],
                confidence=0.0,
                citations={"System": "LLM or Parser failure"}
            )