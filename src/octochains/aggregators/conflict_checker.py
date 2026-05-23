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
import itertools
import logging
import concurrent.futures
from typing import Callable, Optional
from octochains.base import Aggregator
from octochains.schema import ConflictReport, Conflict
from octochains.utils import parse_and_validate_json

class ConflictChecker(Aggregator):
    """
    Octochains Conflict Checker Aggregator.
    
    This aggregator acts as the deterministic 'Chief Justice' for your multi-agent architecture, 
    auditing isolated expert reports for logical inconsistencies, timeline mismatches, and incompatible claims. 
    
    It supports two distinct architectural strategies for conflict detection, toggleable via the `pairwise_audit` flag.

    Strategy 1: Dynamic Prompt-Matrix (pairwise_audit=False) [DEFAULT]
    ------------------------------------------------------------------
    - Mechanics: Passes all agent reports into a single API call, dynamically injecting a step-by-step 
      matrix instruction. The reasoning model internally evaluates pairs before grading global severity.
    - Pros: Highly cost-effective (1 API call). Capable of catching "Holistic" conflicts.
    - Cons: Slight variance in reasoning paths between runs due to the larger context window.

    Strategy 2 [RECOMMENDED]: Parallel Multi-Threaded Pairwise (pairwise_audit=True)
    ------------------------------------------------------------------
    - Mechanics: Programmatically generates all unique agent combinations (N*(N-1)/2) and fires 
      simultaneous, completely isolated API calls using a ThreadPoolExecutor.
    - Pros: Ironclad determinism. Hyper-focused precision on direct bilateral contradictions.
    - Cons: API costs scale quadratically with the number of agents.

    The Importance of `custom_goal` (Domain-Specific Logic)
    ------------------------------------------------------------------
    In multi-agent reasoning, a generic prompt is a weak prompt. The `custom_goal` parameter allows 
    developers to define the exact "laws of logic" for their specific industry and use case.
    
    - Default Behavior: If omitted, the aggregator defaults to a highly optimized, universal logic prompt 
      that enforces strict counting rules and evidence thresholds (ideal for general logical disputes).
    - Overriding the Default: When providing a `custom_goal`, developers MUST include strict structural 
      guardrails. For example:
        * Medical: "A conflict exists ONLY if Agent A's prescribed treatment makes Agent B's diagnosis fatal."
        * DevOps: "A conflict exists ONLY if the Frontend's requested payload is impossible for the Backend."
        * Legal: "A conflict exists ONLY if complying with Agent A forces a violation of Agent B's rules."
      
      CRITICAL: When overriding, you must instruct the LLM on how to count and consolidate conflicts. 
      Failure to provide strict consolidation rules in a `custom_goal` will result in advanced reasoning 
      models splitting single root-cause issues into multiple false-positive conflicts.
    """
   
    def __init__(self, 
                 llm_callable: Callable[[str], str], 
                 custom_goal: Optional[str] = None,
                 pairwise_audit: bool = False,
                 max_threads: int = 5,
                 show_log: bool = False):
        
        # Generalized for any domain (Tech, Med, Finance, Logic)
        default_goal = (
            "Outcome: A structured audit identifying logical contradictions, factual discrepancies, "
            "fundamentally incompatible claims between the provided agent reports.\n"
            "Constraints: Do not flag omissions. An agent leaving out information outside its specific domain is expected and is NOT a conflict. "
            "CRITICAL COUNTING RULE: You must consolidate conflicts by their core root cause. If multiple agents "
            "conflict over the exact same underlying issue, combine them into a SINGLE comprehensive conflict. Do not split them.\n"
            "Evidence Required: A conflict exists ONLY if Agent A's claim, timeline, or technical requirement makes Agent B's conclusion or strategy practically, mathematically, or logically impossible.\n"
            "Final Answer: Return ONLY valid JSON matching the exact schema."
        )
        super().__init__(
            role="Chief Auditor of Conflicts",
            goal=custom_goal or default_goal,
            llm_callable=llm_callable
        )
        
        self.pairwise_audit = pairwise_audit
        self.max_threads = max_threads
        self.show_log = show_log

    def execute(self, agent_reports: dict[str, str]) -> ConflictReport:
        if self.show_log:
            mode_str = "Parallel Pairwise (Multi-Threaded)" if self.pairwise_audit else "Global Prompt-Matrix"
            print(f"\n[ConflictChecker] Starting execution. Mode: {mode_str}")
            print(f"[ConflictChecker] Total input reports to audit: {len(agent_reports)}")

        if self.pairwise_audit:
            return self._run_parallel_pairwise_audit(agent_reports)
        else:
            return self._run_prompt_matrix_audit(agent_reports)

    # =========================================================================
    # STRATEGY 1: Dynamic Prompt Matrix (Single Call, Low Cost)
    # =========================================================================
    def _run_prompt_matrix_audit(self, agent_reports: dict[str, str]) -> ConflictReport:
        compiled_reports = self._format_reports(agent_reports)
        agent_names = list(agent_reports.keys())
        pairs = list(itertools.combinations(agent_names, 2))
        
        # Programmatically build the step-by-step instructions
        matrix_steps = "\n".join([f"Step {i+1}: Look at reports from {a} and {b} and identify conflicts." for i, (a, b) in enumerate(pairs)])
        
        strategy_instruction = (
            "CRITICAL REASONING STRATEGY (INTERNAL MATRIX AUDIT): \n"
            "You must evaluate the reports strictly in the following order before making your final JSON conclusion:\n"
            f"{matrix_steps}\n"
            f"Step {len(pairs)+1}: Consolidate all findings into a single structured output."
        )
            
        prompt = self._build_prompt(compiled_reports, strategy_instruction)
        
        if self.show_log:
            print(f"[ConflictChecker] Generated dynamic prompt matrix with {len(pairs)} internal comparative steps.")
            print("[ConflictChecker] Dispatching single evaluation call to reasoning LLM...")

        try:
            raw_output = self.llm_callable(prompt)
            result = parse_and_validate_json(raw_output, ConflictReport)
            
            if self.show_log:
                status = f"Success. Found {len(result.conflicts)} conflict(s)." if result.has_conflicts else "Success. No conflicts found."
                print(f"[ConflictChecker] {status}")
                
            return result
        except Exception as e:
            return self._generate_error_report(e)

    # =========================================================================
    # STRATEGY 2: Multi-Threaded Parallel Pairs (Multiple Calls, High Accuracy)
    # =========================================================================
    def _run_parallel_pairwise_audit(self, agent_reports: dict[str, str]) -> ConflictReport:
        master_conflicts = []
        pairs = list(itertools.combinations(agent_reports.items(), 2))
        
        if self.show_log:
            print(f"[ConflictChecker] Generated {len(pairs)} unique bilateral combinations for isolation.")
            print(f"[ConflictChecker] Spinning up ThreadPoolExecutor (max_workers={self.max_threads})...")

        logging.info(f"Initiating {len(pairs)} parallel LLM threads for Pairwise Audit...")

        # Worker function for the thread pool
        def _check_single_pair(pair) -> list[Conflict]:
            (agent_a, report_a), (agent_b, report_b) = pair
            pair_dict = {agent_a: report_a, agent_b: report_b}
            compiled_pair = self._format_reports(pair_dict)
            
            prompt = self._build_prompt(
                compiled_pair, 
                extra_instruction=f"Focus strictly on direct contradictions between {agent_a} and {agent_b}."
            )
            
            if self.show_log:
                print(f"  └── [Thread] Auditing pair: {agent_a} vs {agent_b}")

            try:
                raw_output = self.llm_callable(prompt)
                result = parse_and_validate_json(raw_output, ConflictReport)
                
                if self.show_log:
                    if result.has_conflicts:
                        print(f"  └── [Thread] Found {len(result.conflicts)} conflict(s) between {agent_a} and {agent_b}")
                    else:
                        print(f"  └── [Thread] Clear. No conflicts between {agent_a} and {agent_b}")
                        
                return result.conflicts if result.has_conflicts else []
            except Exception as e:
                logging.error(f"Thread failure for {agent_a} vs {agent_b}: {e}")
                if self.show_log:
                    print(f"  └── [Thread ERROR] Execution failed for {agent_a} vs {agent_b}: {e}")
                return []

        # Execute threads in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            results = list(executor.map(_check_single_pair, pairs))
            
            for thread_conflicts in results:
                master_conflicts.extend(thread_conflicts)
                
        has_conflicts = len(master_conflicts) > 0
        summary = f"Multi-threaded pairwise audit completed across {len(pairs)} pairs. " + ("Conflicts detected." if has_conflicts else "No conflicts found.")
        
        if self.show_log:
            print(f"[ConflictChecker] Thread pool closed. Combined total conflicts discovered: {len(master_conflicts)}")
            
        return ConflictReport(
            has_conflicts=has_conflicts,
            conflicts=master_conflicts,
            summary=summary
        )

    # =========================================================================
    # HELPERS
    # =========================================================================
    def _build_prompt(self, compiled_reports: str, extra_instruction: str = "") -> str:
        return f"""
        Role: {self.role}
        Goal: {self.goal}
        
        {extra_instruction}
        
        REPORTS:
        {compiled_reports}
        
        CRITICAL FORMATTING RULE: 
        You MUST return ONLY valid JSON. Your JSON must exactly match this structure:
        {{
            "has_conflicts": <boolean>,
            "summary": "<string summarizing the overall findings>",
            "conflicts": [
                {{
                    "description": "<string describing the exact contradiction>",
                    "involved_agents": ["<Agent Name 1>", "<Agent Name 2>"],
                    "severity": "<Critical | Moderate | Minor>" # how severe the contradiction is 
                }}
            ]
        }}
        If no conflicts are found, set "has_conflicts": false and "conflicts": [].
        """

    def _generate_error_report(self, error: Exception) -> ConflictReport:
        logging.error(f"ConflictChecker execution failed: {str(error)}")
        return ConflictReport(
            has_conflicts=True,
            conflicts=[Conflict(description=f"System Error: {str(error)}", involved_agents=["System"], severity="Critical")],
            summary="Fatal execution error in the aggregator."
        )