# ==============================================================================
# Copyright (c) 2026 Ahmad Varasteh (octochains). All rights reserved.
#
# Licensed under the Business Source License 1.1 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
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
        Executes the parallel reasoning workflow with thread-level fault isolation.
        
        1. Launches all agents simultaneously in separate threads.
        2. Collects raw results and traps any individual execution failures.
        3. Pipes ONLY successful specialist evaluations to the Aggregator.
        4. Aggregator synthesizes a final consensus based on valid data.
        
        Args:
            problem_data (str): The input case or data to analyze.
            show_log (bool): If True, prints a detailed execution trace to the console.
            
        Returns:
            Report: The final consensus and a comprehensive audit trail (traces).
        """
        traces: List[Trace] = []
        valid_agent_reports: Dict[str, str] = {}
        logger = logging.getLogger("octochains")
        if show_log:
            print("\n============================================================")
            print("[ENGINE] Booting Octochains Parallel Reasoning Workflow...")
            print(f"[ENGINE] Provisioned Agents: {len(self.agents)}")
            print(f"[ENGINE] Assigned Aggregator: {self.aggregator.role}")
            print("============================================================\n")

        # ---------------------------------------------------------
        # PHASE 1: Parallel Specialist Analysis (Fault Isolated)
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
                    # Retrieve raw output from the isolated thread
                    raw_result = future.result()
                    
                    # Standardize output string strictly for valid results
                    string_result = agent.format_output(raw_result)
                    valid_agent_reports[agent.role] = string_result
                    
                    if show_log:
                        print(f"  └── [Success] Collected structured report from {agent.role}.")
                        
                    # Log success in the immutable audit trace
                    traces.append(Trace(
                        agent_role=agent.role, 
                        status="success", 
                        output=raw_result,
                        error_message=None
                    ))
                    
                except Exception as exc:
                    # Fault Isolation: Trap exception so remaining agents continue uninterrupted
                    error_msg = f"Agent '{agent.role}' failed: {str(exc)}"
                    logger.error(error_msg, exc_info=True)
                    
                    if show_log:
                        print(f"  └── [ERROR] Thread failed for {agent.role}: {str(exc)}")
                    
                    # Record error in trace audit, but DO NOT pollute valid_agent_reports
                    traces.append(Trace(
                        agent_role=agent.role, 
                        status="error", 
                        output=None, 
                        error_message=error_msg
                    ))

        # ---------------------------------------------------------
        # PHASE 2: Aggregated Consensus (Blind Synthesis)
        # ---------------------------------------------------------
        if show_log:
            print(f"\n[ENGINE] >>> PHASE 2: Aggregated Consensus")
            print(f"  ├── [Handoff] Piping {len(valid_agent_reports)} valid reports to {self.aggregator.role}...")
            
        # Guard against total failure where all agents errored out
        if not valid_agent_reports:
            fatal_msg = "All parallel specialist agents failed to execute. Cannot compute consensus."
            logger.critical(fatal_msg)
            if show_log:
                print(f"  └── [FATAL ERROR] {fatal_msg}")
            raise AggregatorError(fatal_msg)

        try:
            # Aggregator synthesizes purely from valid specialist opinions
            consensus = self.aggregator.execute(valid_agent_reports)
            
            if show_log:
                print("  └── [Success] Aggregation complete. Consensus achieved.")
                print("\n============================================================")
                print("[ENGINE] Workflow Terminated Successfully.")
                print("============================================================\n")
                
        except Exception as exc:
            logger.critical(f"Fatal Aggregator Failure: {str(exc)}", exc_info=True)
            if show_log:
                print(f"  └── [FATAL ERROR] {self.aggregator.role} crashed: {str(exc)}")
                print("\n============================================================")
                print("[ENGINE] Workflow Terminated with Errors.")
                print("============================================================\n")
                
            raise AggregatorError(f"The aggregator '{self.aggregator.role}' failed to execute: {str(exc)}") from exc

        return Report(consensus=consensus, traces=traces)