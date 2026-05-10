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
from typing import Dict, List, Callable, Any

def tool(func: Callable):
    """
    A decorator to mark an Agent's method as a tool.
    It marks the function so the Agent can 'discover' it later.
    """
    func._is_octochain_tool = True
    return func

class Agent(ABC):
    """
    The Superior Parent Class for all specialized parallel workers.
    Enforces 'Forced Perspective' and provides automatic tool discovery.
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

    def __init__(self, role: str, goal: str, input_description: str):
        """
        Initializes the Agent.
        
        Args:
            role: The persona of the agent (e.g., "Financial Analyst").
            goal: The objective of the agent (e.g., "Find compliance risks").
            input_description: A short description of the expected input format/content 
                               to help users of the Agent Hub understand how to use it.
        """
        self.role = role
        self.goal = goal
        self.input_description = input_description

    def format_output(self, output: Any) -> str:
        """
        Ensures that whatever the agent returns is converted 
        into a string for the Aggregator to read.
        """
        if isinstance(output, str):
            return output
        
        # If it's a Pydantic model, convert to JSON
        if hasattr(output, "model_dump_json"):
            return output.model_dump_json(indent=2)
            
        # If it's a dict or list, convert to string
        import json
        try:
            return json.dumps(output, indent=2)
        except:
            return str(output)
        
    
    @property
    def tools(self) -> List[Dict[str, Any]]:
        """
        The Discovery Engine.
        Automatically finds all @tool decorated methods and builds a 
        universal JSON schema for tool-calling LLMs (OpenAI, Gemini, etc).
        """
        discovered = []
        for name, method in inspect.getmembers(self, predicate=inspect.ismethod):
            if getattr(method, "_is_octochain_tool", False):
                sig = inspect.signature(method)
                doc = inspect.getdoc(method) or "No description provided."
                
                parameters = {
                    "type": "object",
                    "properties": {},
                    "required": []
                }

                for param_name, param in sig.parameters.items():
                    if param_name == "self":
                        continue
                    
                    # Determine the JSON type based on the Python type hint
                    json_type = self.TYPE_MAP.get(param.annotation, "string")
                    
                    parameters["properties"][param_name] = {
                        "type": json_type,
                        "description": f"Input for {param_name}"
                    }
                    
                    # If there's no default value, it's required
                    if param.default is inspect.Parameter.empty:
                        parameters["required"].append(param_name)

                discovered.append({
                    "name": name,
                    "description": doc,
                    "parameters": parameters
                })
        return discovered

    @abstractmethod
    def execute(self, input_description: str, problem_data: str) -> Any:
        """
        The core reasoning logic. Implement LLM calls (OpenAI, Ollama, etc.) here.
        Use `input_description` to guide the model on what to expect in `problem_data`.
        """
        pass

class Aggregator(ABC):
    """
    The Superior Parent Class for the Aggregator layer (The 'Chief Justice').
    """
    def __init__(self, role: str, goal: str):
        self.role = role
        self.goal = goal

    @abstractmethod
    def execute(self, agent_reports: Dict[str, str]) -> str:
        """
        Takes the results from all parallel agents.
        Returns the final verdict.
        Implement LLM calls (OpenAI, Ollama, etc.) here. (if needed!)
        """
        pass