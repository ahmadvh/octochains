#==============================================================================
#
# Copyright (c) 2026 Ahmad Varasteh (octochains). All rights reserved.
# Licensed under the Business Source License 1.1 (the "License");
#
# you may not use this file except in compliance with the License.
#
#==============================================================================

from typing import Any
from octochains.base import Agent

class SkilledAgent(Agent):
    """
    The concrete, ready-to-use Agent implementation for official Octochains presets.
    
    This agent requires no subclassing. It is defined entirely via configuration
    (role, goal, and injected markdown skills) rather than custom code.
    
    Users should only bypass this and subclass `Agent` directly if they need 
    to implement custom tool-calling, active API fetching, or multi-step 
    reasoning loops inside their execution logic.
    """

    def execute(self, problem_data: str) -> Any:
        """
        The standard execution flow for a purely reasoning-based expert agent.
        
        It retrieves the isolated identity prompt, appends all relevant procedural 
        skill constraints, executes the user's provided LLM, and formats the output.
        """
        # 1. Retrieve the strict, isolated identity and task prompt
        prompt = self._build_prompt(problem_data)

        # 2. Retrieve and format the full text of all applicable procedural skills
        skill_context = self.load_relevant_skills(problem_data)

        if skill_context:
            prompt += f"\n\n=== APPLICABLE SKILL GUIDANCE ===\n{skill_context}\n"

        # 3. Execute the user's BYO-LLM callable
        # We know this exists because base.py enforces the fail-fast check on init
        raw_result = self.llm_callable(prompt)

        # 4. Strip <think> tags and normalize JSON/Pydantic outputs for the Aggregator
        return self.format_output(raw_result)