import os
from litellm import completion
from octochains.base import Agent, Aggregator
from octochains.engine import Engine 
from dotenv import load_dotenv

# --- Configuration ---
# Pointing to your GPU machine running Ollama
OLLAMA_API_BASE = "http://localhost:11434"
# Using a small, fast local model (change to phi3, gemma2:2b, or qwen2.5 as needed)
MODEL_NAME = "ollama/llama3.2:3b"

def call_ollama(prompt: str) -> str:
    """Helper function to call the local Ollama model via LiteLLM."""
    response = completion(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        api_base=OLLAMA_API_BASE,
        # Optional: Adjust temperature. Low for technical/cynic, slightly higher for marketing
        temperature=0.4 
    )
    return response.choices[0].message.content

# --- 1. Define the Agents ---

class TechLead(Agent):
    def __init__(self):
        super().__init__(
            role="Tech Lead", 
            goal="Assess the technical feasibility of the idea and suggest the most efficient technology stack."
        )

    def execute(self, problem_data: str) -> str:
        prompt = f"""You are a {self.role}. Your goal is to {self.goal}.
        Analyze the following Micro-SaaS idea and provide:
        1. Technical feasibility score (1-10)
        2. Recommended Tech Stack
        3. Biggest technical hurdle.
        
        Idea: {problem_data}"""
        
        return call_ollama(prompt)

class MarketingGuru(Agent):
    def __init__(self):
        super().__init__(
            role="Marketing Guru", 
            goal="Identify the target audience, the 'hook', and user acquisition channels."
        )

    def execute(self, problem_data: str) -> str:
        prompt = f"""You are a {self.role}. Your goal is to {self.goal}.
        Analyze the following Micro-SaaS idea and provide:
        1. Target Audience Persona
        2. The primary marketing 'hook' or value proposition.
        3. Top 2 cheap user acquisition channels.
        
        Idea: {problem_data}"""
        
        return call_ollama(prompt)

class RiskOfficer(Agent):
    def __init__(self):
        super().__init__(
            role="Cynic / Risk Officer", 
            goal="Find every reason why this idea will fail, focusing on market competition and user churn."
        )

    def execute(self, problem_data: str) -> str:
        prompt = f"""You are a {self.role}. Your goal is to {self.goal}.
        Analyze the following Micro-SaaS idea and provide:
        1. Why this will fail (be brutal).
        2. Hidden competitors (who is already doing this for free?).
        3. Why users will churn after week 1.
        
        Idea: {problem_data}"""
        
        return call_ollama(prompt)

class PricingSpecialist(Agent):
    def __init__(self):
        super().__init__(
            role="Pricing Specialist", 
            goal="Determine the optimal monetization strategy and pricing tiers."
        )

    def execute(self, problem_data: str) -> str:
        prompt = f"""You are a {self.role}. Your goal is to {self.goal}.
        Analyze the following Micro-SaaS idea and provide:
        1. Best pricing model (Freemium, One-time, Subscription?)
        2. Suggested price points.
        3. How to justify the price to early adopters.
        
        Idea: {problem_data}"""
        
        return call_ollama(prompt)

# --- 2. Define the Aggregator ---

class VentureCapitalist(Aggregator):
    def __init__(self):
        super().__init__(
            role="Venture Capitalist", 
            goal="Decide if the idea is worth building based on the expert reports."
        )
        # Load environment variables once when the Aggregator is initialized
        load_dotenv()

    def synthesize(self, problem_data: str, agent_reports: dict) -> str:
        print(f"\n[{self.role}] Synthesizing reports and making final decision via OpenAI...\n")
        
        compiled_reports = ""
        for agent_name, report in agent_reports.items():
            compiled_reports += f"--- {agent_name} ---\n{report}\n\n"

        prompt = f"""You are a {self.role}. Your goal is to {self.goal}.
        
        ORIGINAL IDEA:
        {problem_data}
        
        EXPERT REPORTS:
        {compiled_reports}
        
        Based on the above reports, provide a final executive summary including:
        1. GO / NO-GO Decision.
        2. The strongest reason FOR building it.
        3. The strongest reason AGAINST building it.
        4. Final pivot or adjustment recommendation to make it succeed.
        """
        
        # Directly call OpenAI using LiteLLM
        # It will automatically pick up your OPENAI_API_KEY from the environment
        response = completion(
            model="gpt-4o", 
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3  
        )
        
        return response.choices[0].message.content



if __name__ == "__main__":
    # The Micro-SaaS Idea Input
    idea_input = "An app that uses AI to remind you to water your plants based on local weather, humidity in the house, and the specific breed of the plant."
    
    print(f"Evaluating Idea: '{idea_input}'\n")

    # Initialize Agents
    agents = [
        TechLead(),
        MarketingGuru(),
        RiskOfficer(),
        PricingSpecialist()
    ]

    # Initialize Aggregator
    aggregator = VentureCapitalist()

    # Create and run the Octochains Engine
    engine = Engine(agents=agents, aggregator=aggregator)
    
    # Broadcast to all agents in parallel, then aggregate
    report = engine.run(problem_data=idea_input)
    
    # --- Create Results Directory ---
    output_dir = "demo-examples/02-micro-saas-validator/results"
    os.makedirs(output_dir, exist_ok=True)
    print(f"\n📁 Saving reports to '{output_dir}/' directory...\n")

    for trace in report.traces:
        # Extract role and output safely
        role = getattr(trace, 'agent_role', getattr(trace, 'agent_name', 'Specialist'))
        output = getattr(trace, 'output', getattr(trace, 'result', str(trace)))
        
        # Save individual trace to a file
        safe_filename = role.replace(" ", "_").replace("/", "").lower()
        file_path = os.path.join(output_dir, f"{safe_filename}_report.txt")
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"ROLE: {role}\n")
            f.write("="*30 + "\n")
            f.write(output)
            
    # --- Print and Save the Final Aggregated Consensus ---
    final_verdict = report.consensus

    # Save the final verdict to a file
    final_file_path = os.path.join(output_dir, "final_venture_capitalist_verdict.txt")
    with open(final_file_path, "w", encoding="utf-8") as f:
        f.write("🚀 FINAL VENTURE CAPITALIST VERDICT\n")
        f.write("="*50 + "\n")
        f.write(final_verdict)
        print("🚀 FINAL VENTURE CAPITALIST VERDICT\n")
        print("="*50 + "\n")
        print(final_verdict)
        
    print(f"\n✅ All reports successfully saved in the '{output_dir}/' folder.")