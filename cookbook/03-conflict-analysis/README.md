# Demo 03: Executive Conflict Analysis

This demo showcases how Octochains applies Parallel Isolated Reasoning to high-stakes enterprise decision-making, specifically Mergers and Acquisitions (M&A) due diligence. It serves as a masterclass in combining domain-isolated agents with advanced reasoning aggregators.

## The Business Problem: "Deal Fever"

In enterprise environments, cross-functional teams often fall victim to "Cognitive Tunnel Vision" or "Deal Fever."

- Sales teams see immediate revenue potential and aggressive growth targets.
- Financial teams look at top-line metrics while worrying about immediate cash runway.
- Engineering teams inherit unscalable, bleeding-edge architectures after the deal is already signed.

When traditional AI systems analyze an M&A dossier, they group these conflicting perspectives together in a single prompt context. This causes the model to generate a generalized, compromised "average summary"—completely burying the critical structural risks.

---

# The Octochains Solution

Octochains solves this by strictly isolating the analytical processes to prevent logical contamination before aggregating the findings through a rigorous truth-gate.

In this demo, we analyze a target startup ("AuraMatch AI") using three specialized agents:

- **CFOAgent:** Audits the burn rate, cash runway, and valuation.
- **CTOAgent:** Audits the infrastructure overhead, refactoring timelines, and technical debt.
- **CROAgent:** Audits the sales integration and enterprise cross-selling timeline.

---

# Technical Architecture

## Phase 1: Parallel Domain Isolation

The Framework Engine forces all three agents to evaluate the raw target document simultaneously, in complete isolation.

Crucially, each agent translates its reasoning into a strictly typed, deterministic Dataclass schema (e.g., `TechDueDiligence`). This guarantees that top-line sales figures cannot subtly warp or soften the technical or financial realities.

---

## Phase 2: The Conflict Checker (Aggregator Layer)

Instead of using a standard summarizer, this demo deploys the `ConflictChecker`—a core, domain-agnostic Octochains aggregator designed to audit isolated expert reports for logical contradictions or incompatible claims.

To overcome the reasoning limitations of standard models, Phase 2 swaps out standard LLMs for GPT-5.5 utilizing advanced internal thinking capabilities and provides two highly deterministic execution strategies:

```python
# Toggle absolute precision vs. single-call cost-efficiency
boss = ConflictChecker(
    llm_callable=call_gpt_5_5_aggregator,
    pairwise_audit=True,  # Activates Strategy 1 (Multi-threaded)
    max_threads=3
)
```
# Audit Strategies

## Strategy 1: Parallel Multi-Threaded Pairwise (`pairwise_audit=True`)

* **How it works:** Programmatically calculates all unique agent combinations $N(N-1) / 2$ and fires simultaneous, isolated API calls to the reasoning model using a Python `ThreadPoolExecutor`.
* **The Advantage:** Ironclad determinism. By constraining the model's focus to strictly two perspectives at a time (e.g., CFO vs. CTO), it eliminates the reasoning variance and token drift common in large context windows.

## Strategy 2: Dynamic Prompt-Matrix (`pairwise_audit=False`)

* **How it works:** Consolidates all data into a single, highly structured API call. It programmatically builds a step-by-step evaluation timeline directly inside the prompt layer, forcing the reasoning model to run its own matrix evaluation sequentially.
* **The Advantage:** Highly cost-efficient (1 API call) and uniquely capable of catching Holistic Conflicts (where a combination of claims from Agent A and Agent B indirectly invalidates Agent C).

---

## Critical Realities Caught by this Demo

By combining Isolated Parallel Reasoning with the `ConflictChecker`, Octochains successfully surfaces two fatal structural flaws that standard AI summarizers pass over:

* **The Cash/Refactor Mismatch (Critical):** The `CTOAgent` reports a required 6–12 month infrastructure refactor due to unscalable cloud-based GPU clusters. The `CFOAgent` reports that the target company only has 3 months of cash runway left at a \$400k/month burn rate. Octochains flags that the target will go bankrupt mid-remediation.
* **The Sales/Integration Illusion (Moderate):** The `CROAgent` projects massive revenue scaling to 50 Fortune 500 clients by Q3 (3 months away). The framework flags that you cannot scale a broken, un-refactored architecture to enterprise clients on a 3-month timeline if it takes the CTO 12 months to stabilize the core.

---

## Running the Demo

Ensure your environment variables are configured with your OpenAI API Key:

```bash
export OPENAI_API_KEY="your-api-key-here"
```

Ensure you have installed the official OpenAI Python SDK (Octochains uses the official SDK for advanced reasoning endpoints)

```bash
pip install openai python-dotenv
```

Navigate to the conflict analysis directory and execute the demo:

```bash
python run_demo.py
```