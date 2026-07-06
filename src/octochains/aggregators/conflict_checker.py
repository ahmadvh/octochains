# ==============================================================================
# Copyright (c) 2026 Ahmad Varasteh (octochains). All rights reserved.
#
# Licensed under the Business Source License 1.1 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#
# ==============================================================================
import itertools
import logging
import concurrent.futures
from typing import Callable, Optional, List, Dict, Any
from octochains.base import Aggregator
from octochains.schema import ConflictReport, Conflict
from octochains.utils import parse_and_validate_json

logger = logging.getLogger("octochains")

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
    """
   
    def __init__(self, 
                 llm_callable: Callable[[str], str], 
                 custom_goal: Optional[str] = None,
                 pairwise_audit: bool = False,
                 max_threads: int = 5,
                 show_log: bool = False):
        
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

    def execute(self, agent_reports: Dict[str, str]) -> ConflictReport:
        if self.show_log:
            mode_str = "Parallel Pairwise (Multi-Threaded)" if self.pairwise_audit else "Global Prompt-Matrix"
            print(f"\n[ConflictChecker] Starting execution. Mode: {mode_str}")
            print(f"[ConflictChecker] Total input reports to audit: {len(agent_reports)}")

        
        if len(agent_reports) < 2:
            error_msg = (
                f"Audit Aborted: Conflict detection mathematically requires at least 2 valid expert reports, "
                f"but only received {len(agent_reports)}. Upstream agent failures prevented pairwise comparison."
            )
            logger.warning(f"[ConflictChecker] {error_msg}")
            if self.show_log:
                print(f"[ConflictChecker WARNING] {error_msg}")
                
            return ConflictReport(
                has_conflicts=False,
                conflicts=[],
                summary=error_msg
            )

        if self.pairwise_audit:
            return self._run_parallel_pairwise_audit(agent_reports)
        else:
            return self._run_prompt_matrix_audit(agent_reports)

    # =========================================================================
    # STRATEGY 1: Dynamic Prompt Matrix (Single Call, Low Cost)
    # =========================================================================
    def _run_prompt_matrix_audit(self, agent_reports: Dict[str, str]) -> ConflictReport:
        compiled_reports = self._format_reports(agent_reports)
        agent_names = list(agent_reports.keys())
        pairs = list(itertools.combinations(agent_names, 2))
        
        matrix_steps = "\n".join([f"Step {i+1}: Look at reports from {a} and {b} and identify conflicts." for i, (a, b) in enumerate(pairs)])
        
        strategy_instruction = (
            "CRITICAL REASONING STRATEGY (INTERNAL MATRIX AUDIT): \n"
            "You must evaluate the reports strictly in the following order before making your final JSON conclusion:\n"
            f"{matrix_steps}\n"
            f"Step {len(pairs)+1}: Consolidate all findings into a single structured output."
        )
            
        prompt = self._build_prompt(compiled_reports, strategy_instruction, valid_roles=agent_names)
        
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
    def _run_parallel_pairwise_audit(self, agent_reports: Dict[str, str]) -> ConflictReport:
        master_conflicts = []
        pairs = list(itertools.combinations(agent_reports.items(), 2))
        
        if self.show_log:
            print(f"[ConflictChecker] Generated {len(pairs)} unique bilateral combinations for isolation.")
            print(f"[ConflictChecker] Spinning up ThreadPoolExecutor (max_workers={self.max_threads})...")

        logger.info(f"Initiating {len(pairs)} parallel LLM threads for Pairwise Audit...")

        # Worker function for the thread pool
        def _check_single_pair(pair) -> List[Conflict]:
            (agent_a, report_a), (agent_b, report_b) = pair
            pair_dict = {agent_a: report_a, agent_b: report_b}
            compiled_pair = self._format_reports(pair_dict)
            
            prompt = self._build_prompt(
                compiled_pair, 
                extra_instruction=f"Focus strictly on direct contradictions between {agent_a} and {agent_b}.",
                valid_roles=[agent_a, agent_b]
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
                logger.error(f"Thread failure for {agent_a} vs {agent_b}: {str(e)}", exc_info=True)
                if self.show_log:
                    print(f"  └── [Thread ERROR] Execution failed for {agent_a} vs {agent_b}: {str(e)}")
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
    def _build_prompt(self, compiled_reports: str, extra_instruction: str = "", valid_roles: Optional[List[str]] = None) -> str:
     
        role_rule = (
            f'- The strings inside "involved_agents" MUST be selected strictly from this list of responding experts: {valid_roles}. Do NOT fabricate agent names.'
            if valid_roles else '- Only include the exact names of the agents participating in the contradiction.'
        )
        
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
                    "severity": "<Critical | Moderate | Minor>" // how severe the contradiction is 
                }}
            ]
        }}
        
        CRITICAL RULES FOR 'involved_agents':
        {role_rule}
        
        If no conflicts are found, set "has_conflicts": false and "conflicts": [].
        """

    def _generate_error_report(self, error: Exception) -> ConflictReport:
        logger.error(f"ConflictChecker execution failed: {str(error)}", exc_info=True)
        return ConflictReport(
            has_conflicts=True,
            conflicts=[Conflict(description=f"System Error: {str(error)}", involved_agents=["System"], severity="Critical")],
            summary="Fatal execution error in the aggregator."
        )