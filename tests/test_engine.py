import pytest
from typing import Dict, Any
from octochains.engine import Engine
from octochains.base import Agent, Aggregator, tool

def mock_llm_call(prompt: str) -> str:
    return "Mock LLM Response"

# ==========================================
# 1. Mock Agents
# ==========================================
class MockAgent(Agent):
    def __init__(self):
        super().__init__(
            role="Risk Specialist", 
            goal="Identify mock risks",
            input_description="a raw text string containing the business proposal.",
            llm_callable=mock_llm_call
        )

    def execute(self, problem_data: str) -> Any:
        return "High Risk Detected"

class ToolAgent(Agent):
    """An agent specifically designed to test tool discovery and prompt building."""
    def __init__(self):
        super().__init__(
            role="Researcher", 
            goal="Test tools",
            input_description="Dummy input",
            llm_callable=mock_llm_call
        )

    @tool
    def dummy_search(self, query: str):
        """A dummy search tool."""
        return f"Searched for {query}"

    def execute(self, problem_data: str) -> Any:
        # Return the generated prompt instead of the LLM response so we can inspect it
        return self._build_prompt(problem_data)

# ==========================================
# 2. Mock Aggregator (Standard String)
# ==========================================
class MockAggregator(Aggregator):
    def __init__(self):
        super().__init__(
            role="Chief Mock Officer", 
            goal="Return a fixed verdict",
            llm_callable=mock_llm_call
        )

    def execute(self, agent_reports: Dict[str, str]) -> Any:
        # Double-Blind check: Ensure we only got the reports, not the original problem
        assert "Risk Specialist" in agent_reports
        assert agent_reports["Risk Specialist"] == "High Risk Detected"
        return "Final Verdict: REJECTED"

# ==========================================
# 3. Mock Aggregator (Structured JSON/Dict)
# ==========================================
class StructuredAggregator(Aggregator):
    def __init__(self):
        # Testing the optional llm_callable by passing None
        super().__init__(
            role="Structured Mock Officer", 
            goal="Return a JSON object",
            llm_callable=None 
        )

    def execute(self, agent_reports: Dict[str, str]) -> Any:
        # Testing the new 'Any' return type by returning a dictionary
        return {"status": "REJECTED", "reason": agent_reports.get("Risk Specialist")}

# ==========================================
# 4. Engine & Integration Tests
# ==========================================
def test_engine_run_string_output():
    """Tests the standard text-based aggregation."""
    agent = MockAgent()
    aggregator = MockAggregator()
    
    assert agent.input_description == "a raw text string containing the business proposal."

    # Run the engine
    engine = Engine(agents=[agent], aggregator=aggregator)
    result = engine.run("Test Problem")
    
    # Check the final output and traces
    assert result.consensus == "Final Verdict: REJECTED"
    assert len(result.traces) == 1
    assert result.traces[0].agent_role == "Risk Specialist"
    assert result.traces[0].status == "success"

def test_engine_run_structured_output():
    """Tests that the Aggregator and Schema correctly handle dictionary objects."""
    agent = MockAgent()
    aggregator = StructuredAggregator()
    
    engine = Engine(agents=[agent], aggregator=aggregator)
    result = engine.run("Test Problem")
    
    # Prove that the 'Any' update allows objects to pass cleanly through the engine
    assert isinstance(result.consensus, dict)
    assert result.consensus["status"] == "REJECTED"
    assert result.consensus["reason"] == "High Risk Detected"

# ==========================================
# 5. Base Class Feature Tests (NEW)
# ==========================================
def test_agent_prompt_and_tools():
    """Tests that the _build_prompt helper correctly injects tool schemas."""
    agent = ToolAgent()
    
    # Generate the prompt
    prompt = agent.execute("Find the GDP of France")
    
    # Verify Identity Block
    assert "=== YOUR IDENTITY ===" in prompt
    assert "Role: Researcher" in prompt
    
    # Verify Tool Block
    assert "=== AVAILABLE TOOLS ===" in prompt
    assert "dummy_search" in prompt
    assert "A dummy search tool." in prompt
    
    # Verify Data Block
    assert "Find the GDP of France" in prompt

def test_agent_format_output():
    """Tests the safety net that prevents dictionaries from crashing Phase 1 of the engine."""
    agent = MockAgent()
    
    # Simulate an agent returning a raw dictionary instead of a string
    raw_dict = {"risk_level": "High"}
    
    formatted = agent.format_output(raw_dict)
    
    # Ensure it was safely stringified
    assert isinstance(formatted, str)
    assert "High" in formatted