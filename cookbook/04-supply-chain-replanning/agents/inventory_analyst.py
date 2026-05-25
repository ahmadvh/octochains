import csv
import json
from openai import OpenAI
from octochains.base import Agent
import os
from dotenv import load_dotenv

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "your-key-here")
client = OpenAI()


class InventoryAnalyst(Agent):
    def __init__(self):
        super().__init__(
            role="Global Inventory Analyst",
            goal="Determine if we have enough domestic stock to survive the supply chain disruption.",
            input_description="A brief text summary of a live global supply chain crisis."
        )

    def check_local_stock(self, sku: str, region: str) -> str:
        try:
            data_path = "cookbook/04-supply-chain-replanning/agents/agents_resource_data/warehouse_stock.csv"
            with open(data_path, "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row["SKU"] == sku and row["Region"] == region:
                        return f"Found {row['Units_Available']} units of {sku} in {region}."
            return f"No stock found for {sku} in {region}."
        except Exception as e:
            return f"Database error: {str(e)}"

    def execute(self, problem_data: str) -> str:
        system_prompt = self._build_prompt(problem_data)
        
        tools = [{
            "type": "function",
            "function": {
                "name": "check_local_stock",
                "description": "Check the warehouse database for inventory levels.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sku": {"type": "string", "description": "The product ID (e.g., X-900)"},
                        "region": {"type": "string", "description": "The geographical region (e.g., US-East)"}
                    },
                    "required": ["sku", "region"]
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
            
            tool_result = self.check_local_stock(args.get("sku"), args.get("region"))
            
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