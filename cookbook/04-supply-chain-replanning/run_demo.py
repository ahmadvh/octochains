# run_demo.py
import os
import csv
from dotenv import load_dotenv
from openai import OpenAI

from octochains.engine import Engine
from octochains.aggregators import Synthesizer  

# Import the modularized agents
from agents.inventory_analyst import InventoryAnalyst
from agents.logistics_director import LogisticsDirector

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "your-key-here")
client = OpenAI()

# ==============================================================================
# 1. Orchestration with Built-in Synthesizer
# ==============================================================================

def main():
    crisis_brief = (
        "CRISIS BRIEF: The Port of Hamburg is on strike. All sea freight for our "
        "flagship product (SKU: X-900) to EU-Central is halted. "
        "We need to know if we have backup stock in US-East, and if so, how much it "
        "will cost to air-freight 300 units to EU-Central immediately to save key contracts."
    )

    print("🚨 Global Supply Chain Crisis Detected. Initiating Octochains...")
    
    action_plan_goal = (
        "You are the VP of Operations. Your objective is to synthesize the inventory and logistics "
        "data into a final emergency action plan. "
        "CRITICAL INSTRUCTIONS: "
        "1. Identify the exact number of units requested in the original Crisis Brief. "
        "2. Identify the freight cost per unit from the logistics data. "
        "3. You MUST calculate and output the total final cost (Units Requested multiplied by Cost Per Unit). "
        "Do not authorize shipping excess inventory. You must list the final calculated dollar amount in your key_takeaways."
    )
    
    # A simple callable for the Synthesizer since it doesn't need tools
    def call_openai_simple(prompt: str) -> str:
        res = client.chat.completions.create(
            model="gpt-4o", 
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        return res.choices[0].message.content

    boss = Synthesizer(
        llm_callable=call_openai_simple,
        custom_goal=action_plan_goal
    )
    
    # Notice how clean the Engine initialization is now
    engine = Engine(
        agents=[InventoryAnalyst(), LogisticsDirector()], 
        aggregator=boss
    )
    
    output_path = "cookbook/04-supply-chain-replanning/results/report.txt"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Run the engine
    report = engine.run(problem_data=crisis_brief, show_log=True) 
    
    with open(output_path, "w") as f:
        f.write(report.model_dump_json(indent=2))
    
    print("\n" + "="*50)
    print(" 📦 FINAL EMERGENCY ACTION PLAN")
    print("="*50)
    print(f"Confidence Level: {report.consensus.confidence * 100}%")
    print("\nNarrative Strategy:")
    print(report.consensus.narrative)
    
    print("\nAction Items:")
    for takeaway in report.consensus.key_takeaways:
        print(f" - {takeaway}")

    print("\nCitations:")
    for key, citation in report.consensus.citations.items():
        print(f" - [{key}]: {citation}")

        

if __name__ == "__main__":
    main()