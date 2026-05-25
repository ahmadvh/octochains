# Octochains Cookbook: Supply Chain Replanning

This example demonstrates how to build an **Enterprise-Grade Supply Chain Crisis Resolution Workflow** using Octochains.

It highlights how specialized agents can use custom Pydantic-powered tools to query local CSV databases in parallel, strictly isolated from one another, before synthesizing their findings into a final executive action plan.

## The Scenario

**Crisis Brief:** The Port of Hamburg is on strike. All sea freight for our flagship product (SKU: X-900) to EU-Central is halted. The Executive Board needs an immediate action plan to save key contracts.

We need to know:
1. Do we have backup stock in our domestic warehouses (e.g., US-East)?
2. If so, how much will it cost to air-freight 300 units to EU-Central immediately?

## The Architecture

This cookbook introduces the **Built-in `Synthesizer`** and the **`@tool` decorator** with Pydantic schemas.

### 1. Parallel Data Fetching
* **The Inventory Analyst:** Equipped with a `check_local_stock` tool. It queries a simulated `warehouse_stock.csv` to verify inventory levels.
* **The Logistics Director:** Equipped with a `get_freight_rates` tool. It queries a simulated `freight_rates.csv` to calculate alternative shipping costs and timelines.

*Crucially, these agents operate in complete isolation. The Logistics Director has no access to the warehouse database, and the Inventory Analyst cannot see freight rates.*

### 2. The Synthesizer (Aggregator)
Instead of writing a custom aggregator class, this example uses Octochains' built-in `Synthesizer`. We hijack its default behavior by passing a `custom_goal` that forces the LLM to act as the VP of Operations. 

The engine natively outputs a `SynthesisResult` Pydantic object, completely eliminating manual JSON parsing while guaranteeing a strict, predictable output structure:
* `narrative`: The immediate strategic plan.
* `key_takeaways`: Bulleted list of estimated costs, unit movements, and risk warnings.
* `confidence`: The LLM's self-assessed confidence score.
* `citations`: A verifiable audit trail mapping claims back to the isolated specialists.

## How to Run

1.  Navigate to the `cookbook/04-supply-chain-replanning` directory.
2.  Ensure your `OPENAI_API_KEY` is set in your `.env` file or environment variables.
3.  Execute the script:
    ```bash
    python dynamic_replanning.py
    ```

*(Note: The script will automatically generate the mock `warehouse_stock.csv` and `freight_rates.csv` files required for execution and delete them upon completion.)*