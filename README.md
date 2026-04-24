# Octochains

!<img width="250" align="right" height="250" alt="octochains" src="https://github.com/user-attachments/assets/e45eb716-8910-438a-a595-1f96e2085ff2" />
[![GOSIM Spotlight 2026](https://img.shields.io/badge/GOSIM_2026-Top_10_Featured_Project-blueviolet)](https://gosim.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-0.1.0-blue)](https://pypi.org/project/octochains/)

**Octochains** is a lightweight, zero-dependency Python framework for **Collaborative AI Reasoning**. It moves away from "monolithic" AI responses toward a parallel, multi-expert architecture that eliminates "Expert Blindspots" in high-stakes decision-making.

---

### The Core Innovation

Even State-of-the-Art models (like GPT-5) can fall into "Reasoning Traps", a form of cognitive tunnel vision where the model commits to a path too early. Octochains eliminates this via a MapReduce-inspired architecture:

1.  **Broadcasting**: The full, complex problem is passed directly to every specialized agent in the pool.
2.  **Parallel Execution**: Agents operate simultaneously in isolated, threaded environments, ensuring they cannot bias each other's initial findings.
3.  **The Aggregator**: A final "Chief Justice" agent synthesizes these conflicting or supporting insights into a single transparent, explainable, and robust outcome.

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
        """Analyzes text for regulatory non-compliance."""
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

    def synthesize(self, problem_data: str, agent_reports: dict[str, str]) -> str:
        """
        Receives the original problem and a dictionary of reports.
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
---
### Featured Use Case: Medical Diagnostics

While Octochains is a universal framework, its power is best demonstrated in multidisciplinary medicine. The featured example simulates a clinical team to rule out underlying heart conditions, psychological factors, or respiratory issues that might be missed by a single-model analysis.

- **Cardiologist Agent**: Focuses on arrhythmias and structural abnormalities.
- **Psychologist Agent**: Identifies conditions like anxiety or panic disorders.
- **Pulmonologist Agent**: Assesses respiratory causes such as asthma or COPD.

⚠️ **Disclaimer**: This project is for research and educational purposes only and is **not intended for clinical use**.

---

### Repository Structure 

**The Agent & Aggregator Hub**
Octochains is built to be modular. We are developing an Agent & Aggregator Hub where the community can contribute, publish, and reuse specialized reasoning modules.
```plaintext
src/octochains/
├── __init__.py           <-- Core framework exports
├── base.py               <-- Abstract Base Classes (Agent/Aggregator)
├── engine.py             <-- Parallel Broadcast Engine
├── schema.py    
├── exceptions.py         <-- Error handling     
│
├── agents/               <-- THE AGENT HUB
│   ├── medical/          
│   │   ├── __init__.py   <-- Export: Cardiologist, Neurologist, etc.
│   │   ├── cardiology.py
│   │   └── neurology.py
│   ├── legal/
│   │   ├── __init__.py   <-- Export: Compliance, ContractExpert
│   │   └── compliance.py
│   └── finance/
│       ├── __init__.py
│       └── analyst.py
│
└── aggregators/          <-- THE AGGREGATOR LIBRARY
    ├── medical/
    │   ├── __init__.py   <-- Export: ChiefMedicalOfficer
    │   └── cmo.py
    └── logic/            <-- Standard decision-making logic
        ├── __init__.py   <-- Export: MajorityVote, WeightedConsensus
        ├── majority.py
        └── consensus.py
```
**Demo Examples**
Every demo in Octochains is designed as a standalone, reproducible case study. This ensures the core framework remains lightweight while allowing specific use cases to have their own environment.
```plaintext
demo-examples/
└── 01-ai-agents-for-medical-diagnostics/
    ├── medical_reports/    <-- Sample patient dossiers
    ├── results/            <-- Historical audit logs of agent outputs
    ├── requirements.txt    <-- Isolated dependencies (e.g., biopython)
    └── run_demo.py         <-- Entry point for the diagnostic engine
```

---

### Future Roadmap
We are expanding Octochains from a library into a comprehensive ecosystem for high-stakes AI reasoning.

- **The Agent Hub:** A community-driven marketplace for pre-tuned specialist modules. Developers can build and publish their own "experts" (e.g., M&A Due Diligence, Cybersecurity Threat Hunter, or Endocrinology Specialist) for others to snap into their own chains.

---
### License & Contact
Octochains is open-source under the MIT license. For enterprise features and custom integrations
contact: ahmad.vh7@gmail.com
