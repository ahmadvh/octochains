# Octochains

[![GOSIM Spotlight 2026](https://img.shields.io/badge/GOSIM_2026-Top_10_Featured_Project-blueviolet)](https://gosim.org) 
[![License: BSL 1.1](https://img.shields.io/badge/License-BSL_1.1-orange.svg)](LICENSE.md)
[![Version](https://img.shields.io/badge/version-0.1.0-blue)](https://pypi.org/project/octochains/)

<p align="center">
  <img src="https://github.com/user-attachments/assets/93aecdbf-10af-4f32-9cf3-18a0547d494a" alt="Octochains Logo" width="30%" style="max-width:200px; min-width:150px;"/>
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

<div align="center">
  <img width="800px" height="410px" alt="octochains-architecture"  src="https://github.com/user-attachments/assets/74cb3609-4852-4d64-9c17-f4f3094674c7" />

</div>

---

### Quickstart

Octochains is designed to be developer-first and model-agnostic.

### 1. Install
```bash
pip install octochains
```

### 2. Define an Agent
```python
from octochains import Agent, tool

class Specialist(Agent):
    def __init__(self):
        super().__init__(
            role="Legal Expert", 
            goal="Identify liability risks"
        )

    @tool
    def check_compliance(self, text: str):
        """
        Analyzes text for regulatory non-compliance.
        """
        # Framework automatically generates JSON schema for this tool
        return "Compliant"

    def execute(self, data: str) -> str:
        # Use any LLM here (OpenAI, Gemini, Ollama, etc.)
        # The 'data' passed here is the full complex problem.
        return f"Legal Analysis: {data}"
```
### 3. Define an Aggregator
```python
from octochains import Aggregator

class ChiefConsensusOfficer(Aggregator):
    def __init__(self):
        super().__init__(
            role="Chief Aggregator",
            goal="Synthesize expert opinions into a final verdict"
        )

    def execute(self, agent_reports: dict[str, str]) -> str:
        """
        Receives the a dictionary of reports.
        Key: Agent Role, Value: Agent output string.
        """
        # Here you can call a high-reasoning LLM to compare the reports
        # or implement custom logic to resolve conflicts.
        verdict = "APPROVED"
        for role, report in agent_reports.items():
            if "RISK" in report.upper():
                verdict = "REJECTED"
        
        return f"Final Decision: {verdict} based on {len(agent_reports)} expert inputs."
```

### 4. Run the Parallel Engine
```python
from octochains import Engine

# Initialize your experts and the aggregator
engine = Engine(
    agents=[legal_expert, finance_expert, tech_expert], 
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
