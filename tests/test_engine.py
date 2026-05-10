import pytest
from octochains import Engine, Agent, Aggregator

# 1. Mock Agent 
class MockAgent(Agent):
    def __init__(self):
        super().__init__(
            role="Risk Specialist", 
            goal="Identify mock risks",
            input_description="a raw text string containing the business proposal."
        )

    def execute(self, problem_data: str):
        return "High Risk Detected"

# 2. Mock Aggregator 
class MockAggregator(Aggregator):
    def __init__(self):
        super().__init__(
            role="Chief Mock Officer", 
            goal="Return a fixed verdict"
        )

    def execute(self, agent_reports: dict[str, str]) -> str:
        # Double-Blind check: Ensure we only got the reports, not the original problem
        assert "Risk Specialist" in agent_reports
        assert agent_reports["Risk Specialist"] == "High Risk Detected"
        return "Final Verdict: REJECTED"

# 3. Test the Engine Flow
def test_engine_run():
    agent = MockAgent()
    aggregator = MockAggregator()
    
    assert agent.input_description == "a raw text string containing the business proposal."

    # Run the engine
    engine = Engine(agents=[agent], aggregator=aggregator)
    result = engine.run("Test Problem")
    
    # Check the final output
    assert result.consensus == "Final Verdict: REJECTED"