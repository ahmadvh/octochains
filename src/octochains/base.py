# ==============================================================================
# Copyright (c) 2026 Ahmad Varasteh (octochains). All rights reserved.
#
# Licensed under the Business Source License 1.1 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://github.com/ahmadvh/octochains/blob/main/LICENSE.md
#
# ==============================================================================
import inspect
from abc import ABC, abstractmethod
from typing import Dict, List, Callable, Any, Optional

# Define the custom type alias for the framework
# The callable takes a string prompt, but can return anything (String, Dict, Object)
LLMCallable = Callable[[str], Any]

def tool(func: Callable):
    """
    A decorator to mark an Agent's method as a tool.
    It marks the function so the Agent can 'discover' it dynamically.
    """
    func._is_octochain_tool = True
    return func


class Agent(ABC):
    """
    The Superior Parent Class for all specialized parallel workers.
    Enforces 'Forced Perspective', provides dynamic tool injection, 
    and handles boilerplate prompt generation.
    """
    # Maps Python type hints to JSON Schema types for universal LLM compatibility
    TYPE_MAP = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object"
    }

    def __init__(self, 
                 role: str, 
                 goal: str, 
                 input_description: str,
                 llm_callable: Optional[LLMCallable] = None):
        """
        Initializes the Agent.
        
        Args:
            role: The specific persona (e.g., "Senior Financial Analyst").
            goal: What this agent is trying to achieve.
            input_description: A short description of the input data. 
            llm_callable: A model-agnostic execution function. 
                          It MUST accept a single argument (prompt: str).
                          It can return a raw string or a structured object.
        """
        self.role = role
        self.goal = goal
        self.input_description = input_description
        self.llm_callable = llm_callable

    def _build_prompt(self, problem_data: str) -> str:
        """
        The "Sensible Default" prompt builder.
        Automatically constructs a highly structured, strict prompt.
        If any @tool methods exist, it dynamically injects their schemas here.
        """
        prompt = f"""
            You are operating in a highly restricted, isolated environment.
            You have NO knowledge of what other agents are doing. Do not assume anything outside your domain.

            === YOUR IDENTITY ===
            Role: {self.role}
            Goal: {self.goal}

            === YOUR TASK ===
            Data Description: {self.input_description}
            """
        
        # DYNAMIC TOOL INJECTION
        tools = self._discover_tools()
        if tools:
            prompt += "\n=== AVAILABLE TOOLS ===\n"
            prompt += "You have access to the following tools. If you need to use a tool, output your request in JSON format.\n"
            for t in tools:
                prompt += f"- Tool Name: {t['name']}\n  Description: {t['description']}\n  Parameters: {t['parameters']}\n"

        prompt += f"""
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
        Ensures the engine always gets a string representation of the output
        in Phase 1, preventing crashes if an object is returned.
        """
        if isinstance(raw_result, str):
            return raw_result
        return str(raw_result)

    def _discover_tools(self) -> List[Dict[str, Any]]:
        """
        Discovers and formats tools marked with the @tool decorator.
        """
        discovered = []
        for name, method in inspect.getmembers(self, predicate=inspect.ismethod):
            if getattr(method, '_is_octochain_tool', False):
                sig = inspect.signature(method)
                doc = inspect.getdoc(method) or "No description provided."
                
                parameters = {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
                
                for param_name, param in sig.parameters.items():
                    if param_name == 'self':
                        continue
                        
                    json_type = self.TYPE_MAP.get(param.annotation, "string")
                    
                    parameters["properties"][param_name] = {
                        "type": json_type,
                        "description": f"Input for {param_name}"
                    }
                    
                    if param.default is inspect.Parameter.empty:
                        parameters["required"].append(param_name)

                discovered.append({
                    "name": name,
                    "description": doc,
                    "parameters": parameters
                })
        return discovered

    @abstractmethod
    def execute(self, problem_data: str) -> Any:
        """
        The core reasoning logic.
        Use `self._build_prompt(problem_data)` to get your strict isolated prompt,
        or completely ignore it and write your own custom prompt if using advanced techniques.
        Execute it using `self.llm_callable(prompt)`.
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