import pytest
import json
from typing import Dict, Any
from pydantic import BaseModel, Field

from octochains.engine import Engine
from octochains.base import Agent, Aggregator
from octochains.utils import parse_and_validate_json
from octochains.schema import Trace, Report

def mock_llm_call(prompt: str) -> str:
    return "Mock LLM Response"

# ==========================================
# 1. Pydantic Mock Schemas
# ==========================================
class MockStructuredResponse(BaseModel):
    """Used to test the JSON parser's resilience."""
    verdict: str
    score: int
    
    # Simulates the aggregator setup to ignore LLM hallucinations
    model_config = {"extra": "ignore"} 

# ==========================================
# 2. Mock Agents
# ==========================================
class MockAgent(Agent):
    def __init__(self):
        super().__init__(
            role="Risk Specialist", 
            goal="Identify mock risks",
            input_description="A raw text string.",
            llm_callable=mock_llm_call
        )

    def execute(self, problem_data: str) -> Any:
        return "High Risk Detected"

class FailingAgent(Agent):
    """Tests the Engine's resilience to agent crashes."""
    def __init__(self):
        super().__init__(role="Crash Dummy", goal="Fail spectacularly")

    def execute(self, problem_data: str) -> Any:
        raise ValueError("Simulated API Timeout or Execution Failure")

class PromptTestingAgent(Agent):
    """Tests that the base _build_prompt generates the correct identity string."""
    def __init__(self):
        super().__init__(role="Prompt Tester", goal="Verify formatting", input_description="Test Input")

    def execute(self, problem_data: str) -> Any:
        return self._build_prompt(problem_data)

# ==========================================
# 3. Mock Aggregators
# ==========================================
class MockAggregator(Aggregator):
    def __init__(self):
        super().__init__(
            role="Chief Mock Officer", 
            goal="Return a fixed verdict",
            llm_callable=mock_llm_call
        )

    def execute(self, agent_reports: Dict[str, str]) -> Any:
        assert "Risk Specialist" in agent_reports
        return "Final Verdict: REJECTED"

class StructuredAggregator(Aggregator):
    def __init__(self):
        super().__init__(
            role="Structured Mock Officer", 
            goal="Return a JSON object",
            llm_callable=None 
        )

    def execute(self, agent_reports: Dict[str, str]) -> Any:
        return {"status": "REJECTED", "reason": agent_reports.get("Risk Specialist")}

# ==========================================
# 4. Engine & Integration Tests 
# ==========================================
def test_engine_run_string_output():
    """Tests standard text-based execution."""
    agent = MockAgent()
    aggregator = MockAggregator()
    
    engine = Engine(agents=[agent], aggregator=aggregator)
    result = engine.run("Test Problem")
    
    assert result.consensus == "Final Verdict: REJECTED"
    assert len(result.traces) == 1
    assert result.traces[0].agent_role == "Risk Specialist"
    assert result.traces[0].status == "success"

def test_engine_run_structured_output():
    """Tests that the Engine cleanly handles Python dictionary objects without crashing."""
    agent = MockAgent()
    aggregator = StructuredAggregator()
    
    engine = Engine(agents=[agent], aggregator=aggregator)
    result = engine.run("Test Problem")
    
    assert isinstance(result.consensus, dict)
    assert result.consensus["status"] == "REJECTED"

def test_engine_resilience_to_agent_failure():
    """Tests that a failing agent does not crash the entire engine workflow."""
    agent1 = MockAgent()      # Will succeed
    agent2 = FailingAgent()   # Will crash
    aggregator = MockAggregator()
    
    engine = Engine(agents=[agent1, agent2], aggregator=aggregator)
    result = engine.run("Test Problem", show_log=False)
    
    # The aggregator should still run with the successful agent's report
    assert result.consensus == "Final Verdict: REJECTED"
    assert len(result.traces) == 2
    
    # Verify trace statuses
    success_trace = next(t for t in result.traces if t.agent_role == "Risk Specialist")
    failed_trace = next(t for t in result.traces if t.agent_role == "Crash Dummy")
    
    assert success_trace.status == "success"
    assert failed_trace.status == "error"
    assert "Simulated API Timeout" in failed_trace.error_message

# ==========================================
# 5. Base Class Feature Tests
# ==========================================
def test_agent_build_prompt_pure_engine():
    """Tests that the _build_prompt helper generates the strict identity prompt."""
    agent = PromptTestingAgent()
    prompt = agent.execute("Here is the data.")
    
    assert "Role: Prompt Tester" in prompt
    assert "Goal: Verify formatting" in prompt
    assert "Input Description: Test Input" in prompt
    assert "Here is the data." in prompt
    assert "CRITICAL INSTRUCTIONS:" in prompt

def test_agent_format_output_pydantic():
    """Tests that format_output correctly invokes Pydantic's model_dump_json."""
    agent = MockAgent()
    
    # Simulate an agent returning a Pydantic object
    pydantic_obj = MockStructuredResponse(verdict="APPROVED", score=99)
    formatted = agent.format_output(pydantic_obj)
    
    assert isinstance(formatted, str)
    assert "APPROVED" in formatted
    assert "99" in formatted

# ==========================================
# 6. JSON Parsing & Validation Tests
# ==========================================
def test_parse_and_validate_json_success():
    """Tests that the parser correctly extracts and maps valid JSON to a Pydantic model."""
    raw_llm_text = """
    Here is my final analysis based on the data provided:
    {
        "verdict": "PASS",
        "score": 85
    }
    Hope this helps!
    """
    result = parse_and_validate_json(raw_llm_text, MockStructuredResponse)
    
    assert isinstance(result, MockStructuredResponse)
    assert result.verdict == "PASS"
    assert result.score == 85

def test_parse_and_validate_json_with_think_tags():
    """Tests that reasoning model artifacts (<think>) are cleanly stripped."""
    raw_llm_text = """<think>
    Wait, I should calculate the score first. 
    It looks like {"verdict": "FAIL"} but I'll update it.
    </think>
    {
        "verdict": "PASS",
        "score": 90
    }
    """
    result = parse_and_validate_json(raw_llm_text, MockStructuredResponse)
    
    assert result.score == 90

def test_parse_and_validate_json_hallucinated_keys():
    """Tests that extra keys are ignored gracefully if model_config allows it."""
    raw_llm_text = '{"verdict": "PASS", "score": 85, "hallucinated_extra_key": "this would crash a dataclass"}'
    
    result = parse_and_validate_json(raw_llm_text, MockStructuredResponse)
    
    assert result.verdict == "PASS"
    assert not hasattr(result, "hallucinated_extra_key")

def test_parse_and_validate_json_missing_keys():
    """Tests that Pydantic ValidationError is properly wrapped in a ValueError."""
    raw_llm_text = '{"verdict": "PASS"}' # Missing the 'score' field
    
    with pytest.raises(ValueError) as excinfo:
        parse_and_validate_json(raw_llm_text, MockStructuredResponse)
        
    assert "Schema validation failed" in str(excinfo.value)
    assert "score" in str(excinfo.value)


from octochains.exceptions import AggregatorError

# ==========================================
# Additional Mock Classes for Failure Testing
# ==========================================
class TotalCrashAgent(Agent):
    """Simulates a complete agent breakdown."""
    def __init__(self, role_name: str = "Total Crash Dummy"):
        super().__init__(role=role_name, goal="Fail unconditionally")

    def execute(self, problem_data: str) -> Any:
        raise RuntimeError(f"Simulated fatal error in {self.role}")

class FailingAggregator(Aggregator):
    """Simulates an aggregator crashing during consensus generation."""
    def __init__(self):
        super().__init__(
            role="Broken Chief Officer", 
            goal="Fail during synthesis",
            llm_callable=None
        )

    def execute(self, agent_reports: Dict[str, str]) -> Any:
        raise ValueError("Simulated LLM synthesis failure")

class VerifyingAggregator(Aggregator):
    """An aggregator that records exactly what reports it received for assertion."""
    def __init__(self):
        super().__init__(
            role="Verifying Officer", 
            goal="Verify received report keys",
            llm_callable=None
        )
        self.received_keys = []

    def execute(self, agent_reports: Dict[str, str]) -> Any:
        self.received_keys = list(agent_reports.keys())
        return f"Consensus built on: {', '.join(self.received_keys)}"


# ==========================================
# 7. Extended Fault Tolerance & Resilience Tests
# ==========================================
def test_engine_isolates_failures_from_aggregator():
    """
    Ensures that when an agent fails, its error is excluded from the valid reports
    sent to the aggregator, but is still preserved in the audit traces.
    """
    success_agent = MockAgent()
    failing_agent = FailingAgent()
    aggregator = VerifyingAggregator()

    engine = Engine(agents=[success_agent, failing_agent], aggregator=aggregator)
    result = engine.run("Test Problem", show_log=False)

    # 1. Verify the aggregator ONLY received the successful agent's report
    assert "Risk Specialist" in aggregator.received_keys
    assert "Crash Dummy" not in aggregator.received_keys
    assert result.consensus == "Consensus built on: Risk Specialist"

    # 2. Verify the audit trail captures both the success and the specific error
    assert len(result.traces) == 2
    
    success_trace = next(t for t in result.traces if t.agent_role == "Risk Specialist")
    error_trace = next(t for t in result.traces if t.agent_role == "Crash Dummy")

    assert success_trace.status == "success"
    assert success_trace.error_message is None
    assert error_trace.status == "error"
    assert "Simulated API Timeout" in error_trace.error_message


def test_engine_raises_error_on_total_agent_failure():
    """
    Tests that if ALL agents fail, the engine halts immediately and raises
    an AggregatorError instead of executing the aggregator with empty reports.
    """
    agent1 = TotalCrashAgent("Crash Dummy 1")
    agent2 = TotalCrashAgent("Crash Dummy 2")
    aggregator = MockAggregator()

    engine = Engine(agents=[agent1, agent2], aggregator=aggregator)

    # The engine should raise an AggregatorError when zero valid reports exist
    with pytest.raises(AggregatorError) as excinfo:
        engine.run("Test Problem", show_log=False)

    assert "All parallel specialist agents failed" in str(excinfo.value)


def test_engine_wraps_aggregator_failure():
    """
    Tests that if specialist agents succeed but the aggregator fails during synthesis,
    the error is cleanly caught and wrapped in an AggregatorError.
    """
    agent = MockAgent()
    failing_aggregator = FailingAggregator()

    engine = Engine(agents=[agent], aggregator=failing_aggregator)

    with pytest.raises(AggregatorError) as excinfo:
        engine.run("Test Problem", show_log=False)

    assert "The aggregator 'Broken Chief Officer' failed to execute" in str(excinfo.value)
    assert "Simulated LLM synthesis failure" in str(excinfo.value)