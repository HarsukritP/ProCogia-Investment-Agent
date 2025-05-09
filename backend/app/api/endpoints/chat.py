from fastapi import APIRouter, Depends, Body
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import json
from datetime import datetime

from ...services.llm.openai_client import openai_client
from ...services.get.market_data import market_data_service
from ...services.get.news_sentiment import news_sentiment_service
from ...services.analyze.market_analyzer import market_analyzer
from ...services.analyze.portfolio_optimizer import portfolio_optimizer
from ...services.analyze.risk_analyzer import risk_analyzer

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    portfolio_id: Optional[int] = None

class ChatResponse(BaseModel):
    response: str
    actions_taken: Optional[List[str]] = None
    timestamp: str

router = APIRouter()

@router.post("/", response_model=ChatResponse)
def chat(request: ChatRequest = Body(...)):
    """
    Chat with the portfolio optimization agent.
    """
    # Format messages for the LLM
    formatted_messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
    
    # Add system prompt
    system_prompt = """
    You are an advanced AI-powered portfolio optimization agent for investment firms. You continuously monitor financial markets, assess risk, optimize asset allocations, and provide actionable investment recommendations. You help investment professionals make data-driven decisions to maximize returns while managing risk.
    
    When interacting with users:
    1. Provide clear, concise answers to investment questions
    2. Support your recommendations with data and analysis
    3. Be professional but conversational
    4. Explain complex financial concepts in accessible terms
    5. Offer actionable insights whenever possible
    
    Use the real-time market data and portfolio information that has been provided to inform your responses.
    """
    
    # Keep track of actions taken
    actions_taken = []
    
    # Enhance with market insights if relevant
    user_query = request.messages[-1].content.lower()
    
    if any(keyword in user_query for keyword in ["market", "economy", "news", "sentiment", "outlook"]):
        # Get market analysis
        try:
            market_analysis = market_analyzer.analyze_market_conditions()
            actions_taken.append("Analyzed market conditions")
            
            # Enhance system prompt with market insights
            system_prompt += f"\n\nCurrent Market Context (as of {datetime.now().strftime('%Y-%m-%d %H:%M')}):"
            
            if "market_summary" in market_analysis:
                system_prompt += f"\n- Market Summary: {market_analysis['market_summary']}"
            
            if "market_outlook" in market_analysis:
                short_term = market_analysis["market_outlook"]["short_term"]["outlook"]
                medium_term = market_analysis["market_outlook"]["medium_term"]["outlook"]
                system_prompt += f"\n- Market Outlook: {short_term.title()} short-term, {medium_term.title()} medium-term"
            
            if "indices_analysis" in market_analysis and "trend" in market_analysis["indices_analysis"]:
                system_prompt += f"\n- Market Trend: {market_analysis['indices_analysis']['trend'].title()}"
            
            if "key_drivers" in market_analysis and market_analysis["key_drivers"]:
                top_driver = market_analysis["key_drivers"][0]["factor"]
                system_prompt += f"\n- Primary Market Driver: {top_driver}"
        
        except Exception as e:
            print(f"Error enhancing with market data: {e}")
    
    # Generate response using OpenAI
    response = openai_client.generate_response(formatted_messages, system_prompt)
    
    # Return the response
    return {
        "response": response,
        "actions_taken": actions_taken,
        "timestamp": datetime.now().isoformat()
    }