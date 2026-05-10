class OctochainsError(Exception):
    """Base exception for all Octochains-related errors."""
    pass

class AgentExecutionError(OctochainsError):
    """Raised when an individual agent fails during the parallel run."""
    def __init__(self, agent_role: str, original_exception: Exception):
        self.agent_role = agent_role
        self.message = f"Agent '{agent_role}' failed: {str(original_exception)}"
        super().__init__(self.message)

class AggregatorError(OctochainsError):
    """Raised when the Aggregator fails to synthesize results."""
    pass