# AI-Agents-for-Stock-market-agent

<img width="900" alt="image" src="https://github.com/user-attachments/assets/b7c87bf6-dfff-42fe-b8d1-9be9e6c7ce86">

A Python project designed to create specialized LLM-based AI agents that analyze complex stock market agent ,langchain , and LLM API that can fetch the latest stock market prices for the asked ticker/stock. The system integrates insights from various stock  professionals to provide comprehensive assessments and personalized stock agents recommendations, demonstrating the potential of AI in multidisciplinary places.

## Current Version Overview

In the current version, we have implemented three AI agents using GPT-4o, each specializing in a different aspect of latest stock analysis . A report is passed to each of these agents, who then analyze the report simultaneously using threading, based on their specific area of expertise. Each agent provides recommendations and diagnoses from their perspective. After all AI agents complete their analyses, the results are combined and passed to a large language model, which summarizes the findings and identifies three potential health issues for the agents.

### AI Agents

**1. stock market agent **

- **Focus**: Identify any potential cardiac issues that could explain the patient's symptoms, including ruling out conditions such as arrhythmias or structural abnormalities that might not be apparent in initial evaluations.
  
- **Recommendation**: Suggest additional cardiovascular testing or continuous monitoring if necessary to uncover hidden heart-related problems. Provide management strategies if a cardiovascular issue is identified.

**2. stock agent**

- **Focus**: Determine if the symptoms align with a psychological condition, such as panic disorder or another anxiety-related issue. Assess the impact of stress, anxiety, and lifestyle factors on the patient’s overall condition.
  
- **Recommendation**: Recommend appropriate psychological interventions (e.g., therapy, stress management techniques) or medications to address the psychological aspects of the symptoms. Evaluate whether adjustments to the current psychological management are needed.

  
- **Recommendation**: Suggest additional respiratory evaluations, such as lung function tests or exercise-induced bronchoconstriction tests, to rule out any underlying lung conditions. Recommend breathing exercises or other treatments if a respiratory issue is suspected.

## Future Enhancements

In future versions, the system could expand to include a broader range of AI agents, each specializing in different stock fields, such as, to provide even more comprehensive analyses. These AI agents could be implemented using the [Assistant API from OpenAI](https://platform.openai.com/docs/assistants/overview) and use `function calling` and `code interpreter` capabilities to enhance their intelligence and effectiveness. Additionally, advanced parsing methodologies could be introduced to handle latests stock reports with more complex structures, allowing the system to accurately interpret and analyze a wider variety of latest stock data data.

## Repository Structure- **Results Folder**: Stores the outputs of the agentic system.
  
**To be able to run the code, please insert your OpenAI API key within the `apikey.env` file.**
import requests

API_KEY = 'your_alpha_vantage_api_key'

def get_stock_prices(ticker):
    url = f'https://www.alphavantage.co/query'
    params = {
        'function': 'TIME_SERIES_INTRADAY',
        'symbol': ticker,
        'interval': '5min',
        'apikey': API_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()
    
    

# Example usage:
ticker = "AAPL"  # Stock symbol (e.g., Apple)
stock_info = get_stock_prices(ticker)
print(stock_info)


4. API Agent (FastAPI):
Create an API endpoint using FastAPI to access the stock price via an HTTP request.

python
Copy
from fastapi import FastAPI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI
from pydantic import BaseModel
import requests

API_KEY = 'your_alpha_vantage_api_key'

app = FastAPI()

class StockRequest(BaseModel):
    ticker: str

def get_stock_prices(ticker):
    url = f'https://www.alphavantage.co/query'
    params = {
        'function': 'TIME_SERIES_INTRADAY',
        'symbol': ticker,
        'interval': '5min',
        'apikey': API_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()
    
# API endpoint to fetch stock prices
@app.post("/stock_price/")
async def stock_price(request: StockRequest):
    ticker = request.ticker
    stock_data = get_stock_prices(ticker)
    
    # Using LangChain with OpenAI for more advanced reasoning (optional)
    prompt_template = "Give a brief summary of the stock price of {ticker}: {price} at time {time}."
    prompt = PromptTemplate(input_variables=["ticker", "price", "time"], template=prompt_template)
    llm = OpenAI(temperature=0.7)  # Using OpenAI's GPT-3 for LLM

    chain = LLMChain(llm=llm, prompt=prompt)
    result = chain.run(ticker=ticker, price=stock_data['price'], time=stock_data['time'])
    
    return {
        'ticker': ticker,
        'price': stock_data['price'],
        'time': stock_data['time'],
        'summary': result
    } 
    "ticker": "AAPL",
    "price": "150.00",
    "time": "2025-03-25 12:00:00",
    "summary": "The stock price of AAPL is 150.00 at time 2025-03-25 12:00:00."
}

Conclusion:
This setup allows you to create an API that fetches the largest stock market prices for a given stock ticker.

The API is enhanced with LangChain to provide intelligent summaries of the stock prices.

FastAPI is used to create the API, which can be tested with curl or Postman.

Finally, the API can be deployed on a cloud server to make it publicly accessible.










