#  Medical Diagnostics Web App Demo

This web application demonstrates the **Octochains** framework's capability to coordinate a multidisciplinary medical team through parallel AI reasoning. By simulating isolated specialists—including a **Cardiologist**, **Psychologist**, and **Pulmonologist**—the system evaluates complex reports independently to prevent "groupthink" and bias.

## Setup and Installation

### 1. Environment Configuration
Ensure you have a `.env` file in the root of the `01-ai-agents-for-medical-diagnostics` folder containing your necessary API credentials (e.g., `OPENAI_API_KEY`).

### 2. Install Dependencies
Install all required packages for this specific demo:
```bash
pip install -r demo-examples\01-ai-agents-for-medical-diagnostics\requirements.txt
```

### 3. Run the Application
Navigate to the `Webapp` directory where the backend logic (`main.py`) is located and start the server using Uvicorn:
```bash
cd Webapp
uvicorn main:app --reload
```

### 4. Access the Interface
**Then**, open your web browser and navigate to:
 **`http://127.0.0.1:8000`**

---

## Project Structure
Based on the `01-ai-agents-for-medical-diagnostics` directory:

- `medical_reports/`: Contains sample medical reports for testing.
- `Webapp/`: The core web application directory.
    - `static/`: Frontend assets (CSS, JS, logos).
    - `main.py`: FastAPI backend entry point.
    - `prompts.py`: Specialist agent prompt definitions.
- `.env`: Environment variables (API keys).
- `requirements.txt`: Python dependencies.
- `run_demo.py`: Alternative entry point for the demo.

> [!CAUTION]
> **Disclaimer:** This project is for research and educational purposes only and is not intended for clinical use.

