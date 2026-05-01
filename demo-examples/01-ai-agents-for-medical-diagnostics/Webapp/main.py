import os
import uuid
import json
import asyncio
from fastapi.responses import StreamingResponse, PlainTextResponse
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from octochains import Agent, Aggregator, Engine
import datetime



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
    
    session_id = str(uuid.uuid4())

    async def generate_stream():
        agents = [Cardiologist(), Psychologist(), Pulmonologist(), Neurologist()]
        
        # Helper to run synchronous LLM calls in a background thread
        async def run_agent(agent):
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, agent.execute, patient_data)
            return agent.role, result

        # Start all agents concurrently
        tasks = [asyncio.create_task(run_agent(a)) for a in agents]
        agent_reports = {}
        
        # Yield results AS THEY FINISH
        for coro in asyncio.as_completed(tasks):
            role, res = await coro
            agent_reports[role] = res
            # Stream the individual completion to the frontend
            yield json.dumps({"type": "agent_done", "role": role, "result": res}) + "\n"
        
        # Once all agents are done, run the aggregator
        aggregator = MultidisciplinaryTeam()
        loop = asyncio.get_event_loop()
        consensus = await loop.run_in_executor(None, aggregator.synthesize, patient_data, agent_reports)
        
        # Save session context
        traces_text = "\n\n".join([f"--- {role} ---\n{res}" for role, res in agent_reports.items()])
        session_store[session_id] = {
            "original_data": patient_data, "traces": traces_text, "consensus": consensus
        }
        
        # Stream the final result
        yield json.dumps({"type": "consensus", "session_id": session_id, "consensus": consensus}) + "\n"

    # Return as a stream
    return StreamingResponse(generate_stream(), media_type="application/x-ndjson")

@app.get("/download_log/{session_id}")
async def download_log(session_id: str):
    context = session_store.get(session_id)
    if not context:
        return JSONResponse({"error": "Session not found"}, status_code=404)
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Format a comprehensive, compliance-ready log file
    log_content = (
        "=================================================\n"
        " OCTOCHAINS AI - EU AI ACT COMPLIANCE TRACE LOG \n"
        "=================================================\n"
        f"Session ID: {session_id}\n"
        f"Timestamp: {timestamp}\n"
        "Model Environment: Parallel Multi-Agent (LLM)\n"
        "Status: COMPLETED\n\n"
        "--- ORIGINAL INPUT DATA ---\n"
        f"{context.get('original_data', 'N/A')}\n\n"
        "=================================================\n"
        " MULTIDISCIPLINARY AGENT TRACES \n"
        "=================================================\n"
        f"{context.get('traces', 'N/A')}\n\n"
        "=================================================\n"
        " FINAL CONSENSUS REPORT \n"
        "=================================================\n"
        f"{context.get('consensus', 'N/A')}\n"
        "=================================================\n"
        "End of Trace Log."
    )
    
    # The Content-Disposition header forces the browser to download it as a .txt file
    headers = {
        "Content-Disposition": f"attachment; filename=octochains_trace_{session_id}.txt"
    }
    
    return PlainTextResponse(content=log_content, headers=headers)
@app.post("/chat")
async def chat_with_team(session_id: str = Form(...), message: str = Form(...)):
    context = session_store.get(session_id)
    if not context: return JSONResponse({"error": "Session not found"}, status_code=404)
    
    prompt = prompts.CHAT_PROMPT.format(traces=context['traces'], consensus=context['consensus'], message=message)
    response = ChatOpenAI(temperature=0.3, model="gpt-4o").invoke(prompt)
    return {"reply": response.content}