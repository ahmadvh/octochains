import os
import uuid
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from octochains import Agent, Aggregator, Engine

# Import our new prompts file
import prompts

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "your-key-here")

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

session_store = {}

# --- AGENTS ---
class Cardiologist(Agent):
    def __init__(self, model="gpt-4o"):
        super().__init__(role="Cardiologist", goal="Identify arrhythmias or structural heart issues.")
        self.llm = ChatOpenAI(temperature=0, model=model)
    def execute(self, medical_report: str) -> str:
        return self.llm.invoke(prompts.CARDIOLOGIST_PROMPT.format(medical_report=medical_report)).content

class Psychologist(Agent):
    def __init__(self, model="gpt-4o"):
        super().__init__(role="Psychologist", goal="Identify mental health issues.")
        self.llm = ChatOpenAI(temperature=0, model=model)
    def execute(self, medical_report: str) -> str:
        return self.llm.invoke(prompts.PSYCHOLOGIST_PROMPT.format(medical_report=medical_report)).content

class Pulmonologist(Agent):
    def __init__(self, model="gpt-4o"):
        super().__init__(role="Pulmonologist", goal="Identify respiratory issues.")
        self.llm = ChatOpenAI(temperature=0, model=model)
    def execute(self, medical_report: str) -> str:
        return self.llm.invoke(prompts.PULMONOLOGIST_PROMPT.format(medical_report=medical_report)).content

class Neurologist(Agent):
    def __init__(self, model="gpt-4o"):
        super().__init__(role="Neurologist", goal="Identify neurological issues.")
        self.llm = ChatOpenAI(temperature=0, model=model)
    def execute(self, medical_report: str) -> str:
        return self.llm.invoke(prompts.NEUROLOGIST_PROMPT.format(medical_report=medical_report)).content

class MultidisciplinaryTeam(Aggregator):
    def __init__(self, model="gpt-4o"):
        super().__init__(role="MultidisciplinaryTeam", goal="Synthesize reports.")
        self.llm = ChatOpenAI(temperature=0, model=model)

    def synthesize(self, problem_data: str, agent_reports: dict) -> str:
        prompt = prompts.AGGREGATOR_PROMPT.format(
            cardio=agent_reports.get('Cardiologist', 'N/A'),
            psych=agent_reports.get('Psychologist', 'N/A'),
            pulmo=agent_reports.get('Pulmonologist', 'N/A'),
            neuro=agent_reports.get('Neurologist', 'N/A')
        )
        return self.llm.invoke(prompt).content

# --- ENDPOINTS ---
@app.post("/analyze")
async def analyze_report(file: UploadFile = File(...)):
    content = await file.read()
    patient_data = content.decode("utf-8")

    agents = [Cardiologist(), Psychologist(), Pulmonologist(), Neurologist()]
    aggregator = MultidisciplinaryTeam()
    engine = Engine(agents=agents, aggregator=aggregator)
    
    report = engine.run(problem_data=patient_data)
    
    session_id = str(uuid.uuid4())
    traces_text = "\n\n".join([f"--- {getattr(t, 'agent_role', 'Agent')} ---\n{getattr(t, 'output', str(t))}" for t in report.traces])
    
    session_store[session_id] = {
        "original_data": patient_data, "traces": traces_text, "consensus": report.consensus
    }
    return {"session_id": session_id, "consensus": report.consensus, "traces": traces_text}

@app.post("/chat")
async def chat_with_team(session_id: str = Form(...), message: str = Form(...)):
    context = session_store.get(session_id)
    if not context: return JSONResponse({"error": "Session not found"}, status_code=404)
    
    prompt = prompts.CHAT_PROMPT.format(traces=context['traces'], consensus=context['consensus'], message=message)
    response = ChatOpenAI(temperature=0.3, model="gpt-4o").invoke(prompt)
    return {"reply": response.content}