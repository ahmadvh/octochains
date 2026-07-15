# ==============================================================================
# Copyright (c) 2026 Ahmad Varasteh (octochains). All rights reserved.
#
# Licensed under the Business Source License 1.1 (the "License");
# you may not use this file except in compliance with the License.
#
# ==============================================================================

from abc import ABC, abstractmethod
from typing import Dict, List, Callable, Any, Optional
import json
import re
from dataclasses import is_dataclass, asdict
from pydantic import BaseModel 
from .skills import Skill

# Define the custom type alias for the framework
# The callable takes a string prompt, but can return anything (String, Dict, Object)
LLMCallable = Callable[[str], Any]

class Agent(ABC):
    """
    The Base Parent Class for all specialized parallel workers.
    Enforces 'Forced Perspective' and normalizes output, while leaving 
    execution and tool-calling entirely up to the user.
    """

    def __init__(self, 
                 role: str, 
                 goal: str, 
                 input_description: Optional[str] = None,
                 llm_callable: Optional[LLMCallable] = None,
                 skills: Optional[List['Skill']] = None):
        """
        Initializes the Agent.
        
        Args:
            role: The specific persona (e.g., "Senior Financial Analyst").
            goal: What this agent is trying to achieve.
            input_description: A short description of the input data. 
            llm_callable: A model-agnostic execution function. 
            skills: A list of granular procedural markdown skills.
        """
        # Fail-fast check to prevent silent thread crashes and enforce BYO-LLM
        if skills and llm_callable is None:
            raise ValueError(
                f"Agent '{role}' requires an llm_callable because it has skills "
                "attached (skill routing needs an LLM to select relevant guidance). "
                "Pass llm_callable=..., or construct this agent without skills."
            )

        self.role = role
        self.goal = goal
        self.input_description = input_description
        self.llm_callable = llm_callable
        self.skills = skills or []

    def _skill_index(self) -> str:
        """Returns a progressive-disclosure summary of available skills."""
        if not self.skills:
            return ""
        
        index_lines = ["\n            === AVAILABLE SKILLS ==="]
        for skill in self.skills:
            index_lines.append(f"            - {skill.name}: {skill.description}")
        return "\n".join(index_lines)

    def get_skill(self, name: str) -> Optional['Skill']:
        """Retrieves a specific skill by its strictly defined name."""
        for skill in self.skills:
            if skill.name == name:
                return skill
        return None

    def load_relevant_skills(self, problem_data: str) -> str:
        """
        Retrieves the full content of relevant skills. 
        For highly granular presets, this safely formats all injected skills.
        Can be overridden in subclasses for LLM-based dynamic routing if needed.
        """
        if not self.skills:
            return ""
        
        context_lines = []
        for skill in self.skills:
            context_lines.append(f"--- SKILL: {skill.name} (v{skill.version}) ---")
            context_lines.append(skill.content)
            context_lines.append("-" * 40)
            
        return "\n".join(context_lines)

    def _build_prompt(self, problem_data: str) -> str:
        """
        The "Sensible Default" prompt builder.
        Automatically constructs a highly structured, strict identity prompt.
        Users can utilize this in their custom execute() methods to establish the persona.
        """
        prompt = f"""
            You are operating in a highly restricted, isolated environment.
            You have NO knowledge of what other agents are doing. Do not assume anything outside your domain.

            === YOUR IDENTITY ===
            Role: {self.role}
            Goal: {self.goal}{self._skill_index()}

            === YOUR TASK ===
            Input Description: {self.input_description or "Unstructured context data."}
            
            === RAW PROBLEM DATA ===
            {problem_data}

            CRITICAL INSTRUCTIONS:
            Answer strictly from the perspective of your Role. 
            Do not provide a generic summary. Provide actionable, specialized insights based on the data above.

            YOUR SPECIALIZED REPORT:
            """
        return prompt

    def format_output(self, raw_result: Any) -> str:
        """
        Standardizes the agent's output into a clean string for the Aggregator.
        Automatically serializes Dictionaries, Dataclasses, and Pydantic models into JSON.
        Stripping out reasoning traces from thinking models.
        """
        # 1. Detect and serialize the object using native Pydantic serializers first
        if isinstance(raw_result, str):
            string_output = raw_result
        elif isinstance(raw_result, BaseModel):
            string_output = raw_result.model_dump_json(indent=2)
        elif isinstance(raw_result, dict):
            string_output = json.dumps(raw_result, indent=2)
        elif is_dataclass(raw_result):
            string_output = json.dumps(asdict(raw_result), indent=2)
        elif hasattr(raw_result, 'json') and callable(getattr(raw_result, 'json')): 
            # Support for legacy Pydantic V1 models if passed
            string_output = raw_result.json(indent=2)
        else:
            # Fallback for standard classes or primitives
            string_output = str(raw_result)
            
        # 2. Strip thinking model artifacts before sending to the aggregator
        clean_output = re.sub(r'<think>.*?(?:</think>|$)', '', string_output, flags=re.DOTALL)
        
        return clean_output.strip()

    @abstractmethod
    def execute(self, problem_data: str) -> Any:
        """
        The core reasoning logic.
        Use `self._build_prompt(problem_data)` to get your strict isolated prompt,
        or completely ignore it and write your own custom prompt.
        
        Tool calling, API execution, and parsing must be handled here by the user.
        """
        pass


class Aggregator(ABC):
    """
    The Superior Parent Class for the Aggregator layer (The 'Chief Justice').
    """
    def __init__(self, 
                 role: str, 
                 goal: str,
                 llm_callable: Optional[LLMCallable] = None):
        """
        Initializes the Aggregator.
        
        Args:
            role: The persona of the aggregator.
            goal: The overarching objective of the aggregation step.
            llm_callable: A model-agnostic execution function. 
                          It MUST accept a single argument (prompt: str).
                          It can return a raw string, a parsed dictionary, 
                          or a structured object (like a Pydantic model).
        """
        self.role = role
        self.goal = goal
        self.llm_callable = llm_callable

    def _format_reports(self, agent_reports: Dict[str, str]) -> str:
        """
        Helper method to standardize how agent outputs are presented to the LLM.
        """
        formatted = []
        for agent_role, report in agent_reports.items():
            formatted.append(f"=== EXPERT REPORT: {agent_role} ===\n{report}\n")
        return "\n".join(formatted)

    @abstractmethod
    def execute(self, agent_reports: Dict[str, str]) -> Any:
        """
        Takes the results from all parallel agents.
        Returns the final verdict (String, Dict, or Object).
        Use `self._format_reports(agent_reports)` to prepare the context.
        """
        pass