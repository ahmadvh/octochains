# 💡 Demo 02: The Micro-SaaS Idea Validator

This demo showcases a **Hybrid AI Architecture** using the **Octochains** framework. It evaluates a short startup idea by combining the speed and cost-efficiency of **local open-source models** (via Ollama) with the advanced reasoning capabilities of **cloud models** (via OpenAI).

By running 4 distinct expert agents in parallel locally, and reserving the expensive API call for the final synthesis, you get a comprehensive venture capital report for fractions of a cent!

### Why This Pattern Matters
Small local models (like 1.5B or 3B parameters) are fast but can hallucinate if given overly complex prompts. By restricting each local model to a single, highly-specific goal (e.g., "Just find the marketing hook") and running them in parallel, we effectively eliminate their blindspots. The larger, smarter cloud model then only has to synthesize structured data, drastically reducing token costs while maintaining high-quality output.

---

## Architecture Overview

### 1. The Local Specialist Agents (Ollama)
We use `llama3.2:3b` (or any small local model) running on a GPU machine to power four specialized perspectives. These run simultaneously using Octochains' parallel engine:
* **Tech Lead**: Assesses technical feasibility and suggests a tech stack.
* **Marketing Guru**: Identifies the target audience and acquisition channels.
* **Cynic / Risk Officer**: Brutally dissects why the idea will fail and finds hidden competitors.
* **Pricing Specialist**: Determines the optimal monetization and pricing tiers.

### 2. The Cloud Aggregator (OpenAI)
* **Venture Capitalist**: Powered by `gpt-4o`. This agent acts as the "Chief Justice." It reads the 4 local expert reports, synthesizes the findings, and makes a final **GO / NO-GO** investment decision.

---

## Getting Started

### 1. Install Dependencies
This demo requires `litellm` to seamlessly route requests between Ollama and OpenAI. Navigate to this directory and install the requirements:
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables
This demo uses high-reasoning models (like GPT-4o). You must provide an API key to run the simulation.

- Create a .env file in this directory.
- Add your OpenAI API key:

```plaintext
    OPENAI_API_KEY=your_actual_api_key_here
```
### 3. Point to Your Local Ollama Instance
By default, run_demo.py is configured to point to the standard local Ollama address (http://localhost:11434).

- If you are running Ollama on a different port or a remote machine, change this in `run_demo.py`:
```python
OLLAMA_API_BASE = "http://localhost:11434"
```
- Make sure you have pulled the model beforehand: ollama run llama3.2:3b

---

### Input
The system is currently configured to evaluate this micro-SaaS idea:

"An app that uses AI to remind you to water your plants based on local weather, humidity in the house, and the specific breed of the plant."

(You can easily change the idea_input variable in the script to test your own ideas!)

### Output & Artifacts
The Octochains engine will broadcast the idea, collect the reports, and generate a final verdict.

To keep things organized, the script automatically generates a `results/` folder containing the individual traces and the final synthesis:
```plaintext
results/
├── tech_lead_report.txt
├── marketing_guru_report.txt
├── cynic__risk_officer_report.txt
├── pricing_specialist_report.txt
└── final_venture_capitalist_verdict.txt
```
---
### 🤝 Contributing New Demos

We encourage the community to contribute new standalone case studies to show how **Octochains** can be used in different industries (Legal, Finance, Cybersecurity, etc.).

### Guidelines for New Demos:
* **Isolated Environments**: Every new demo must have its own `requirements.txt` file for its specific dependencies.
* **Entry Point**: Provide a clear `run_demo.py` that demonstrates the full "Broadcast -> Collaborative Isolated Reasoning -> Aggregate" flow.
* **Data**: Include sample data (like the .txt reports in this demo) to make the example reproducible.