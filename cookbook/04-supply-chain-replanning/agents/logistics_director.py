import csv
import json
from openai import OpenAI
from octochains.base import Agent
import os
from dotenv import load_dotenv

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "your-key-here")
client = OpenAI()


class LogisticsDirector(Agent):
    def __init__(self):
        super().__init__(
            role="Director of Logistics",
            goal="Calculate emergency shipping timelines and costs to bypass the disruption."
        )

    def get_freight_rates(self, route: str, method: str) -> str:
        try:
            data_path = "cookbook/04-supply-chain-replanning/agents/agents_resource_data/freight_rates.csv"
            with open(data_path, "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row["Route"] == route and row["Method"] == method:
                        return f"Method: {method}, Cost: {row['Cost_Per_Unit']}, Time: {row['Days_In_Transit']} days."
            return "Route not found."
        except Exception as e:
            return f"Database error: {str(e)}"

    def execute(self, problem_data: str) -> str:
        system_prompt = self._build_prompt(problem_data)
        
        tools = [{
            "type": "function",
            "function": {
                "name": "get_freight_rates",
                "description": "Calculate alternative shipping costs and timelines.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "route": {"type": "string", "description": "Format: 'Origin to Destination' (e.g., 'US-East to EU-Central')"},
                        "method": {"type": "string", "description": "'Air' or 'Sea'"}
                    },
                    "required": ["route", "method"]
                }
            }
        }]

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Please analyze the problem and provide your final expert report."}
        ]

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=tools,
            temperature=0.1
        )
        
        response_message = response.choices[0].message
        messages.append(response_message)

        if response_message.tool_calls:
            tool_call = response_message.tool_calls[0]
            args = json.loads(tool_call.function.arguments)
            
            tool_result = self.get_freight_rates(args.get("route"), args.get("method"))
            
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_result
            })

            final_response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.1
            )
            return final_response.choices[0].message.content

        return response_message.content