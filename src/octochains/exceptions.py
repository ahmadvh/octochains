class OctochainsError(Exception):
    """Base exception for all Octochains-related errors."""
    pass

class AgentExecutionError(OctochainsError):
    """Raised when an individual agent fails during the parallel run."""
    def __init__(self, agent_role: str, original_exception: Exception):
        self.agent_role = agent_role
        self.message = f"Agent '{agent_role}' failed: {str(original_exception)}"
        super().__init__(self.message)

class NoValidReportsError(OctochainsError):
    """
    Raised when every parallel specialist agent failed, leaving zero valid
    reports to aggregate. Distinct from AggregatorError: this means the
    aggregator was never even invoked, not that it failed during synthesis.
    """
    pass

class IncompleteAgentBatchError(OctochainsError):
    """
    Raised when Engine was constructed with require_all_agents=True and at
    least one (but not all) agents failed. Distinct from NoValidReportsError
    (total failure) and AggregatorError (aggregator itself failed) — this
    means partial data existed, but the caller opted out of proceeding on
    an incomplete picture.
    """
    def __init__(self, failed_roles: list, succeeded_roles: list):
        self.failed_roles = failed_roles
        self.succeeded_roles = succeeded_roles
        self.message = (
            f"Engine halted: {len(failed_roles)} agent(s) failed "
            f"({', '.join(failed_roles)}) and require_all_agents=True. "
            f"{len(succeeded_roles)} agent(s) succeeded ({', '.join(succeeded_roles)}) "
            f"but were not passed to the aggregator."
        )
        super().__init__(self.message)

class AggregatorError(OctochainsError):
    """Raised when the Aggregator itself fails to synthesize results."""
    pass