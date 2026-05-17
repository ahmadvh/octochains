# Octochains

[![GOSIM Spotlight 2026](https://img.shields.io/badge/GOSIM_2026-Top_10_Featured_Project-blueviolet)](https://gosim.org) 
[![License: BSL 1.1](https://img.shields.io/badge/License-BSL_1.1-orange.svg)](LICENSE.md)
[![Version](https://img.shields.io/badge/version-0.2.0-blue)](https://pypi.org/project/octochains/)

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
Octochains requires an `LLMCallable`: a standard Python function that takes a `prompt: str` and returns an output (string, dictionary, or object).

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
```python
from octochains import Agent, tool

class Specialist(Agent):
    def __init__(self):
        super().__init__(
            role="Legal Expert", 
            goal="Identify liability risks",
            input_description="A business proposal document.",
            llm_callable=my_llm
        )

    @tool
    def check_compliance(self, text: str):
        """
        Analyzes text for regulatory non-compliance.
        """
        # Framework automatically generates JSON schema for this tool
        return "Compliant"

    def execute(self, data: str) -> str:
        # Base class automatically handles the double-blind isolation prompt
        # and dynamically injects your @tool schemas!
        prompt = self._build_prompt(data)
        return self.llm_callable(prompt)
```

### 4. Define an Aggregator
```python
from octochains import Aggregator
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
from octochains import Engine

# Initialize your experts and the aggregator
legal_expert = Specialist()
# finance_expert = FinanceSpecialist()
# tech_expert = TechSpecialist()

engine = Engine(
    agents=[legal_expert], # Add as many agents as you need
    aggregator=ChiefConsensusOfficer()
)

# Broadcast the complex problem to all agents at once
report = engine.run("Full Project Alpha Investment Case File...")

print(f"Consensus: {report.consensus}")
print(f"Audit Trail: {report.traces}")
```

## Architecture & Strategy
Octochains is designed for high-stakes environments where "vibe-based" AI isn't enough. It excels in **Medical Diagnostics**, **Legal Audits**, and **Strategic Business and Financial Analysis**.

## Repository Structure
* `/src/octochains/engine.py`: The high-performance parallel execution engine.
* `/src/octochains/agents/`: A growing library of specialized experts (Finance, Legal, Medical and etc.).
* `/src/octochains/aggregators/`: Standardized synthesis logic (Majority Vote, Weighted Consensus, etc.).

## Future Roadmap
We are expanding Octochains from a library into a comprehensive ecosystem for high-stakes reasoning:

* Community-driven marketplace for pre-tuned specialists Agents.

## License
Octochains is **Fair-code**, distributed under the **Business Source License 1.1**.

* **Individuals & Internal Use:** Free to use for personal projects, research, and internal business workflows.
* **Commercial Providers:** You **cannot** offer Octochains as a managed SaaS or sell a commercial wrapper of the engine without a license.
* **The Guarantee:** On **May 10, 2030**, this version automatically becomes **Apache 2.0 (Open Source)**.

**To access the Enterprise Reasoning Features, contact:** [ahmad.vh7@gmail.com](mailto:ahmad.vh7@gmail.com)
