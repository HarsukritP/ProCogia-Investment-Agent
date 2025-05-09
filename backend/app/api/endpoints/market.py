from fastapi import APIRouter, Query
from typing import List, Optional

from ...services.get.market_data import market_data_service
from ...services.get.news_sentiment import news_sentiment_service
from ...services.analyze.market_analyzer import market_analyzer

router = APIRouter()

@router.get("/data")
def get_market_data(
    symbols: Optional[List[str]] = Query(None), 
    indices: Optional[List[str]] = Query(None)
):
    """
    Get market data for specified symbols and indices.
    """
    return market_data_service.get_market_data(symbols, indices)

@router.get("/news")
def get_market_news(
    symbols: Optional[List[str]] = Query(None), 
    topics: Optional[List[str]] = Query(None), 
    days: int = Query(3, ge=1, le=30)
):
    """
    Get market news with sentiment analysis.
    """
    return news_sentiment_service.get_market_news(symbols, topics, days)

@router.get("/analysis")
def analyze_market_conditions():
    """
    Get comprehensive market analysis.
    """
    # Fetch market data and news
    market_data = market_data_service.get_market_data(
        indices=["S&P 500", "NASDAQ", "Dow Jones", "Russell 2000", "VIX"]
    )
    
    news_data = news_sentiment_service.get_market_news(
        topics=["market", "economy", "federal reserve", "inflation"]
    )
    
    # Analyze market conditions
    return market_analyzer.analyze_market_conditions(market_data, news_data)