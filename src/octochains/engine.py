# ==============================================================================
# Copyright (c) 2026 Ahmad Varasteh (octochains). All rights reserved.
#
# Licensed under the Business Source License 1.1 (the "License");
# you may not use this file except in compliance with the License.
#
# ==============================================================================
import concurrent.futures
import logging
from typing import List, Dict, Optional
from .base import Agent, Aggregator
from .schema import Trace, Report
from .exceptions import AggregatorError, AgentExecutionError, NoValidReportsError, IncompleteAgentBatchError

logger = logging.getLogger("octochains")


class Engine:
    """
    The Orchestrator of the Octochains framework.

    It manages the parallel execution of multiple specialized Agents
    and pipes their collective wisdom into a single Aggregator.
    """

    def __init__(
        self,
        agents: List[Agent],
        aggregator: Aggregator,
        max_workers: Optional[int] = None,
        agent_timeout: Optional[float] = None,
        require_all_agents: bool = False,
    ):
        """
        Initialize the engine with workers and a boss.

        Args:
            agents (List[Agent]): A list of specialist agents (workers).
                Each agent's `role` must be unique.
            aggregator (Aggregator): The decision-maker (boss).
            max_workers (Optional[int]): Caps concurrent agent threads.
            agent_timeout (Optional[float]): Max seconds to wait for the
                whole parallel batch before treating any still-running
                agents as failed and returning control to the caller.
                Defaults to None (wait indefinitely). Note: Python cannot
                forcibly kill a running thread — a timed-out agent's
                underlying call may continue running in the background,
                detached, after run() returns.
            require_all_agents (bool): If True, ANY agent failure halts
                the workflow BEFORE the aggregator is invoked, raising
                IncompleteAgentBatchError — even if other agents
                succeeded. Total failure (zero successes) always raises
                NoValidReportsError instead, regardless of this flag.
                Defaults to False.
        """
        roles = [agent.role for agent in agents]
        if len(roles) != len(set(roles)):
            duplicates = {r for r in roles if roles.count(r) > 1}
            raise ValueError(
                f"Duplicate agent role(s) detected: {duplicates}. Each agent's "
                "role must be unique — duplicate roles would silently overwrite "
                "each other's reports during aggregation."
            )

        self.agents = agents
        self.aggregator = aggregator
        self.max_workers = max_workers
        self.agent_timeout = agent_timeout
        self.require_all_agents = require_all_agents

    def run(self, problem_data: str, show_log: bool = False) -> Report:
        """
        Executes the parallel reasoning workflow with thread-level fault isolation.
        """
        traces_by_role: Dict[str, Trace] = {}
        valid_agent_reports: Dict[str, str] = {}

        if show_log:
            print("\n============================================================")
            print("[ENGINE] Booting Octochains Parallel Reasoning Workflow...")
            print(f"[ENGINE] Provisioned Agents: {len(self.agents)}")
            print(f"[ENGINE] Assigned Aggregator: {self.aggregator.role}")
            if self.require_all_agents:
                print("[ENGINE] Mode: require_all_agents=True (no partial-data aggregation)")
            print("============================================================\n")

        # ---------------------------------------------------------
        # PHASE 1: Parallel Specialist Analysis (Fault Isolated)
        # ---------------------------------------------------------
        if show_log:
            print("[ENGINE] >>> PHASE 1: Parallel Specialist Analysis")

        # NOTE: managed manually (NOT via `with`) — a plain `with` block
        # always blocks on exit until ALL submitted work finishes, which
        # would silently defeat agent_timeout's purpose of returning
        # control promptly when an agent hangs.
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers)
        timed_out = False

        try:
            if show_log:
                for agent in self.agents:
                    print(f"  ├── [Dispatching] Thread launched for {agent.role}...")

            future_to_agent = {
                executor.submit(agent.execute, problem_data): agent
                for agent in self.agents
            }

            try:
                for future in concurrent.futures.as_completed(future_to_agent, timeout=self.agent_timeout):
                    agent = future_to_agent[future]
                    try:
                        raw_result = future.result()
                        string_result = agent.format_output(raw_result)
                        valid_agent_reports[agent.role] = string_result

                        if show_log:
                            print(f"  └── [Success] Collected structured report from {agent.role}.")

                        traces_by_role[agent.role] = Trace(
                            agent_role=agent.role,
                            status="success",
                            output=raw_result,
                            error_message=None
                        )

                    except Exception as exc:
                        wrapped_error = AgentExecutionError(agent.role, exc)
                        logger.error(wrapped_error.message, exc_info=True)

                        if show_log:
                            print(f"  └── [ERROR] Thread failed for {agent.role}: {str(exc)}")

                        traces_by_role[agent.role] = Trace(
                            agent_role=agent.role,
                            status="error",
                            output=None,
                            error_message=wrapped_error.message
                        )

            except concurrent.futures.TimeoutError:
                timed_out = True
                for future, agent in future_to_agent.items():
                    if not future.done():
                        timeout_msg = f"Agent '{agent.role}' timed out after {self.agent_timeout}s"
                        logger.error(timeout_msg)
                        if show_log:
                            print(f"  └── [TIMEOUT] {timeout_msg}")
                        traces_by_role[agent.role] = Trace(
                            agent_role=agent.role,
                            status="error",
                            output=None,
                            error_message=timeout_msg
                        )
        finally:
            # Normal case: wait for clean shutdown. Timeout case: don't
            # block on stragglers — they may keep running detached in the
            # background; we've already recorded them as failed and moved on.
            executor.shutdown(wait=not timed_out, cancel_futures=timed_out)

        traces: List[Trace] = [traces_by_role[agent.role] for agent in self.agents]

        # ---------------------------------------------------------
        # PHASE 2a: Total Failure Gate (unconditional — checked FIRST,
        # regardless of require_all_agents, since "zero valid data" is a
        # more fundamental problem than "incomplete batch")
        # ---------------------------------------------------------
        if show_log:
            print(f"\n[ENGINE] >>> PHASE 2: Aggregated Consensus")
            print(f"  ├── [Handoff] Piping {len(valid_agent_reports)} valid reports to {self.aggregator.role}...")

        if not valid_agent_reports:
            fatal_msg = "All parallel specialist agents failed to execute. Cannot compute consensus."
            logger.critical(fatal_msg)
            if show_log:
                print(f"  └── [FATAL ERROR] {fatal_msg}")
            raise NoValidReportsError(fatal_msg)

        # ---------------------------------------------------------
        # PHASE 2b: Completeness Gate (opt-in — only relevant once we
        # know at least one agent succeeded but not all of them did)
        # ---------------------------------------------------------
        failed_roles = [t.agent_role for t in traces if t.status == "error"]

        if self.require_all_agents and failed_roles:
            succeeded_roles = [t.agent_role for t in traces if t.status == "success"]
            error = IncompleteAgentBatchError(failed_roles=failed_roles, succeeded_roles=succeeded_roles)
            logger.error(error.message)
            if show_log:
                print(f"\n[ENGINE] >>> HALTED: {error.message}")
                print("============================================================\n")
            raise error

        # ---------------------------------------------------------
        # PHASE 3: Aggregation
        # ---------------------------------------------------------
        try:
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