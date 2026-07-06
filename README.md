# Octochains

[![GOSIM Spotlight 2026](https://img.shields.io/badge/GOSIM_2026-Top_10_Featured_Project-blueviolet)](https://gosim.org) 
[![License: BSL 1.1](https://img.shields.io/badge/License-BSL_1.1-orange.svg)](LICENSE.md)
[![Version](https://img.shields.io/badge/version-0.4.1-blue)](https://pypi.org/project/octochains/)

<p align="center">
  <img src="https://github.com/user-attachments/assets/93aecdbf-10af-4f32-9cf3-18a0547d494a" alt="Octochains Logo" width="40%" style="max-width:260px; min-width:150px;"/>
</p>

**Octochains** is a zero-dependency Python framework for **fault-tolerant, parallel, and isolated multi-agent reasoning and consensus**. It is purpose-built for complex, decomposable tasks that require independent, multi-perspective analysis without logical contamination.

Unlike traditional sequential agent chains where models bias each other through shared chat histories, Octochains executes domain specialists in **Parallel Isolated Threads**. Every angle of a high-stakes decision, from clinical diagnostics to financial risk and legal audits, is evaluated in pristine isolation before being synthesized by a centralized verification layer.

## Why Octochains?

Standard multi-agent frameworks suffer from **Cognitive Tunnel Vision** and **Groupthink**, where early outputs dictate downstream reasoning. Octochains eliminates this through a robust, thread-safe architecture:

* **Parallel Isolation:** Expert agents operate in private threads with zero awareness of peer outputs, guaranteeing objective, unpolluted analysis.
* **Centralized Consensus:** A specialized aggregator audits isolated reports, resolving logical conflicts and highlighting evidence gaps before delivering a type-safe verdict.
* **Audit-First Design:** Every execution generates an immutable, 100% traceable log of expert rationale and error states, meeting **EU AI Act** requirements for monitorable enterprise AI.

## How Octochains Compares

| Feature | Octochains | Sequential Frameworks (e.g., CrewAI, AutoGen) | Routing Graph Frameworks (e.g., LangGraph) |
| :--- | :--- | :--- | :--- |
| **Execution Model** | **Parallel Isolated Threads** | Sequential / Turn-Based Chat | Directed Acyclic Graphs (DAGs) |
| **Cognitive Bias Protection** | **100% (Zero Peer Awareness)** | Low (Agents read previous chat logs) | Moderate (Depends on node state) |
| **Fault Tolerance** | **Thread-Level Isolation & Recovery** | Global workflow fails on node crash | Complex custom retry logic required |
| **Dependencies** | **Zero (Pure Python Engine)** | Heavy (LangChain, Pydantic, etc.) | Heavy |
| **Primary Use Case** | **High-Stakes Consensus & Auditing** | Conversational Task Automation | Complex Stateful Workflows |

## Scientifically Validated Performance

Octochains is built on the architectural principles validated in the study **["Towards a Science of Scaling Agent Systems"](https://research.google/blog/towards-a-science-of-scaling-agent-systems-when-and-why-agent-systems-work/)** (Google Research / MIT). Research confirms that for analytical, decomposable tasks, a **Parallel Isolated** architecture delivers a massive performance delta over standard sequential models:

| Benchmark | Task Domain | Performance Gain vs. Single-Agent |
| :--- | :--- | :--- |
| **Finance-Agent (FAB)** | **Decomposable Financial Reasoning** | **+80.8% 🚀** |
| **Workbench** | **Structured Business Planning** | **+57.2%** |
| **PlanCraft** | **Sequential Automation** | *(Use Single-Agent Instead)* |

## Architecture & Anatomy

https://github.com/user-attachments/assets/ede601fd-0a08-451f-b783-67d854767bb8

---

## Quickstart

Octochains is designed to be developer-first, model-agnostic, and lightweight.

### 1. Install
```batch
pip install octochains
```
### 2. Bring Your Own LLM (Zero-Dependency)
Octochains is a "Pure Engine." It does not force you to install heavy SDKs or learn proprietary API wrappers. You maintain 100% control over your models and API keys.
```python
import openai

client = openai.Client(api_key="sk-...")

def my_llm(prompt: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content
```
### 3. Define Specialist Agents
Agents inherit from `Agent` and implement an `execute()` method. The framework builds the strict "Forced Perspective" identity prompt for you, while you retain full control over the execution loop.
```python
from octochains.base import Agent

class TechAnalyst(Agent):
    def __init__(self):
        super().__init__(
            role="Chief Technology Officer", 
            goal="Evaluate technical feasibility and database scalability."
        )

    def execute(self, problem_data: str) -> str:
        # 1. Framework generates a strict, isolated identity prompt
        system_prompt = self._build_prompt(problem_data)

        # 2. You control the API execution (or tool injection!) 
        full_prompt = f"{system_prompt}

Please provide your expert analysis."
        return my_llm(full_prompt)
```

💡 **Using Tools?** You own the `execute()` loop! You can bypass the simple text wrapper and inject your provider's native tool schemas (e.g., OpenAI functions or external database hooks) directly into the API call.

### 4. Define an Aggregator
The Aggregator waits for all experts to finish, reads their parallel reports, and synthesizes the final executive decision.

```python
from octochains.base import Aggregator
from typing import Any

class ChiefConsensusOfficer(Aggregator):
    def __init__(self):
        super().__init__(
            role="Chief Aggregator",
            goal="Synthesize expert opinions into a final verdict",
            llm_callable=my_llm
        )

    def execute(self, agent_reports: dict[str, str]) -> Any:
        # Helper method cleanly formats valid reports and injects anti-hallucination guardrails
        compiled_reports = self._format_reports(agent_reports)
        
        prompt = f"""
        Role: {self.role}
        Goal: {self.goal}
        Reports:{compiled_reports}
        FINAL VERDICT:
        """
        return self.llm_callable(prompt)
```

### 5. Run the Parallel Engine
The engine launches all agents concurrently, traps individual thread failures without crashing the pool, and pipes clean data to the aggregator.

```python

from octochains.engine import Engine

# 1. Initialize your workforce
tech_expert = TechAnalyst()
# finance_expert = FinanceSpecialist()
# legal_expert = LegalExpert()

engine = Engine(
    agents=[tech_expert], 
    aggregator=ChiefConsensusOfficer()
)

# 2. Broadcast the problem data to all agents simultaneously
report = engine.run(
    problem_data="Full Project Alpha Investment Case File...",
    show_log=True  # Enables real-time execution tracing in your terminal
)

print(f"Consensus:
{report.consensus}") 
print(f"Audit Trail:
{report.traces}")
```

### Expected Terminal Output

```batch

[ENGINE] Booting Octochains Parallel Reasoning Workflow...
[ENGINE] Provisioned Agents: 1 | Assigned Aggregator: Chief Aggregator
  ├── [Dispatching] Thread launched for Chief Technology Officer...
  └── [Success] Collected structured report from Chief Technology Officer.
[ENGINE] >>> PHASE 2: Aggregated Consensus

Consensus:
Technical feasibility is APPROVED. The architecture supports isolated scaling without bottlenecking database read operations.

Audit Trail:
[Trace(agent_role='Chief Technology Officer', status='success', error_message=None)]
```

## Official Enterprise Aggregators

While Octochains allows you to build custom aggregators, we provide out-of-the-box modules designed for enterprise-grade verification and consensus.

### 1. ConflictChecker
The deterministic "Chief Justice" of your architecture. It audits expert reports for logical contradictions, timeline mismatches, and incompatible claims.

* **Strategy 1 (Prompt-Matrix):** Single-call audit using a structured internal comparative matrix.
* **Strategy 2 (Parallel Pairwise):** Multi-threaded execution that programmatically spawns isolated bilateral threads across all unique agent pairs for absolute, reproducible auditability.
* **Mathematical Safety Gate:** Automatically aborts audits without wasting API tokens if upstream failures reduce surviving reports to fewer than 2.

```python
from octochains.aggregators import ConflictChecker

boss = ConflictChecker(
    llm_callable=my_llm,
    pairwise_audit=True,  # Toggle to True for multi-threaded O(N^2) pairwise isolation
    max_threads=5,
    show_log=True
)
```
### 2. Synthesizer
The "Chief Integration Officer." It merges multiple isolated expert reports into a single cohesive executive narrative, automatically resolving redundancies, mapping citations strictly to responding agents, and zeroing out confidence scores if upstream pipelines fail.
```python
from octochains.aggregators import Synthesizer

writer = Synthesizer(
    llm_callable=my_llm,
    show_log=True
)
```
Check out the `/cookbook/` directory for full examples of these aggregators in action.

## Repository Structure

* `/src/octochains/engine.py`: High-performance parallel orchestrator with thread-level exception trapping.
* `/src/octochains/base.py`: Superior abstract base classes with automated threshold gates and anti-hallucination prompt injection.
* `/src/octochains/agents/`: Specialized domain expert templates (Finance, Legal, Medical).
* `/src/octochains/aggregators/`: Standardized synthesis and deterministic auditing logic.

## Future Roadmap

We are actively expanding Octochains from a library into a comprehensive ecosystem for high-stakes reasoning:

* **Community Marketplace:** Pre-tuned, specialized agent prompts and domain-specific validation rules.
* **Expanded Aggregator Suite:** Out-of-the-box integration for democratic Majority Vote streams, strict Minimax boundary-testing gates, and categorical Classifiers.
* **Octonodes:** A production-grade visual application interface allowing architects to drag-and-drop parallel topologies, map data hooks, and export automated Python/Rust deployment code.
* **HITL Gateways:** Native Human-in-the-Loop intercept protocols allowing domain experts to step in at critical decision forks or review aggregated conflict logs before execution.

## License

Octochains is **Fair-Code**, distributed under the **Business Source License 1.1**.

* **Individuals & Internal Use:** Free to use, modify, and scale for personal projects, academic research, and internal company workflows.
* **Commercial Providers:** You **cannot** offer Octochains as a managed SaaS reasoning infrastructure or sell a commercial wrapper of the core engine without an enterprise license.
* **The Open-Source Guarantee:** To protect the codebase as a permanent public good, this version contains a deterministic sunset clause: on **May 10, 2030**, the license automatically transitions to **Apache 2.0 (Open Source)**.

**To access Enterprise Reasoning Features or commercial licensing, contact:** [ahmad.vh7@gmail.com](mailto:ahmad.vh7@gmail.com)

<img referrerpolicy="no-referrer-when-downgrade" src="https://static.scarf.sh/a.png?x-pxid=e5ca0204-186e-4871-b23b-249181c25fd2" />
