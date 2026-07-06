import pytest
import json
from unittest.mock import MagicMock, patch
from typing import Dict

from octochains.aggregators.conflict_checker import ConflictChecker
from octochains.schema import ConflictReport, Conflict


# ==========================================
# 1. Mock Data & JSON Responses
# ==========================================
MOCK_CONFLICT_JSON = json.dumps({
    "has_conflicts": True,
    "summary": "Contradiction detected regarding port configurations.",
    "conflicts": [
        {
            "description": "Security demands Port 443 exclusively, but DevOps requires Port 80 for HTTP validation.",
            "involved_agents": ["Security Analyst", "DevOps Engineer"],
            "severity": "Critical"
        }
    ]
})

MOCK_CLEAR_JSON = json.dumps({
    "has_conflicts": False,
    "summary": "All expert strategies align without logical contradiction.",
    "conflicts": []
})


@pytest.fixture
def mock_llm_callable():
    """Returns a MagicMock that simulates an LLM response."""
    mock = MagicMock()
    mock.return_value = MOCK_CLEAR_JSON
    return mock


@pytest.fixture
def sample_reports() -> Dict[str, str]:
    """Returns a standard 3-agent expert panel output."""
    return {
        "Security Analyst": "All traffic must be encrypted over Port 443. HTTP Port 80 must be blocked.",
        "DevOps Engineer": "We need Port 80 open for AWS ALB health check validations.",
        "Data Scientist": "Model training requires 4x A100 GPUs with CUDA 12 support."
    }


# ==========================================
# 2. Mathematical Safety Gate Tests (N < 2)
# ==========================================
def test_mathematical_gate_zero_reports(mock_llm_callable):
    """
    Tests that passing an empty dictionary (0 reports) immediately aborts
    the audit without making any LLM calls.
    """
    checker = ConflictChecker(llm_callable=mock_llm_callable)
    result = checker.execute({})

    # Assert zero tokens wasted
    mock_llm_callable.assert_not_called()
    
    # Assert clean fallback report
    assert result.has_conflicts is False
    assert len(result.conflicts) == 0
    assert "Audit Aborted" in result.summary
    assert "mathematically requires at least 2" in result.summary


def test_mathematical_gate_single_report(mock_llm_callable):
    """
    Tests that passing exactly 1 surviving report (e.g., when 4/5 agents fail)
    immediately aborts the audit without making any LLM calls.
    """
    checker = ConflictChecker(llm_callable=mock_llm_callable)
    result = checker.execute({"Security Analyst": "Everything looks secure."})

    mock_llm_callable.assert_not_called()
    assert result.has_conflicts is False
    assert "only received 1" in result.summary


# ==========================================
# 3. Strategy 1: Prompt Matrix Tests
# ==========================================
def test_strategy_1_prompt_matrix_execution(mock_llm_callable, sample_reports):
    """
    Tests Strategy 1 (pairwise_audit=False). Verifies that a single API call is made
    and that the dynamic role binding and step matrix are injected into the prompt.
    """
    mock_llm_callable.return_value = MOCK_CONFLICT_JSON
    checker = ConflictChecker(llm_callable=mock_llm_callable, pairwise_audit=False)
    
    result = checker.execute(sample_reports)

    # 1. Verify exact API call count (Strategy 1 is always 1 call)
    assert mock_llm_callable.call_count == 1
    
    # 2. Inspect the generated prompt sent to the LLM
    prompt_sent = mock_llm_callable.call_args[0][0]
    
    # Check that dynamic matrix steps were built for 3 pairs: (N*(N-1)/2) -> 3*2/2 = 3 steps
    assert "Step 1: Look at reports from Security Analyst and DevOps Engineer" in prompt_sent
    assert "Step 3: Look at reports from DevOps Engineer and Data Scientist" in prompt_sent
    assert "Step 4: Consolidate all findings" in prompt_sent
    
    # Check that dynamic anti-hallucination role binding was injected
    assert "selected strictly from this list of responding experts: ['Security Analyst', 'DevOps Engineer', 'Data Scientist']" in prompt_sent
    
    # 3. Verify output parsing
    assert result.has_conflicts is True
    assert len(result.conflicts) == 1
    assert result.conflicts[0].severity == "Critical"


def test_strategy_1_fatal_llm_exception(mock_llm_callable, sample_reports):
    """
    Tests that if the LLM or parser throws an unhandled exception during Strategy 1,
    the checker catches it and returns a clean system error ConflictReport.
    """
    mock_llm_callable.side_effect = RuntimeError("Simulated OpenAI API Timeout")
    checker = ConflictChecker(llm_callable=mock_llm_callable, pairwise_audit=False)
    
    result = checker.execute(sample_reports)

    assert result.has_conflicts is True
    assert len(result.conflicts) == 1
    assert "Simulated OpenAI API Timeout" in result.conflicts[0].description
    assert result.conflicts[0].involved_agents == ["System"]
    assert result.summary == "Fatal execution error in the aggregator."


# ==========================================
# 4. Strategy 2: Parallel Pairwise Tests
# ==========================================
def test_strategy_2_parallel_pairwise_execution(mock_llm_callable, sample_reports):
    """
    Tests Strategy 2 (pairwise_audit=True). For 3 agents, there are 3 unique pairs.
    Verifies that 3 isolated API calls are made in parallel, and each thread strictly
    binds only the two participating agents.
    """
    mock_llm_callable.return_value = MOCK_CONFLICT_JSON
    checker = ConflictChecker(llm_callable=mock_llm_callable, pairwise_audit=True, max_threads=5)
    
    result = checker.execute(sample_reports)

    # For 3 agents, combinatorial pairs = 3 * (3 - 1) / 2 = 3 isolated thread calls
    assert mock_llm_callable.call_count == 3
    
    # Verify bilateral role binding: inspect one of the thread prompts
    prompts_sent = [call[0][0] for call in mock_llm_callable.call_args_list]
    
    # Find the prompt specifically testing Security Analyst vs DevOps Engineer
    sec_devops_prompt = next(
        p
        for p in prompts_sent
        if "Security Analyst" in p and "DevOps Engineer" in p
    )
    assert "strictly from this list of responding experts: ['Security Analyst', 'DevOps Engineer']" in sec_devops_prompt
    assert "Data Scientist" not in sec_devops_prompt  # Data Scientist must be isolated out!
    
    # Verify aggregation (3 threads returned 1 conflict each -> 3 total conflicts compiled)
    assert result.has_conflicts is True
    assert len(result.conflicts) == 3
    assert "Multi-threaded pairwise audit completed across 3 pairs" in result.summary


def test_strategy_2_thread_failure_resilience(sample_reports):
    """
    CRITICAL RESILIENCE TEST:
    Simulates a multi-threaded Strategy 2 execution where 1 thread raises an exception
    (e.g., rate limit exceeded) while the other 2 threads succeed.
    Verifies that the pool does NOT crash and successful thread results are preserved.
    """
    call_counter = 0

    def flaky_llm_mock(prompt: str) -> str:
        nonlocal call_counter
        call_counter += 1
        # Make the 2nd thread crash intentionally
        if call_counter == 2:
            raise ValueError("Simulated RateLimitError on Thread 2")
        return MOCK_CONFLICT_JSON

    checker = ConflictChecker(llm_callable=flaky_llm_mock, pairwise_audit=True, max_threads=3)
    
    # The execute call must complete without throwing an unhandled exception
    result = checker.execute(sample_reports)

    # Total 3 pairs attempted
    assert call_counter == 3
    
    # 2 threads succeeded (each returning 1 conflict), 1 thread failed (returning 0)
    assert result.has_conflicts is True
    assert len(result.conflicts) == 2  # Combined results from Thread 1 and Thread 3
    assert "Multi-threaded pairwise audit completed across 3 pairs" in result.summary