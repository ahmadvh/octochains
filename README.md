# Octochains

[![GOSIM Spotlight 2026](https://img.shields.io/badge/GOSIM_2026-Top_10_Featured_Project-blueviolet)](https://gosim.org) 
[![License: BSL 1.1](https://img.shields.io/badge/License-BSL_1.1-orange.svg)](LICENSE.md)
[![Version](https://img.shields.io/badge/version-0.4.0-blue)](https://pypi.org/project/octochains/)

<p align="center">
  <img src="https://github.com/user-attachments/assets/93aecdbf-10af-4f32-9cf3-18a0547d494a" alt="Octochains Logo" width="40%" style="max-width:260px; min-width:150px;"/>
</p>

**Octochains** is a lightweight, zero-dependency Python framework for **Collaborative AI Reasoning**.It is purpose-built for **Decomposable Tasks**, complex problems that require independent, multi-perspective analysis.

By shifting from monolithic responses to **Parallel Isolated Reasoning**, Octochains ensures that every angle of a decision, from clinical diagnostics to financial risk, is evaluated in threaded isolation, preventing logical contamination and "Expert Blindspots."

## Scientifically Validated Performance
Octochains is built on the architectural principles validated in the 2026 study **["Towards a Science of Scaling Agent Systems"](https://research.google/blog/towards-a-science-of-scaling-agent-systems-when-and-why-agent-systems-work/)** (Google Research / MIT).

Research confirms that for analytical, decomposable tasks, a **Parallel Isolated** architecture (the core of Octochains) delivers a massive performance delta over standard sequential or single-agent models:

| Benchmark | Task Domain | Performance Gain vs. Single-Agent |
| :--- | :--- | :--- |
| **Finance-Agent (FAB)** | **Decomposable Financial Reasoning** | **+80.8% 🚀** |
| **Workbench** | **Structured Business Planning** | **+57.2%** |
| **PlanCraft** | **Sequential Automation** | *(Use Single-Agent Instead)* |

## Why Octochains?

Standard AI chains suffer from **"Cognitive Tunnel Vision"**, where a model commits to a logical path too early. Octochains eliminates this via:

* **Parallel Isolation:** Expert nodes operate in private threads with zero awareness of peers, preventing "logical contamination."
* **Centralized Verification:** A specialized "Chief Justice" aggregator synthesizes reports, identifying conflicts and evidence gaps before delivering a verdict.
* **Audit-First Design:** Every decision generates a 100% traceable log of expert rationale, meeting **EU AI Act** requirements for monitorable AI.


## Octochains Anathomy 

https://github.com/user-attachments/assets/ede601fd-0a08-451f-b783-67d854767bb8

---

### Quickstart

Octochains is designed to be developer-first and model-agnostic.

### 1. Install
```bash
pip install octochains
```

### 2. Bring Your Own LLM (Zero-Dependency)
Octochains is a "Pure Engine." It does not force you to install heavy SDKs or learn proprietary API wrappers. You maintain 100% control over your models.

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
### 3. Define Agent
Agents inherit from `Agent` and implement an `execute()` method. The framework builds the strict "Forced Perspective" constraint prompt for you, but you own the API call.
```python
from octochains.base import Agent

class TechAnalyst(Agent):
    def __init__(self):
        super().__init__(
            role="Chief Technology Officer", 
            goal="Evaluate technical feasibility."
        )

    def execute(self, problem_data: str) -> str:
        # 1. Framework generates a strict, isolated identity prompt
        system_prompt = self._build_prompt(problem_data)

        # 2. You control the API execution! 
        full_prompt = f"{system_prompt}\n\nPlease provide your expert analysis."
        return my_llm(full_prompt)
```
💡 **Using Tools?** You own the `execute()` loop, You can bypass the `my_llm` wrapper here and inject your provider's native tool schema (e.g., OpenAI's tools=[...] array) directly into a native API call!

### 4. Define an Aggregator
The Aggregator waits for all experts to finish, reads their parallel reports, and makes the final executive decision.
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
        """
        Receives a dictionary of reports.
        Key: Agent Role, Value: Agent output string.
        Can return a string, or natively return a structured JSON/Pydantic object!
        """
        # Helper method cleanly formats the raw dictionary
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
```python
from octochains.engine import Engine

# 1. Initialize your workforce
tech_expert = TechAnalyst()
# finance_expert = FinanceSpecialist()
# legal_expert = LegalExpert()

engine = Engine(
    agents=[tech_expert], # Add as many parallel agents as you need
    aggregator=ChiefConsensusOfficer()
)

# 2. Broadcast the complex problem to all agents at once
report = engine.run(
    problem_data="Full Project Alpha Investment Case File...",
    show_log=True  # Enables the execution tracing UI in your terminal
)

print(f"Consensus:\n{report.consensus}") # Final verdict from the aggregator
print(f"Audit Trail:\n{report.traces}")  # Execution logs for each agent
```

## Official Aggregators
While Octochains allows you to build custom aggregators (as shown in the Quickstart), we provide official, domain-agnostic aggregators designed for enterprise-grade reasoning. We are actively developing and will be adding more specialized aggregators in future releases.

### 1. `ConflictChecker`
The "Chief Justice" of your architecture. It audits expert reports for logical inconsistencies, timeline mismatches, and incompatible claims. 
* **Strategy 1 (Prompt-Matrix):** Single-call audit using a structured internal matrix.
* **Strategy 2 (Parallel Pairwise):** Multi-threaded execution that performs $\frac{N(N-1)}{2}$ isolated pairwise comparisons—ideal for absolute, reproducible auditability.

```python
from octochains.aggregators import ConflictChecker

boss = ConflictChecker(
    llm_callable=my_llm,
    pairwise_audit=True, # Toggle to True for parallel multi-threaded execution 
    show_log=True        # Visualize the audit TUI in your terminal
)
```
### 2. `Synthesizer`
The "Chief Integration Officer." It merges multiple isolated expert reports into a single, cohesive executive narrative, automatically resolving redundancies and identifying critical takeaways.
```python
from octochains.aggregators import Synthesizer

writer = Synthesizer(
    llm_callable=my_llm,
    show_log=True
)

```

Check out the `/cookbook/` directory for full examples of these aggregators in action.

## Architecture & Strategy
Octochains is designed for high-stakes environments where "vibe-based" AI isn't enough. It excels in **Medical Diagnostics**, **Legal Audits**, and **Strategic Business and Financial Analysis**.

## Repository Structure
* `/src/octochains/engine.py`: The high-performance parallel execution engine.
* `/src/octochains/agents/`: A growing library of specialized experts (Finance, Legal, Medical and etc.).
* `/src/octochains/aggregators/`: Standardized synthesis logic (Majority Vote, Weighted Consensus, etc.).

## Future Roadmap
We are expanding Octochains from a library into a comprehensive ecosystem for high-stakes reasoning:

* Community-driven marketplace for pre-tuned specialists Agents.
* Expanding beyond the native ConflictChecker and Synthesizer modules to support out-of-the-box integration of domain-agnostic consensus logic, including democratic Majority Vote streams, strict Minimax Agent boundary-testing gates, and categorical Classifiers.
* **Octonodes**: Launching a production-grade, drag-and-drop web application interface allowing developers and enterprise architects to visually design parallel topologies—connecting input data hooks, clustering isolated expert agent pools, assigning backend hardware models, and chaining modular aggregator gates with automated Python/Rust code export.
* **HITL Gateways**: Native intercept protocols allowing human domain experts to step in at critical decision forks or review aggregated conflict logs before final execution.

## License
Octochains is **Fair-code**, distributed under the **Business Source License 1.1**.

* **Individuals & Internal Use:** Free to use for personal projects, research, and internal business workflows.
* **Commercial Providers:** You **cannot** offer Octochains as a managed SaaS or sell a commercial wrapper of the engine without a license.
* **The Guarantee:** On **May 10, 2030**, this version automatically becomes **Apache 2.0 (Open Source)**.

**To access the Enterprise Reasoning Features, contact:** [ahmad.vh7@gmail.com](mailto:ahmad.vh7@gmail.com)
<img referrerpolicy="no-referrer-when-downgrade" src="https://static.scarf.sh/a.png?x-pxid=e5ca0204-186e-4871-b23b-249181c25fd2" />
