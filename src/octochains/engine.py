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
import logging
from typing import List, Dict
from .base import Agent, Aggregator
from .schema import Trace, Report
from .exceptions import AggregatorError

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
            show_log (bool): If True, prints a detailed execution trace to the console.
            
        Returns:
            Report: The final consensus and a full audit trail (traces).
        """
        traces: List[Trace] = []
        agent_reports: Dict[str, str] = {}

        if show_log:
            print("\n============================================================")
            print("[ENGINE] Booting Octochains Parallel Reasoning Workflow...")
            print(f"[ENGINE] Provisioned Agents: {len(self.agents)}")
            print(f"[ENGINE] Assigned Aggregator: {self.aggregator.role}")
            print("============================================================\n")

        # ---------------------------------------------------------
        # PHASE 1: Parallel Specialist Analysis
        # ---------------------------------------------------------
        if show_log:
            print("[ENGINE] >>> PHASE 1: Parallel Specialist Analysis")

        with concurrent.futures.ThreadPoolExecutor() as executor:
            if show_log:
                for agent in self.agents:
                    print(f"  ├── [Dispatching] Thread launched for {agent.role}...")
            
            future_to_agent = {
                executor.submit(agent.execute, problem_data): agent 
                for agent in self.agents
            }

            for future in concurrent.futures.as_completed(future_to_agent):
                agent = future_to_agent[future]
                try:
                    # Capture the raw output (could be Pydantic, Dict, or Str)
                    raw_result = future.result()
                    
                    # FAULT TOLERANCE: Standardize the output for the Aggregator
                    string_result = agent.format_output(raw_result)
                    
                    agent_reports[agent.role] = string_result
                    
                    if show_log:
                        print(f"  └── [Success] Collected structured report from {agent.role}.")
                        
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
                    
                    logging.error(f"Agent '{agent.role}' execution failed: {error_msg}")
                    if show_log:
                        print(f"  └── [ERROR] Thread failed for {agent.role}: {error_msg}")
                    
                    traces.append(Trace(
                        agent_role=agent.role, 
                        status="error", 
                        output=None, 
                        error_message=error_msg
                    ))

        # ---------------------------------------------------------
        # PHASE 2: Aggregated Consensus
        # ---------------------------------------------------------
        if show_log:
            print(f"\n[ENGINE] >>> PHASE 2: Aggregated Consensus")
            print(f"  ├── [Handoff] Piping {len(agent_reports)} expert reports to {self.aggregator.role}...")
            
        try:
            consensus = self.aggregator.execute(agent_reports)
            
            if show_log:
                print("  └── [Success] Aggregation complete. Consensus achieved.")
                print("\n============================================================")
                print("[ENGINE] Workflow Terminated Successfully.")
                print("============================================================\n")
                
        except Exception as exc:
            logging.critical(f"Fatal Aggregator Failure: {str(exc)}")
            if show_log:
                print(f"  └── [FATAL ERROR] {self.aggregator.role} crashed: {str(exc)}")
                print("\n============================================================")
                print("[ENGINE] Workflow Terminated with Errors.")
                print("============================================================\n")
                
            # Raise explicit exception to guarantee type-safety for downstream apps
            raise AggregatorError(f"The aggregator '{self.aggregator.role}' failed to execute: {str(exc)}") from exc

        # Return the final structured Report object
        return Report(consensus=consensus, traces=traces)