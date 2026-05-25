from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, ConfigDict

class Trace(BaseModel):
    """
    Records the 'Evidence' from a single isolated agent.
    This is what provides the transparency in the final report.
    """
    agent_role: str
    status: str  # 'success' or 'error'
    output: Any  # The raw string or Pydantic object from the agent
    error_message: Optional[str] = None

class Report(BaseModel):
    """
    The final output of the Octochains Engine.
    """
    consensus: Any  # The final verdict from the Aggregator
    traces: List[Trace] = Field(default_factory=list) # The list of all agent outputs

    def __repr__(self):
        return f"<Octochains Report: {len(self.traces)} agents analyzed>"
    
    def to_dict(self) -> dict:
        """Standardized helper for JSON serialization."""
        return self.model_dump()
    

# ===============AGGREGATORS===================

class SynthesisResult(BaseModel):
    """Structured output for the Synthesizer."""
    narrative: str
    key_takeaways: List[str]
    confidence: float # [0.0 - 1.0] Subjective confidence score self-assessed by the LLM.
    citations: Dict[str, str] = Field(default_factory=dict) # Key: Expert Role, Value: Snippet
    
    # Silently ignore any extra keys hallucinated by the LLM
    model_config = ConfigDict(extra='ignore')

    def to_dict(self) -> dict:
        """Standardized helper for JSON serialization."""
        return self.model_dump()
        
    def to_json(self) -> str:
        return self.model_dump_json()

class Conflict(BaseModel):
    """Details on a specific logical inconsistency."""
    description: str
    involved_agents: List[str]
    severity: str  # e.g., "Critical", "Moderate", "Minor"

class ConflictReport(BaseModel):
    """Structured output for the ConflictChecker."""
    has_conflicts: bool
    conflicts: List[Conflict]
    summary: str
    
    # Silently ignore any extra keys hallucinated by the LLM
    model_config = ConfigDict(extra='ignore')

    def to_dict(self) -> dict:
        """Standardized helper for JSON serialization."""
        return self.model_dump()
        
    def to_json(self) -> str:
        return self.model_dump_json()