# File: octochains/schemas/synthesis_result.py (Assumed)

from pydantic import BaseModel, ConfigDict
from typing import List, Dict

class WeightedSynthesisResult(BaseModel):
    """
    The structured result of the WeightedSynthesizer aggregation.
    This structure provides not only the narrative but also explicit metadata 
    regarding how the synthesis was weighted and guided.
    """
    narrative: str  # The primary synthesized, weighted narrative flow.
    key_takeaways: List[str] # Key conclusions derived from the blended perspectives.
    confidence: float # Model's calculated confidence in the synthesized result (0.0 to 1.0).
    citations: Dict[str, str] # Mapping of specific claims or data points back to their source report/agent.
    weights_applied: Dict[str, float] # The configuration weights that shaped this synthesis.
    dominant_perspective: str  # The agent role (key) with the highest weight, defining the core narrative focus.

    model_config = ConfigDict(extra='ignore')