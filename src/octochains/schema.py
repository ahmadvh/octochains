from dataclasses import dataclass, field
from typing import List, Optional, Any

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
    consensus: str  # The final verdict from the Aggregator
    traces: List[Trace] = field(default_factory=list) # The list of all agent outputs

    def __repr__(self):
        return f"<Octochains Report: {len(self.traces)} agents analyzed>"