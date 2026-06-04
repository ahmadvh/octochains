# backend/main.py
import os
import json
import asyncio
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Import directly from the octochains package 
from octochains.base import Agent
from octochains.engine import Engine
from octochains.aggregators import ConflictChecker

from utils.document_parser import parse_pdf_to_sentences
from prompts import FINANCE_PROMPT, LEGAL_PROMPT, OPS_PROMPT, LEASE_DUE_DILIGENCE_GOAL

app = FastAPI(title="Octochains Parallel Reasoning Demo")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- SERVE FRONTEND STATIC FILES ---
base_dir = os.path.dirname(os.path.abspath(__file__))
frontend_dir = os.path.join(base_dir, "..", "frontend")
app.mount("/frontend", StaticFiles(directory=frontend_dir), name="frontend")


current_document_context = []

# Synchronous client wrapper for OpenAI
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- LLM CALLABLES ---

def call_openai_aggregator(prompt: str) -> str:
    """Callable for the Central Aggregator (The Reduce Phase)."""
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "You are the Chief Justice. Analyze the reports and output a structured JSON conflict audit."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.1
    )
    return response.choices[0].message.content

def call_openai_agent(prompt: str) -> str:
    """Callable for the Isolated Specialists (The Map Phase)."""
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[
            {"role": "user", "content": prompt},
        ],
        temperature=0.1
    )
    return response.choices[0].message.content


# --- AGENT WRAPPERS ---
def parse_agent_response(raw_result, agent_name, color):
    if isinstance(raw_result, str):
        try:
            clean_str = raw_result.strip().removeprefix("```json").removesuffix("```").strip()
            parsed_result = json.loads(clean_str)
        except json.JSONDecodeError:
            parsed_result = {"selected_sentence_ids": [], "insight": "Failed to extract structured data."}
    else:
        parsed_result = raw_result

    return {
        "agent": agent_name,
        "color": color,
        "selected_sentence_ids": parsed_result.get("selected_sentence_ids", []),
        "insight": parsed_result.get("insight", "")
    }

class ExpertAgent(Agent):
    """Refactored agent class utilizing the Bring-Your-Own-LLM callable pattern."""
    def __init__(self, role: str, goal: str, color: str, system_prompt: str, llm_callable):
        super().__init__(role=role, goal=goal)
        self.color = color
        self.system_prompt = system_prompt
        self.llm_callable = llm_callable
        
    def execute(self, problem_data: str):
        # Construct the isolated prompt for the specialist
        prompt = f"{self.system_prompt}\n\nAnalyze the following data:\n{problem_data}"
        
        # Execute via the standard callable
        return self.llm_callable(prompt)


# --- API ROUTES ---
@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    global current_document_context
    file_bytes = await file.read()
    
    sentence_objects = parse_pdf_to_sentences(file_bytes)
    current_document_context = sentence_objects
    
    return {"status": "success", "sentences": sentence_objects}


async def run_octochains_stream():
    global current_document_context
    yield f"data: {json.dumps({'status': 'engine_started', 'message': 'Booting thread-isolated experts via OpenAI...'})}\n\n"
    
    # 1. Initialize Agents with the OpenAI callable
    finance = ExpertAgent(
        role="Finance Agent",
        goal="Identify financial risks and liabilities.",
        color="#FFD54D",
        system_prompt=FINANCE_PROMPT,
        llm_callable=call_openai_agent
    )
    legal = ExpertAgent(
        role="Legal Agent",
        goal="Identify legal traps and governance limitations.",
        color="#00BEBE",
        system_prompt=LEGAL_PROMPT,
        llm_callable=call_openai_agent
    )
    ops = ExpertAgent(
        role="Operations Agent",
        goal="Identify operational bottlenecks and maintenance burdens.",
        color="#00A15E",
        system_prompt=OPS_PROMPT,
        llm_callable=call_openai_agent
    )
    
    agents = [finance, legal, ops]
    agent_color_map = {agent.role: agent.color for agent in agents}
    
    # 2. Instantiate the Native Aggregator
    boss = ConflictChecker(
        llm_callable=call_openai_aggregator, 
        pairwise_audit=True,
        custom_goal=LEASE_DUE_DILIGENCE_GOAL,
        max_threads=3,
        show_log=True
    )
    
    # 3. Mount everything directly to the Engine
    engine = Engine(agents=agents, aggregator=boss)
    
    # 4. Fire the complete execution pipeline
    document_payload = json.dumps(current_document_context)
    
    loop = asyncio.get_running_loop()
    execution_results = await loop.run_in_executor(None, engine.run, document_payload, True)
    
    # 5. Extract results out of the Report traces to stream cleanly to the UI
    for trace in execution_results.traces:
        color = agent_color_map.get(trace.agent_role, "#FFFFFF")
        
        # Determine the raw output based on the trace state
        raw_output = trace.output if trace.status == "success" else {"insight": f"Error: {trace.error_message}"}
        formatted_report = parse_agent_response(raw_output, trace.agent_role, color)
        
        yield f"data: {json.dumps({'status': 'agent_report', 'data': formatted_report})}\n\n"
        await asyncio.sleep(0.3)
        
    # 6. Pull the final aggregated output from the engine state
    yield f"data: {json.dumps({'status': 'aggregator_started', 'message': 'Compiling cross-domain conflict analysis...'})}\n\n"
    await asyncio.sleep(0.2)
    
    aggregated_report = execution_results.consensus
    
    # Handle object conversion if the aggregator returned a structured Pydantic object
    if hasattr(aggregated_report, 'model_dump'):
        aggregated_report = aggregated_report.model_dump()
    elif isinstance(aggregated_report, str):
        try:
            aggregated_report = json.loads(aggregated_report)
        except json.JSONDecodeError:
            pass

    yield f"data: {json.dumps({'status': 'conflict_report', 'data': aggregated_report})}\n\n"
    yield f"data: {json.dumps({'status': 'complete'})}\n\n"


@app.get("/api/analyze")
async def analyze_document():
    return StreamingResponse(run_octochains_stream(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)