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
import concurrent.futures
from typing import List, Dict
from .base import Agent, Aggregator
from .schema import Trace, Report

class Engine:
    """
    The Orchestrator of the Octochains framework.
    
    It manages the parallel execution of multiple specialized Agents 
    and pipes their collective wisdom into a single Aggregator.
    """

    def __init__(self, agents: List[Agent], aggregator: Aggregator):
        """
        Initialize the engine with workers and a boss.
        
        Args:
            agents (List[Agent]): A list of specialist agents (workers).
            aggregator (Aggregator): The decision-maker (boss).
        """
        self.agents = agents
        self.aggregator = aggregator

    def run(self, problem_data: str, show_log: bool = False) -> Report:
        """
        Executes the parallel reasoning workflow.
        
        1. Launches all agents simultaneously in separate threads.
        2. Collects raw results (Strings, Dicts, or Pydantic objects).
        3. Formats results into strings for the Aggregator.
        4. Aggregator generates a final report based on the collected data.
        
        Args:
            problem_data (str): The input case or data to analyze.
            
        Returns:
            Report: The final consensus and a full audit trail (traces).
        """
        traces: List[Trace] = []
        agent_reports: Dict[str, str] = {}

        # ---------------------------------------------------------
        # PHASE 1: Parallel Specialist Analysis
        # ---------------------------------------------------------
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Create a map of 'Future' objects to their respective Agents
            if show_log:
                for agent in self.agents:
                    print(f"{agent.role} is executing...")
            
            future_to_agent = {
                executor.submit(agent.execute, problem_data): agent 
                for agent in self.agents
            }

            # Gather results as they complete (asynchronous completion)
            for future in concurrent.futures.as_completed(future_to_agent):
                agent = future_to_agent[future]
                try:
                    # Capture the raw output (could be Pydantic, Dict, or Str)
                    raw_result = future.result()
                    
                    # FAULT TOLERANCE: Standardize the output for the Aggregator
                    # We use the method from our base.py to ensure it's a string.
                    string_result = agent.format_output(raw_result)
                    
                    agent_reports[agent.role] = string_result
                    
                    # Log the success in the audit trace
                    traces.append(Trace(
                        agent_role=agent.role, 
                        status="success", 
                        output=raw_result # Trace keeps the rich object if available
                    ))
                    
                except Exception as exc:
                    # If an agent fails, the show must go on.
                    error_msg = f"Failure: {str(exc)}"
                    agent_reports[agent.role] = f"ERROR: {error_msg}"
                    
                    traces.append(Trace(
                        agent_role=agent.role, 
                        status="error", 
                        output=None, 
                        error_message=error_msg
                    ))

        # ---------------------------------------------------------
        # PHASE 2: Aggregated Consensus
        # ---------------------------------------------------------
        try:
            consensus = self.aggregator.execute(agent_reports)
        except Exception as exc:
            consensus = f"CRITICAL ERROR: Aggregator failed to execute. Details: {str(exc)}"

        # Return the final structured Report object
        return Report(consensus=consensus, traces=traces)