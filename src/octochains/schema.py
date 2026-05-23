from dataclasses import dataclass, field, asdict
from typing import List, Optional, Any, Dict
import json


@dataclass
class Trace:
    """
    Records the 'Evidence' from a single isolated agent.
    This is what provides the transparency in the final report.
    """
    agent_role: str
    status: str  # 'success' or 'error'
    output: Any  # The raw string or Pydantic object from the agent
    error_message: Optional[str] = None

@dataclass
class Report:
    """
    The final output of the Octochains Engine.
    """
    consensus: Any  # The final verdict from the Aggregator
    traces: List[Trace] = field(default_factory=list) # The list of all agent outputs

    def __repr__(self):
        return f"<Octochains Report: {len(self.traces)} agents analyzed>"
    
    def to_dict(self) -> dict:
        """Standardized helper for JSON serialization."""
        return asdict(self)
    

# ===============AGGREGATORS===================

@dataclass
class SynthesisResult:
    """Structured output for the Synthesizer."""
    narrative: str
    key_takeaways: List[str]
    confidence: float # [0.0 - 1.0] Subjective confidence score self-assessed by the LLM.
    citations: Dict[str, str] = field(default_factory=dict) # Key: Expert Role, Value: Snippet

    def to_dict(self) -> dict:
        """Standardized helper for JSON serialization."""
        return asdict(self)
    def to_json(self) -> str:
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: dict):
        """
        Validates keys and types. 
        Ensures 'confidence' is a float and collections are present.
        """
        # Validate existence of required keys
        required = {'narrative', 'key_takeaways', 'confidence', 'citations'}
        missing = required - data.keys()
        if missing:
            raise ValueError(f"Missing fields in JSON: {missing}")
            
        # Cast/Verify types
        return cls(
            narrative=str(data['narrative']),
            key_takeaways=list(data['key_takeaways']),
            confidence=float(data['confidence']),
            citations=dict(data['citations'])
        )

@dataclass
class Conflict:
    """Details on a specific logical inconsistency."""
    description: str
    involved_agents: List[str]
    severity: str  # e.g., "Critical", "Moderate", "Minor"

@dataclass
class ConflictReport:
    """Structured output for the ConflictChecker."""
    has_conflicts: bool
    conflicts: List[Conflict]
    summary: str

    def to_dict(self) -> dict:
        """Standardized helper for JSON serialization."""
        return asdict(self)
    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict):
        required = {'has_conflicts', 'conflicts', 'summary'}
        if not required.issubset(data.keys()):
            raise ValueError(f"Missing fields in ConflictReport: {required - data.keys()}")
            
        # Reconstruct list of Conflict objects
        conflict_list = [Conflict(**c) for c in data['conflicts']]
        
        return cls(
            has_conflicts=bool(data['has_conflicts']),
            conflicts=conflict_list,
            summary=str(data['summary'])
        )