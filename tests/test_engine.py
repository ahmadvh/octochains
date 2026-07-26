import pytest
import time
from typing import Dict, Any
from unittest.mock import MagicMock

from octochains.engine import Engine
from octochains.base import Agent, Aggregator
from octochains.schema import Trace, Report
from octochains.exceptions import (
    AggregatorError,
    NoValidReportsError,
    IncompleteAgentBatchError,
)


def mock_llm_call(prompt: str) -> str:
    return "Mock LLM Response"


# =============================================================================
# 1. Mock Agents
# =============================================================================

class MockAgent(Agent):
    def __init__(self, role="Risk Specialist"):
        super().__init__(
            role=role,
            goal="Identify mock risks",
            input_description="A raw text string.",
            llm_callable=mock_llm_call
        )

    def execute(self, problem_data: str) -> Any:
        return "High Risk Detected"


class FailingAgent(Agent):
    """Tests the Engine's resilience to agent crashes."""
    def __init__(self, role="Crash Dummy"):
        super().__init__(role=role, goal="Fail spectacularly")

    def execute(self, problem_data: str) -> Any:
        raise ValueError("Simulated API Timeout or Execution Failure")


class TotalCrashAgent(Agent):
    """Simulates a complete agent breakdown."""
    def __init__(self, role_name: str = "Total Crash Dummy"):
        super().__init__(role=role_name, goal="Fail unconditionally")

    def execute(self, problem_data: str) -> Any:
        raise RuntimeError(f"Simulated fatal error in {self.role}")


class SlowAgent(Agent):
    """Sleeps before returning — used to test agent_timeout and trace ordering."""
    def __init__(self, role: str, sleep_seconds: float, result: str = "Slow Result"):
        super().__init__(role=role, goal="Take some time to respond")
        self.sleep_seconds = sleep_seconds
        self.result = result

    def execute(self, problem_data: str) -> Any:
        time.sleep(self.sleep_seconds)
        return self.result


# =============================================================================
# 2. Mock Aggregators
# =============================================================================

class MockAggregator(Aggregator):
    def __init__(self):
        super().__init__(role="Chief Mock Officer", goal="Return a fixed verdict", llm_callable=mock_llm_call)

    def execute(self, agent_reports: Dict[str, str]) -> Any:
        return "Final Verdict: REJECTED"


class StructuredAggregator(Aggregator):
    def __init__(self):
        super().__init__(role="Structured Mock Officer", goal="Return a JSON object", llm_callable=None)

    def execute(self, agent_reports: Dict[str, str]) -> Any:
        return {"status": "REJECTED", "reason": agent_reports.get("Risk Specialist")}


class FailingAggregator(Aggregator):
    """Simulates an aggregator crashing during consensus generation."""
    def __init__(self):
        super().__init__(role="Broken Chief Officer", goal="Fail during synthesis", llm_callable=None)

    def execute(self, agent_reports: Dict[str, str]) -> Any:
        raise ValueError("Simulated LLM synthesis failure")


class VerifyingAggregator(Aggregator):
    """Records exactly what reports it received for assertion."""
    def __init__(self):
        super().__init__(role="Verifying Officer", goal="Verify received report keys", llm_callable=None)
        self.received_keys = []

    def execute(self, agent_reports: Dict[str, str]) -> Any:
        self.received_keys = list(agent_reports.keys())
        return f"Consensus built on: {', '.join(self.received_keys)}"


# =============================================================================
# 3. Basic Execution
# =============================================================================

class TestBasicExecution:

    def test_string_output(self):
        engine = Engine(agents=[MockAgent()], aggregator=MockAggregator())
        result = engine.run("Test Problem")

        assert result.consensus == "Final Verdict: REJECTED"
        assert len(result.traces) == 1
        assert result.traces[0].agent_role == "Risk Specialist"
        assert result.traces[0].status == "success"

    def test_structured_dict_output(self):
        engine = Engine(agents=[MockAgent()], aggregator=StructuredAggregator())
        result = engine.run("Test Problem")

        assert isinstance(result.consensus, dict)
        assert result.consensus["status"] == "REJECTED"


# =============================================================================
# 4. Fault Isolation (default: require_all_agents=False)
# =============================================================================

class TestFaultIsolationDefault:

    def test_partial_failure_does_not_crash_engine(self):
        agent1, agent2 = MockAgent(), FailingAgent()
        engine = Engine(agents=[agent1, agent2], aggregator=MockAggregator())
        result = engine.run("Test Problem", show_log=False)

        assert result.consensus == "Final Verdict: REJECTED"
        assert len(result.traces) == 2

        success_trace = next(t for t in result.traces if t.agent_role == "Risk Specialist")
        failed_trace = next(t for t in result.traces if t.agent_role == "Crash Dummy")
        assert success_trace.status == "success"
        assert failed_trace.status == "error"
        assert "Simulated API Timeout" in failed_trace.error_message

    def test_failed_agent_excluded_from_aggregator_input(self):
        """Failed agent's error is excluded from valid reports, but preserved in traces."""
        success_agent, failing_agent = MockAgent(), FailingAgent()
        aggregator = VerifyingAggregator()

        engine = Engine(agents=[success_agent, failing_agent], aggregator=aggregator)
        result = engine.run("Test Problem", show_log=False)

        assert "Risk Specialist" in aggregator.received_keys
        assert "Crash Dummy" not in aggregator.received_keys
        assert result.consensus == "Consensus built on: Risk Specialist"

        success_trace = next(t for t in result.traces if t.agent_role == "Risk Specialist")
        error_trace = next(t for t in result.traces if t.agent_role == "Crash Dummy")
        assert success_trace.error_message is None
        assert "Simulated API Timeout" in error_trace.error_message

    def test_default_require_all_agents_is_false(self):
        """Explicit check that the default behaves as passthrough, not a gate."""
        engine = Engine(agents=[MockAgent(), FailingAgent()], aggregator=MockAggregator())
        assert engine.require_all_agents is False
        result = engine.run("Test Problem", show_log=False)  # should NOT raise
        assert result.consensus == "Final Verdict: REJECTED"


# =============================================================================
# 5. Total Failure & Aggregator Failure
# =============================================================================

class TestTotalAndAggregatorFailure:

    def test_all_agents_failing_raises_no_valid_reports_error(self):
        """
        Renamed from AggregatorError -> NoValidReportsError: total agent
        failure and aggregator-itself-failing are now distinct error types.
        """
        engine = Engine(
            agents=[TotalCrashAgent("Crash Dummy 1"), TotalCrashAgent("Crash Dummy 2")],
            aggregator=MockAggregator()
        )

        with pytest.raises(NoValidReportsError) as excinfo:
            engine.run("Test Problem", show_log=False)

        assert "All parallel specialist agents failed" in str(excinfo.value)

    def test_aggregator_crash_raises_aggregator_error(self):
        engine = Engine(agents=[MockAgent()], aggregator=FailingAggregator())

        with pytest.raises(AggregatorError) as excinfo:
            engine.run("Test Problem", show_log=False)

        assert "The aggregator 'Broken Chief Officer' failed to execute" in str(excinfo.value)
        assert "Simulated LLM synthesis failure" in str(excinfo.value)


# =============================================================================
# 6. Duplicate Role Validation
# =============================================================================

class TestDuplicateRoleValidation:

    def test_duplicate_roles_raise_at_construction(self):
        agent1 = MockAgent(role="CFO")
        agent2 = MockAgent(role="CFO")  # same role, would silently collide

        with pytest.raises(ValueError, match="Duplicate agent role"):
            Engine(agents=[agent1, agent2], aggregator=MockAggregator())

    def test_unique_roles_construct_fine(self):
        agent1 = MockAgent(role="CFO")
        agent2 = MockAgent(role="CTO")
        engine = Engine(agents=[agent1, agent2], aggregator=MockAggregator())
        assert len(engine.agents) == 2


# =============================================================================
# 7. require_all_agents Completeness Gate
# =============================================================================

class TestRequireAllAgents:

    def test_partial_failure_raises_incomplete_batch_error(self):
        engine = Engine(
            agents=[MockAgent(role="CFO"), FailingAgent(role="CTO")],
            aggregator=MockAggregator(),
            require_all_agents=True
        )

        with pytest.raises(IncompleteAgentBatchError) as excinfo:
            engine.run("Test Problem", show_log=False)

        assert excinfo.value.failed_roles == ["CTO"]
        assert excinfo.value.succeeded_roles == ["CFO"]

    def test_aggregator_never_called_when_gate_trips(self):
        """The gate must halt BEFORE the aggregator is invoked at all."""
        mock_aggregator = MagicMock(spec=Aggregator)
        mock_aggregator.role = "Mock Boss"

        engine = Engine(
            agents=[MockAgent(role="CFO"), FailingAgent(role="CTO")],
            aggregator=mock_aggregator,
            require_all_agents=True
        )

        with pytest.raises(IncompleteAgentBatchError):
            engine.run("Test Problem", show_log=False)

        mock_aggregator.execute.assert_not_called()

    def test_all_succeeding_proceeds_normally_even_with_gate_enabled(self):
        engine = Engine(
            agents=[MockAgent(role="CFO"), MockAgent(role="CTO")],
            aggregator=MockAggregator(),
            require_all_agents=True
        )
        result = engine.run("Test Problem", show_log=False)  # should NOT raise
        assert result.consensus == "Final Verdict: REJECTED"
        assert len(result.traces) == 2

    def test_total_failure_still_raises_no_valid_reports_even_with_gate_enabled(self):
        """require_all_agents shouldn't mask the separate total-failure path."""
        engine = Engine(
            agents=[TotalCrashAgent("A"), TotalCrashAgent("B")],
            aggregator=MockAggregator(),
            require_all_agents=True
        )
        with pytest.raises(NoValidReportsError):
            engine.run("Test Problem", show_log=False)


# =============================================================================
# 8. agent_timeout
# =============================================================================

class TestAgentTimeout:

    def test_slow_agent_recorded_as_timeout_without_blocking_fast_agents(self):
        fast_agent = SlowAgent(role="Fast", sleep_seconds=0.05, result="Fast Result")
        slow_agent = SlowAgent(role="Slow", sleep_seconds=1.5, result="Slow Result")

        engine = Engine(
            agents=[fast_agent, slow_agent],
            aggregator=VerifyingAggregator(),
            agent_timeout=0.3
        )

        start = time.monotonic()
        result = engine.run("Test Problem", show_log=False)
        elapsed = time.monotonic() - start

        # Should return well before the slow agent's 1.5s sleep completes —
        # proves shutdown(wait=False) is actually taking effect, not just
        # that the trace gets labeled correctly after a long wait.
        assert elapsed < 1.0, f"engine.run() took {elapsed:.2f}s — agent_timeout did not return control promptly"

        fast_trace = next(t for t in result.traces if t.agent_role == "Fast")
        slow_trace = next(t for t in result.traces if t.agent_role == "Slow")

        assert fast_trace.status == "success"
        assert slow_trace.status == "error"
        assert "timed out" in slow_trace.error_message

    def test_no_timeout_set_waits_indefinitely_by_default(self):
        """Default (agent_timeout=None) preserves the original 'wait forever' behavior."""
        agent = SlowAgent(role="Slow", sleep_seconds=0.3, result="Done")
        engine = Engine(agents=[agent], aggregator=MockAggregator())  # agent_timeout unset

        result = engine.run("Test Problem", show_log=False)  # should NOT raise or timeout
        trace = result.traces[0]
        assert trace.status == "success"


# =============================================================================
# 9. Deterministic Trace Ordering
# =============================================================================

class TestTraceOrdering:

    def test_traces_match_input_agent_order_not_completion_order(self):
        """
        Deliberately make the LAST agent in the input list finish FIRST,
        to prove trace order follows input order, not as_completed() order.
        """
        agent_a = SlowAgent(role="A", sleep_seconds=0.3)
        agent_b = SlowAgent(role="B", sleep_seconds=0.05)  # finishes first
        agent_c = SlowAgent(role="C", sleep_seconds=0.15)

        engine = Engine(agents=[agent_a, agent_b, agent_c], aggregator=MockAggregator())
        result = engine.run("Test Problem", show_log=False)

        assert [t.agent_role for t in result.traces] == ["A", "B", "C"]