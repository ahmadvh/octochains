# 🩺 Demo 01: AI Agents for Medical Diagnostics

This demo showcases the power of the **Octochains** framework in a high-stakes, multidisciplinary medical scenario. It demonstrates how **collaborative isolated reasoning** can prevent diagnostic "tunnel vision" by having specialized AI agents independently evaluate the same patient dossier before reaching a collective consensus.

<img width="1056" height="443" alt="364576315-b7c87bf6-dfff-42fe-b8d1-9be9e6c7ce86" src="https://github.com/user-attachments/assets/c02eff1e-70dd-4edb-b378-9baa06772276" />


---

## Getting Started

Each demo project in Octochains is designed to be standalone with its own environment needs to keep the core framework lightweight.

### 1. Install Dependencies
Navigate to this demo directory and install the specific requirements into your Python virtual environment:
```bash
pip install -r requirements.txt
```

**Note:** This demo utilizes langchain and langchain-openai for agent logic.

### 2. Configure Environment Variables
This demo uses openai models (like GPT-4o). You must provide an API key to run the simulation.

Create a `.env` file in this directory.

Add your OpenAI API key:
```bash
OPENAI_API_KEY=your_actual_api_key_here
```

---

## System Architecture

### Building the Agents
In this demo, we define three specialized agents by inheriting from the `octochains.Agent` base class. Each agent is given a specific "Role" and "Goal" to simulate a real-world clinical team using **collaborative isolated reasoning**:

* **Cardiologist**: Focuses on cardiac workups, ECG, blood tests, and echocardiograms to identify structural heart issues.
* **Psychologist**: Reviews the report for signs of anxiety, depression, or trauma that might manifest as somatic symptoms.
* **Pulmonologist**: Identifies potential respiratory issues such as asthma, COPD, or lung infections affecting the patient's breathing.

Each agent implements an `execute()` method. When the **Octochains Engine** runs, these methods are triggered simultaneously in parallel threads, ensuring that no agent's findings are biased by the others.

### The Aggregator 
The results from the specialists are passed to the `MultidisciplinaryTeam` aggregator. This component acts as a "Chief Justice," receiving only the collective expert reports to synthesize a final verdict.

## 📥 Input & Output Flow

### System Input
The system takes a raw medical report (text format) as input. By default, the `run_demo.py` script is set to analyze a case file from the `medical_reports/` directory.

### System Output
* **Parallel Execution**: The engine broadcasts the patient data to all three specialists at once using the **Octochains** architecture.
* **Expert Reports**: Each agent generates an independent analysis based on their specific domain expertise.
* **Final Consensus**: The aggregator produces a bulleted list of the 3 most likely health issues along with clinical reasoning for each.
* **Persistence**: The final consensus is printed to the console and saved automatically to `results/Final Report.txt`.

### 🤝 Contributing New Demos
We encourage the community to contribute new standalone case studies to show how **Octochains** can be used in different industries (Legal, Finance, Cybersecurity, etc.).

### Guidelines for New Demos:
* **Isolated Environments**: Every new demo must have its own `requirements.txt` file for its specific dependencies.
* **Entry Point**: Provide a clear `run_demo.py` that demonstrates the full "Broadcast -> Collaborative Isolated Reasoning -> Aggregate" flow.
* **Data**: Include sample data (like the .txt reports in this demo) to make the example reproducible.

> ⚠️ **Disclaimer**: This demo is for research and educational purposes only and is not intended for clinical use. It simulates a reasoning process and should not be used as a substitute for professional medical advice, diagnosis, or treatment.
