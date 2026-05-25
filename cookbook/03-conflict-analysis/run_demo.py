import os
from dotenv import load_dotenv

from pydantic import BaseModel,  field_validator, ConfigDict

from octochains.base import Agent
from octochains.engine import Engine
from octochains.aggregators import ConflictChecker
from octochains.utils import parse_and_validate_json
from openai import OpenAI

# 1. Load API Key
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "your-key-here")
openai_client = OpenAI()

def call_openai(prompt: str) -> str:
    """Helper function to call OpenAI directly for deterministic analysis in Phase 1."""
    response = openai_client.chat.completions.create(
        model="gpt-4o", 
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )
    return response.choices[0].message.content


# ==============================================================================
# 2. Define Output Schemas for Agents using pydantic
# ==============================================================================

class FinancialAssessment(BaseModel):
    valuation_verdict: str
    risk_level: str
    primary_concern: str
    
    # Silently discard any extra hallucinated keys from the LLM
    model_config = ConfigDict(extra='ignore')

class TechDueDiligence(BaseModel):
    architecture_viability: str
    estimated_refactor_timeline: str
    blockers: list[str]
    
    model_config = ConfigDict(extra='ignore')

    # Robust coercion to handle LLM hallucinations 
    @field_validator('blockers', mode='before')
    @classmethod
    def ensure_list_format(cls, v):
        if isinstance(v, str):
            return [v]
        elif isinstance(v, list):
            return [str(b) for b in v]
        return []

class RevenueProjection(BaseModel):
    q3_upsell_confidence: str
    expected_integration_speed: str
    scaling_rationale: str  # Added to give the Conflict Checker enough context
    
    model_config = ConfigDict(extra='ignore')


# ==============================================================================
# 3. Define the Specialized Agents 
# ==============================================================================

class CFOAgent(Agent):
    def __init__(self):
        super().__init__(
            role="Chief Financial Officer",
           goal="Evaluate financial viability. You MUST extract the exact runway timeline (e.g., months left) and specific cash burn numbers into your primary concern."
        )
    def execute(self, data: str) -> FinancialAssessment:
        prompt = f"{self.goal}\n\nDOSSIER:\n{data}\n\nReturn ONLY raw JSON with keys: valuation_verdict, risk_level, primary_concern."
        raw_json = call_openai(prompt)
        # parse_and_validate_json automatically utilizes FinancialAssessment.model_validate()
        return parse_and_validate_json(raw_json, FinancialAssessment)

class CTOAgent(Agent):
    def __init__(self):
        super().__init__(
            role="Chief Technology Officer",
            goal="Evaluate technical architecture. Focus on infrastructure costs, tech debt, and key personnel risks."
        )
    def execute(self, data: str) -> TechDueDiligence:
        prompt = f"{self.goal}\n\nDOSSIER:\n{data}\n\nReturn ONLY raw JSON with keys: architecture_viability, estimated_refactor_timeline, blockers."
        raw_json = call_openai(prompt)
        return parse_and_validate_json(raw_json, TechDueDiligence)

class CROAgent(Agent):
    def __init__(self):
        super().__init__(
            role="Chief Revenue Officer",
            goal="Evaluate the market synergy. You MUST extract the exact target metrics, client volume, and explicit timelines (e.g., Q3) for the cross-selling strategy and include them in your scaling rationale."
        )
    def execute(self, data: str) -> RevenueProjection:
        prompt = f"{self.goal}\n\nDOSSIER:\n{data}\n\nReturn ONLY raw JSON with keys: q3_upsell_confidence, expected_integration_speed, scaling_rationale."
        raw_json = call_openai(prompt)
        return parse_and_validate_json(raw_json, RevenueProjection)


# ==============================================================================
# 4. Orchestration & Execution
# ==============================================================================

def main():
    print("Loading Confidential Target Dossier...")
    input_path = "cookbook/03-conflict-analysis/sample_input/target_dossier.txt"
    output_path = "cookbook/03-conflict-analysis/results/output.txt"
    
    try:
        with open(input_path, "r") as f:
            dossier_data = f.read()
    except FileNotFoundError:
        print(f"Error: {input_path} not found.")
        return

    # Initialize the parallel workers
    agents = [CFOAgent(), CTOAgent(), CROAgent()]
    
    # define custom goal 
    ma_due_diligence_goal = (
        "Outcome: A structured executive audit identifying fatal M&A risks, valuation illusions, "
        "timeline paradoxes, and fundamentally incompatible strategies between the C-suite reports.\n"
        "Constraints: Do not flag omissions. A department head ignoring an out-of-domain metric is expected. "
        "Furthermore, if two executives agree on a risk (e.g., both acknowledge the founder leaving), this is alignment, NOT a conflict. Do not flag agreements.\n"
        "CRITICAL COUNTING RULE: You must consolidate conflicts by their core root cause. If a massive infrastructure cost "
        "simultaneously ruins the CRO's profit margins and invalidates the CFO's $12M valuation, combine this into a SINGLE "
        "comprehensive 'Valuation/Margin' conflict. Do not split symptoms into multiple bullet points.\n"
        "Evidence Required: A conflict exists ONLY if Expert A's hard timeline, financial runway, or technical debt makes Expert B's "
        "revenue projection or integration strategy mathematically impossible or financially disastrous.\n"
        "Final Answer: Return ONLY valid JSON matching the exact schema."
    )
    
    # Initialize the Aggregator
    boss = ConflictChecker(
        llm_callable=call_openai, 
        pairwise_audit=True, # Running pairwise comparison
        custom_goal=ma_due_diligence_goal,
        max_threads= 3, # Optimized for 3 pairs (CFO/CTO, CFO/CRO, CTO/CRO)
        show_log=True
    )

    # Initialize the Framework Engine
    engine = Engine(agents=agents, aggregator=boss)
    
    report = engine.run(problem_data=dossier_data, show_log=True)

    # ==============================================================================
    # 5. Format and Save the Output
    # ==============================================================================
    
    print("\n[Engine] Formatting results for output.txt...")
    output_lines = [
        "Octochains: Executive Conflict Analysis Report\n",
        "="*60,
        " PHASE 1: ISOLATED EXPERT FINDINGS (STRUCTURED DATA)",
        "="*60
    ]

    # Append Phase 1: Structured JSON Outputs
    for trace in report.traces:
        output_lines.append(f"\n[{trace.agent_role}]")
        if trace.status == "success":
            # UPDATED: Use Pydantic's native JSON serialization instead of __dict__
            output_lines.append(trace.output.model_dump_json(indent=2))
        else:
            output_lines.append(f"Error: {trace.error_message}")

    output_lines.extend([
        "\n" + "="*60,
        " PHASE 2: CONFLICT AUDIT (EXECUTIVE SUMMARY)",
        "="*60
    ])
    
    # Append Phase 2: Structured Audit 
    if report.consensus.has_conflicts:
        output_lines.append("\n🚨 CRITICAL MISALIGNMENTS DETECTED 🚨\n")
        for conflict in report.consensus.conflicts:
            output_lines.append(f"- Severity: {conflict.severity}")
            output_lines.append(f"  Involved: {', '.join(conflict.involved_agents)}")
            output_lines.append(f"  Description: {conflict.description}\n")
        
        output_lines.append(f"Executive Summary:\n{report.consensus.summary}\n")
    else:
        output_lines.append("\nAll executive perspectives are aligned. Clear to proceed.")

    # Ensure output directory exists before writing
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Write the compiled content to output.txt
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))
        
    print(f"\n✅ Analysis complete. Results successfully saved to {output_path}")

if __name__ == "__main__":
    main()