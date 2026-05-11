import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from octochains import Agent, Aggregator, Engine, tool

# 1. Load your API Key
load_dotenv() # Looks for a .env file with OPENAI_API_KEY
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "your-key-here")

# ---------------------------------------------------------
# 1. THE SPECIALISTS (Agents)
# ---------------------------------------------------------

class Cardiologist(Agent):
    def __init__(self, model="gpt-4o"):
        super().__init__(
            role="Cardiologist",
            goal="Identify subtle signs of arrhythmias or structural heart issues.",
            input_description="medical report of a patient"
        )
        self.llm = ChatOpenAI(temperature=0, model=model)

    def execute(self, medical_report: str) -> str:
        prompt = f"""
        Act like a cardiologist. You will receive a {self.input_description}.
        Task: Review the patient's cardiac workup, including ECG, blood tests, Holter monitor results, and echocardiogram.
        Focus: Determine if there are any subtle signs of cardiac issues that could explain the patient’s symptoms. Rule out any underlying heart conditions.
        Recommendation: Provide guidance on any further cardiac testing or monitoring needed.
        Please only return the possible causes of the patient's symptoms and the recommended next steps.
        
        Medical Report: {medical_report}
        """
        response = self.llm.invoke(prompt)
        return response.content

class Psychologist(Agent):
    def __init__(self, model="gpt-4o"):
        super().__init__(
            role="Psychologist",
            goal="Identify mental health issues such as anxiety, depression, or trauma.",
            input_description="medical report of a patient"
        )
        self.llm = ChatOpenAI(temperature=0, model=model)

    def execute(self, medical_report: str) -> str:
        prompt = f"""
        Act like a psychologist. You will receive a {self.input_description}.
        Task: Review the patient's report and provide a psychological assessment.
        Focus: Identify any potential mental health issues that may be affecting the patient's well-being.
        Recommendation: Offer guidance on how to address these concerns, including therapy or counseling.
        Please only return the possible mental health issues and the recommended next steps.
        
        Patient's Report: {medical_report}
        """
        response = self.llm.invoke(prompt)
        return response.content

class Pulmonologist(Agent):
    def __init__(self, model="gpt-4o"):
        super().__init__(
            role="Pulmonologist",
            goal="Identify respiratory issues such as asthma, COPD, or lung infections.",
            input_description="medical report of a patient"
        )
        self.llm = ChatOpenAI(temperature=0, model=model)

    def execute(self, medical_report: str) -> str:
        prompt = f"""
        Act like a pulmonologist. You will receive a {self.input_description}.
        Task: Review the patient's report and provide a pulmonary assessment.
        Focus: Identify any potential respiratory issues affecting the patient's breathing.
        Recommendation: Offer guidance on pulmonary function tests or imaging studies.
        Please only return the possible respiratory issues and the recommended next steps.
        
        Patient's Report: {medical_report}
        """
        response = self.llm.invoke(prompt)
        return response.content

# ---------------------------------------------------------
# 2. THE DECISION MAKER (Aggregator)
# ---------------------------------------------------------

class MultidisciplinaryTeam(Aggregator):
    def __init__(self, model="gpt-5"):
        super().__init__(
            role="MultidisciplinaryTeam",
            goal="Synthesize reports into 3 possible health issues with reasons."
        )
        self.llm = ChatOpenAI(temperature=0, model=model)

    def execute(self, agent_reports: dict) -> str:
        # We extract the specific reports from the dictionary passed by the Engine
        prompt = f"""
        Act like a multidisciplinary team of healthcare professionals.
        You will receive a medical report of a patient visited by a Cardiologist, Psychologist, and Pulmonologist.
        Task: Review the patient's medical report from these specialists, analyze them and come up with a list of 3 possible health issues.
        Just return a list of bullet points of 3 possible health issues and for each issue provide the reason.

        Cardiologist Report: {agent_reports.get('Cardiologist', 'No report available')}
        Psychologist Report: {agent_reports.get('Psychologist', 'No report available')}
        Pulmonologist Report: {agent_reports.get('Pulmonologist', 'No report available')}
        """
        response = self.llm.invoke(prompt)
        return response.content

# ---------------------------------------------------------
# 3. THE ENGINE RUN (Main)
# ---------------------------------------------------------

if __name__ == "__main__":
    # Sample Case from your folder
    with open("demo-examples/01-ai-agents-for-medical-diagnostics/medical_reports/Medical Report - Charles Baker - Prostate Cancer (Suspicion).txt", "r") as f:
        patient_data = f.read()

    # Initialize Agents
    cardio = Cardiologist()
    psych = Psychologist()
    pulmo = Pulmonologist()
    
    # Initialize the Aggregator
    team_lead = MultidisciplinaryTeam()

    # The Orchestrator
    engine = Engine(agents=[cardio, psych, pulmo], aggregator=team_lead)

    print("🩺 Octochains: Running Multidisciplinary Diagnostic...")
    
    # This runs the 3 specialists in parallel!
    report = engine.run(patient_data, show_log = True)

    print("\n" + "="*60)
    print("FINAL CONSENSUS DIAGNOSIS")
    print("="*60)
    print(report.consensus)

    # create the folder 
    os.makedirs("demo-examples/01-ai-agents-for-medical-diagnostics/results", exist_ok=True)

    # store in the Rsults folder
    with open("demo-examples/01-ai-agents-for-medical-diagnostics/results/Final Report.txt", "w") as f:
        f.write(report.consensus)