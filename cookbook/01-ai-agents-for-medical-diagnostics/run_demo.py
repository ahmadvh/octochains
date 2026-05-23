"""
=============================================================================
Octochains Demo: Multidisciplinary Medical Diagnostics
=============================================================================
This example demonstrates the core philosophy of the Octochains framework: 
Parallel Isolated Reasoning. 

Instead of relying on a single monolithic prompt or a sequential chain of 
agents (which can lead to logical contamination or "groupthink"), Octochains 
utilizes a MapReduce-inspired architecture for multi-agent reasoning. 

How it works:
1. MAP (The Specialists): The Engine broadcasts the medical report to multiple 
   specialized agents simultaneously. Each agent runs in a private, isolated 
   thread, preventing them from being biased by the others.
2. REDUCE (The Aggregator): An official Synthesizer collects the independent 
   reports and builds a unified, comprehensive final consensus.

Zero-Dependency & Bring-Your-Own-LLM:
Notice that Octochains only requires a standard Python callable for the LLM.
=============================================================================
"""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from octochains import Agent, Engine
from octochains.aggregators import Synthesizer # official octochains aggregator
import datetime


# ---------------------------------------------------------
# SETUP: API Key & The Universal LLM Callable
# ---------------------------------------------------------

# 1. Load your API Key securely from the environment
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "your-key-here")

def openai_llm_callable(prompt: str) -> str:
    """
    A standard, model-agnostic callable to pass into the agents and aggregators.
    Octochains doesn't force you into a specific LLM wrapper. You define how 
    the text is generated, and the framework handles the orchestration.
    """
    llm = ChatOpenAI(temperature=0, model="gpt-4o")
    return llm.invoke(prompt).content


# ---------------------------------------------------------
# STEP 1: THE SPECIALISTS (Parallel Agents)
# ---------------------------------------------------------
# Each agent inherits from the base `Agent` class. They are given a strict 
# role and goal. During execution, they are completely unaware of their peers.

class Cardiologist(Agent):
    def __init__(self):
        super().__init__(
            role="Cardiologist",
            goal="Identify subtle signs of arrhythmias or structural heart issues.",
            input_description="medical report of a patient",
            llm_callable=openai_llm_callable
        )

    def execute(self, medical_report: str) -> str:
        # The base Agent handles the isolation. You just provide the domain-specific logic.
        prompt = f"""
        Act like a cardiologist. Your goal is: {self.goal}
        You will receive a {self.input_description}.
        Task: Review the patient's cardiac workup, including ECG, blood tests, Holter monitor results, and echocardiogram.
        Focus: Determine if there are any subtle signs of cardiac issues that could explain the patient’s symptoms. Rule out any underlying heart conditions.
        Recommendation: Provide guidance on any further cardiac testing or monitoring needed.
        Please only return the possible causes of the patient's symptoms and the recommended next steps.
        
        Medical Report: {medical_report}
        """
        return self.llm_callable(prompt)

class Psychologist(Agent):
    def __init__(self):
        super().__init__(
            role="Psychologist",
            goal="Identify mental health issues such as anxiety, depression, or trauma.",
            input_description="medical report of a patient",
            llm_callable=openai_llm_callable
        )

    def execute(self, medical_report: str) -> str:
        prompt = f"""
        Act like a psychologist. You will receive a {self.input_description}.
        Task: Review the patient's report and provide a psychological assessment.
        Focus: Identify any potential mental health issues that may be affecting the patient's well-being.
        Recommendation: Offer guidance on how to address these concerns, including therapy or counseling.
        Please only return the possible mental health issues and the recommended next steps.
        
        Patient's Report: {medical_report}
        """
        return self.llm_callable(prompt)

class Pulmonologist(Agent):
    def __init__(self):
        super().__init__(
            role="Pulmonologist",
            goal="Identify respiratory issues such as asthma, COPD, or lung infections.",
            input_description="medical report of a patient",
            llm_callable=openai_llm_callable
        )

    def execute(self, medical_report: str) -> str:
        prompt = f"""
        Act like a pulmonologist. You will receive a {self.input_description}.
        Task: Review the patient's report and provide a pulmonary assessment.
        Focus: Identify any potential respiratory issues affecting the patient's breathing.
        Recommendation: Offer guidance on pulmonary function tests or imaging studies.
        Please only return the possible respiratory issues and the recommended next steps.
        
        Patient's Report: {medical_report}
        """
        return self.llm_callable(prompt)

# ---------------------------------------------------------
# STEP 2: THE ENGINE RUN (Orchestration)
# ---------------------------------------------------------

if __name__ == "__main__":
    # 1. Load the data to be analyzed
    # Note: Replace this path with your actual local path if running outside the demo folder
    file_path = "cookbook/01-ai-agents-for-medical-diagnostics/medical_reports/Medical Report - David Wilson - Alzheimer’s Disease.txt"
    with open(file_path, "r") as f:
        patient_data = f.read()

    # 2. Initialize the isolated agents
    cardio = Cardiologist()
    psych = Psychologist()
    pulmo = Pulmonologist()
    
    # 3. Initialize the Aggregator (The "Reduce" step)
    # Using the official Synthesizer saves us from writing complex merging prompts.
    # We supply a custom goal to format the final output exactly how we want it.
    team_lead = Synthesizer(
        llm_callable=openai_llm_callable,
        custom_goal="Synthesize the reports into a list of exactly 3 possible health issues. For each issue, provide the reasoning based on the merged perspectives."
    )

    # 4. Construct the Orchestrator Engine
    engine = Engine(agents=[cardio, psych, pulmo], aggregator=team_lead)

    print("🩺 Octochains: Running Multidisciplinary Diagnostic...")
    
    # 5. Execute! 
    # This broadcasts the patient data to all 3 specialists simultaneously.
    # `show_log=True` will print the individual agent execution times to the console.
    report = engine.run(patient_data, show_log=True)
    
    # 6. Handle the structured output
    # Since our Synthesizer returns a SynthesisResult object, we access 
    # the 'narrative' attribute to get the final text.
    consensus_data = report.consensus
    
    print("\n" + "="*80)
    print("🩺 FINAL MULTIDISCIPLINARY DIAGNOSTIC REPORT")
    print("="*80)
    
    if hasattr(consensus_data, 'narrative'):
        # Console Display
        print(f"\n[EXECUTIVE SUMMARY]\n{consensus_data.narrative}")
        print(f"\n[KEY CLINICAL TAKEAWAYS]")
        for i, takeaway in enumerate(consensus_data.key_takeaways, 1):
            print(f"{i}. {takeaway}")
            
        print(f"\n[REPORT METADATA]")
        print(f"Confidence Score: {consensus_data.confidence:.0%}")
        
        # 7. Save to a formatted Markdown file
        os.makedirs("cookbook/01-ai-agents-for-medical-diagnostics/results", exist_ok=True)
        report_path = "cookbook/01-ai-agents-for-medical-diagnostics/results/Diagnostic_Report.md"
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("# Multidisciplinary Diagnostic Report\n\n")
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"**Date:** {timestamp}")
            f.write(f"**Date:** {timestamp}\n\n")
            f.write("## Executive Summary\n")
            f.write(f"{consensus_data.narrative}\n\n")
            f.write("## Key Clinical Takeaways\n")
            for t in consensus_data.key_takeaways:
                f.write(f"- {t}\n")
            f.write("\n## Citations\n")
            for role, snippet in consensus_data.citations.items():
                f.write(f"- **{role}:** *{snippet}*\n")
            f.write(f"\n---\n*Synthesis Confidence: {consensus_data.confidence:.0%}*")
            
        print(f"\n✅ Professional report successfully generated: {report_path}")
    else:
        print(consensus_data)

    
   