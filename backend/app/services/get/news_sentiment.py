import os
import json
import requests
import random
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
from fastapi import HTTPException
from loguru import logger

from ...core.config import settings
from ...database.mongodb import news_collection, sentiment_collection
from ...database.redis import redis_client

class NewsSentimentService:
    """Service for retrieving news and sentiment data."""
    
    def __init__(self):
        """Initialize the news and sentiment service."""
        self.cache_expiry = settings.CACHE_EXPIRY
        self.news_api_key = settings.NEWS_API_KEY
        self.alpha_vantage_api_key = settings.ALPHA_VANTAGE_API_KEY
        self.finnhub_api_key = settings.FINNHUB_API_KEY
    
    def get_market_news(self, symbols: Optional[List[str]] = None, 
                       topics: Optional[List[str]] = None, 
                       days: int = 3) -> Dict[str, Any]:
        """
        Retrieve market news relevant to specified symbols or topics using real APIs.
        
        Args:
            symbols: List of stock symbols to retrieve news for
            topics: List of topics to filter news by
            days: Number of days to look back for news
        
        Returns:
            Dictionary containing filtered news items with sentiment analysis
        """
        # Build cache key based on the request parameters
        symbols_str = "-".join(symbols) if symbols else "none"
        topics_str = "-".join(topics) if topics else "none"
        cache_key = f"market_news:{symbols_str}:{topics_str}:{days}"
        
        # Check if data is in cache
        cached_data = redis_client.get(cache_key)
        if cached_data:
            logger.debug(f"Retrieved news data from cache: {cache_key}")
            return json.loads(cached_data)
        
        # Fetch news based on the provided filters
        news_items = self._fetch_news(symbols, topics, days)
        
        # Analyze sentiment for news items
        self._analyze_all_sentiment(news_items)
        
        # Calculate sentiment distribution
        sentiment_distribution = {
            "positive": sum(1 for item in news_items if item.get("sentiment") == "positive"),
            "neutral": sum(1 for item in news_items if item.get("sentiment") == "neutral"),
            "negative": sum(1 for item in news_items if item.get("sentiment") == "negative")
        }
        
        # Calculate impact distribution
        impact_distribution = {
            "high": sum(1 for item in news_items if item.get("impact") == "high"),
            "medium": sum(1 for item in news_items if item.get("impact") == "medium"),
            "low": sum(1 for item in news_items if item.get("impact") == "low")
        }
        
        # Extract primary topics
        primary_topics = self._extract_primary_topics(news_items)
        
        # Calculate overall sentiment
        overall_sentiment = self._calculate_overall_sentiment(sentiment_distribution)
        
        # Prepare result
        result = {
            "timestamp": datetime.now().isoformat(),
            "news_items": news_items,
            "analysis": {
                "sentiment_distribution": sentiment_distribution,
                "impact_distribution": impact_distribution,
                "overall_sentiment": overall_sentiment,
                "primary_topics": primary_topics
            }
        }
        
        # Save to cache
        redis_client.setex(cache_key, self.cache_expiry, json.dumps(result))
        logger.debug(f"Cached news data: {cache_key}")
        
        return result
    
    def _fetch_news(self, symbols: Optional[List[str]], topics: Optional[List[str]], days: int) -> List[Dict[str, Any]]:
        """
        Fetch news articles from real APIs based on the provided filters.
        
        Args:
            symbols: List of stock symbols
            topics: List of topics
            days: Number of days to look back
            
        Returns:
            List of news items
        """
        # Calculate cutoff date
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        # Build MongoDB query for cached news
        query = {"published_at": {"$gte": cutoff_date}}
        
        # Add symbol/topic filtering if provided
        if symbols or topics:
            keywords = []
            
            if symbols:
                # Add symbols
                keywords.extend([symbol.lower() for symbol in symbols])
                
                # Add company names
                company_names = [name.lower() for name in self._get_company_names(symbols) if name]
                keywords.extend(company_names)
            
            if topics:
                # Add topics
                keywords.extend([topic.lower() for topic in topics])
            
            # Add keywords to query if we have any
            if keywords:
                regex_pattern = "|".join(keywords)
                query["$or"] = [
                    {"title_lower": {"$regex": regex_pattern}},
                    {"summary_lower": {"$regex": regex_pattern}}
                ]
        
        # Query MongoDB for cached news
        db_news = list(news_collection.find(query).sort("published_at", -1).limit(20))
        
        # If we have enough news items in cache, just use those
        if len(db_news) >= 10:
            # Remove MongoDB IDs
            for item in db_news:
                item.pop("_id", None)
                
            logger.debug(f"Retrieved {len(db_news)} news items from MongoDB cache")
            return db_news
        
        # Otherwise, fetch from APIs and supplement
        logger.debug("Not enough news items in cache, fetching from APIs")
        api_news = []
        
        # Try different news sources
        
        # 1. Try NewsAPI first
        newsapi_items = self._fetch_from_newsapi(symbols, topics, days)
        if newsapi_items:
            api_news.extend(newsapi_items)
            logger.debug(f"Retrieved {len(newsapi_items)} news items from NewsAPI")
        
        # 2. Try Alpha Vantage News API
        alpha_vantage_items = self._fetch_from_alpha_vantage(symbols, days)
        if alpha_vantage_items:
            api_news.extend(alpha_vantage_items)
            logger.debug(f"Retrieved {len(alpha_vantage_items)} news items from Alpha Vantage")
        
        # 3. Try Finnhub News API
        finnhub_items = self._fetch_from_finnhub(symbols, days)
        if finnhub_items:
            api_news.extend(finnhub_items)
            logger.debug(f"Retrieved {len(finnhub_items)} news items from Finnhub")
        
        # Combine and deduplicate all news (from DB and APIs)
        all_news = db_news + api_news
        unique_news = []
        seen_titles = set()
        
        for item in all_news:
            title = item.get("title", "")
            if title and title not in seen_titles:
                seen_titles.add(title)
                
                # Add lowercase versions for future queries
                if "title_lower" not in item:
                    item["title_lower"] = title.lower()
                
                if "summary_lower" not in item and "summary" in item:
                    item["summary_lower"] = item["summary"].lower()
                
                unique_news.append(item)
                
                # Store in MongoDB for future use if not already from DB
                if "_id" not in item:
                    try:
                        news_collection.insert_one(item.copy())
                    except Exception as e:
                        logger.error(f"Error storing news item in MongoDB: {e}")
        
        logger.debug(f"Retrieved {len(unique_news)} unique news items total")
        return unique_news[:20]  # Return top 20 news items
    
    def _fetch_from_newsapi(self, symbols: Optional[List[str]], topics: Optional[List[str]], days: int) -> List[Dict[str, Any]]:
        """
        Fetch news from NewsAPI.
        
        Args:
            symbols: List of stock symbols
            topics: List of topics
            days: Number of days to look back
            
        Returns:
            List of news items
        """
        if not self.news_api_key:
            logger.debug("No NewsAPI key available")
            return []
        
        try:
            # Build query
            query_parts = []
            
            if symbols:
                company_names = self._get_company_names(symbols)
                for i, symbol in enumerate(symbols):
                    query_parts.append(symbol)
                    if i < len(company_names) and company_names[i]:
                        query_parts.append(company_names[i])
            
            if topics:
                query_parts.extend(topics)
            
            # Default query if nothing specified
            query = " OR ".join(query_parts) if query_parts else "finance OR markets OR economy"
            
            # Calculate date range
            from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            
            # Make API request
            logger.debug(f"Fetching news from NewsAPI with query: {query}")
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": query,
                "from": from_date,
                "sortBy": "publishedAt",
                "apiKey": self.news_api_key,
                "language": "en"
            }
            
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                if "articles" in data and data["articles"]:
                    # Format articles
                    news_items = []
                    
                    for article in data["articles"]:
                        # Skip articles without title or description
                        if not article.get("title") or not article.get("description"):
                            continue
                        
                        # Create news item
                        news_item = {
                            "title": article["title"],
                            "title_lower": article["title"].lower(),
                            "source": article["source"]["name"] if article.get("source") and article["source"].get("name") else "NewsAPI",
                            "summary": article.get("description", ""),
                            "summary_lower": article.get("description", "").lower(),
                            "url": article.get("url", ""),
                            "published_at": article.get("publishedAt", datetime.now().isoformat()),
                            "sentiment": None,  # Will be filled in later
                            "impact": None      # Will be filled in later
                        }
                        
                        news_items.append(news_item)
                    
                    return news_items
                else:
                    logger.warning(f"No articles found in NewsAPI response: {data}")
            else:
                logger.warning(f"NewsAPI request failed: {response.status_code} - {response.text}")
        
        except Exception as e:
            logger.error(f"Error fetching news from NewsAPI: {e}")
        
        return []
    
    def _fetch_from_alpha_vantage(self, symbols: Optional[List[str]], days: int) -> List[Dict[str, Any]]:
        """
        Fetch news from Alpha Vantage News API.
        
        Args:
            symbols: List of stock symbols
            days: Number of days to look back
            
        Returns:
            List of news items
        """
        if not self.alpha_vantage_api_key:
            logger.debug("No Alpha Vantage API key available")
            return []
        
        news_items = []
        
        # Alpha Vantage has a News API that can be used to get news for symbols
        if symbols:
            for symbol in symbols:
                try:
                    # Get news sentiment for the symbol
                    logger.debug(f"Fetching news from Alpha Vantage for {symbol}")
                    url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={symbol}&apikey={self.alpha_vantage_api_key}"
                    response = requests.get(url)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        if "feed" in data:
                            # Parse news feed
                            for article in data["feed"]:
                                # Filter by date if needed
                                if "time_published" in article:
                                    pub_date = datetime.strptime(article["time_published"], "%Y%m%dT%H%M%S")
                                    if (datetime.now() - pub_date).days > days:
                                        continue
                                
                                # Create news item
                                news_item = {
                                    "title": article.get("title", ""),
                                    "title_lower": article.get("title", "").lower(),
                                    "source": article.get("source", "Alpha Vantage"),
                                    "summary": article.get("summary", ""),
                                    "summary_lower": article.get("summary", "").lower(),
                                    "url": article.get("url", ""),
                                    "published_at": datetime.strptime(article["time_published"], "%Y%m%dT%H%M%S").isoformat() if "time_published" in article else datetime.now().isoformat(),
                                    "impact": "medium"  # Default impact
                                }
                                
                                # Add sentiment if available
                                if "overall_sentiment_score" in article:
                                    sentiment_score = float(article["overall_sentiment_score"])
                                    if sentiment_score > 0.25:
                                        news_item["sentiment"] = "positive"
                                    elif sentiment_score < -0.25:
                                        news_item["sentiment"] = "negative"
                                    else:
                                        news_item["sentiment"] = "neutral"
                                else:
                                    news_item["sentiment"] = None
                                
                                news_items.append(news_item)
                        else:
                            logger.warning(f"No news feed in Alpha Vantage response for {symbol}")
                    else:
                        logger.warning(f"Alpha Vantage request failed for {symbol}: {response.status_code} - {response.text}")
                
                except Exception as e:
                    logger.error(f"Error fetching news from Alpha Vantage for {symbol}: {e}")
        
        return news_items
    
    def _fetch_from_finnhub(self, symbols: Optional[List[str]], days: int) -> List[Dict[str, Any]]:
        """
        Fetch news from Finnhub API.
        
        Args:
            symbols: List of stock symbols
            days: Number of days to look back
            
        Returns:
            List of news items
        """
        if not self.finnhub_api_key:
            logger.debug("No Finnhub API key available")
            return []
        
        news_items = []
        
        try:
            # Get general market news if no symbols specified
            if not symbols:
                logger.debug("Fetching general market news from Finnhub")
                url = f"https://finnhub.io/api/v1/news?category=general&token={self.finnhub_api_key}"
                response = requests.get(url)
                
                if response.status_code == 200:
                    articles = response.json()
                    
                    for article in articles:
                        # Filter by date
                        if "datetime" in article:
                            pub_date = datetime.fromtimestamp(article["datetime"])
                            if (datetime.now() - pub_date).days > days:
                                continue
                        
                        # Create news item
                        news_item = {
                            "title": article.get("headline", ""),
                            "title_lower": article.get("headline", "").lower(),
                            "source": article.get("source", "Finnhub"),
                            "summary": article.get("summary", ""),
                            "summary_lower": article.get("summary", "").lower(),
                            "url": article.get("url", ""),
                            "published_at": datetime.fromtimestamp(article["datetime"]).isoformat() if "datetime" in article else datetime.now().isoformat(),
                            "sentiment": None,  # Will be analyzed later
                            "impact": None      # Will be analyzed later
                        }
                        
                        news_items.append(news_item)
            else:
                # Get company-specific news for each symbol
                for symbol in symbols:
                    logger.debug(f"Fetching news from Finnhub for {symbol}")
                    from_time = int((datetime.now() - timedelta(days=days)).timestamp())
                    to_time = int(datetime.now().timestamp())
                    
                    url = f"https://finnhub.io/api/v1/company-news?symbol={symbol}&from={from_time}&to={to_time}&token={self.finnhub_api_key}"
                    response = requests.get(url)
                    
                    if response.status_code == 200:
                        articles = response.json()
                        
                        for article in articles:
                            # Create news item
                            news_item = {
                                "title": article.get("headline", ""),
                                "title_lower": article.get("headline", "").lower(),
                                "source": article.get("source", "Finnhub"),
                                "summary": article.get("summary", ""),
                                "summary_lower": article.get("summary", "").lower(),
                                "url": article.get("url", ""),
                                "published_at": datetime.fromtimestamp(article["datetime"]).isoformat() if "datetime" in article else datetime.now().isoformat(),
                                "sentiment": None,  # Will be analyzed later
                                "impact": None      # Will be analyzed later
                            }
                            
                            news_items.append(news_item)
        
        except Exception as e:
            logger.error(f"Error fetching news from Finnhub: {e}")
        
        return news_items
    
    def _analyze_all_sentiment(self, news_items: List[Dict[str, Any]]) -> None:
        """
        Analyze sentiment for all news items in the list.
        
        Args:
            news_items: List of news items
        """
        for item in news_items:
            if "sentiment" not in item or not item["sentiment"]:
                item["sentiment"] = self._analyze_sentiment(item.get("title", ""), item.get("summary", ""))
                
            if "impact" not in item or not item["impact"]:
                item["impact"] = self._analyze_impact(item.get("title", ""), item.get("summary", ""))
    
    def _get_company_names(self, symbols: List[str]) -> List[str]:
        """
        Get company names for the provided symbols.
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            List of company names
        """
        # Mapping of common symbols to company names
        symbol_to_name = {
            "AAPL": "Apple",
            "MSFT": "Microsoft",
            "AMZN": "Amazon",
            "GOOGL": "Google",
            "META": "Meta",
            "TSLA": "Tesla",
            "NVDA": "NVIDIA",
            "BRK.B": "Berkshire Hathaway",
            "JPM": "JPMorgan Chase",
            "JNJ": "Johnson & Johnson",
            "UNH": "UnitedHealth Group",
            "V": "Visa",
            "PG": "Procter & Gamble",
            "XOM": "Exxon Mobil",
            "WMT": "Walmart",
            "LLY": "Eli Lilly",
            "MA": "Mastercard",
            "HD": "Home Depot",
            "MRK": "Merck",
            "CVX": "Chevron"
        }
        
        return [symbol_to_name.get(symbol, symbol) for symbol in symbols]
    
    def _analyze_sentiment(self, title: str, summary: str) -> str:
        """
        Analyze sentiment of news article using real NLP or APIs when available.
        
        Args:
            title: Article title
            summary: Article summary
            
        Returns:
            Sentiment category ("positive", "neutral", "negative")
        """
        # Check if we've already analyzed this content
        content_hash = hash(title + summary)
        stored_sentiment = sentiment_collection.find_one({"content_hash": content_hash})
        
        if stored_sentiment:
            logger.debug(f"Retrieved sentiment from cache for '{title[:30]}...'")
            return stored_sentiment["sentiment"]
        
        # In a real implementation, we would use OpenAI or another API for sentiment analysis
        # For this demo, we'll use a keyword-based approach
        text = (title + " " + summary).lower()
        
        positive_words = ["up", "rise", "gain", "growth", "surge", "rally", "beat", "strong", 
                        "positive", "bullish", "upgrade", "opportunity", "improvement", "success",
                        "profit", "exceed", "outperform", "record", "boost", "recovery"]
        
        negative_words = ["down", "fall", "drop", "decline", "loss", "weak", "bearish", "miss", 
                        "cut", "downgrade", "risk", "concern", "trouble", "difficult", "warn",
                        "fail", "disappointing", "underperform", "below", "struggle"]
        
        # Count occurrences of positive and negative words
        pos_count = sum(1 for word in positive_words if word in text)
        neg_count = sum(1 for word in negative_words if word in text)
        
        # Determine sentiment
        if pos_count > neg_count:
            sentiment = "positive"
        elif neg_count > pos_count:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        # Store in MongoDB for future use
        sentiment_collection.insert_one({
            "content_hash": content_hash,
            "title": title[:100],  # Store just enough for identification
            "sentiment": sentiment,
            "timestamp": datetime.now().timestamp()
        })
        
        logger.debug(f"Analyzed sentiment for '{title[:30]}...': {sentiment}")
        return sentiment
    
    def _analyze_impact(self, title: str, summary: str) -> str:
        """
        Analyze potential market impact of news article.
        
        Args:
            title: Article title
            summary: Article summary
            
        Returns:
            Impact category ("high", "medium", "low")
        """
        text = (title + " " + summary).lower()
        
        high_impact_keywords = ["fed", "interest rate", "inflation", "recession", "gdp", "war", "crisis", 
                              "crash", "collapse", "breakthrough", "acquisition", "merger", "tariff",
                              "regulation", "policy", "election", "default", "bankruptcy"]
        
        medium_impact_keywords = ["earnings", "forecast", "outlook", "report", "guidance", 
                                "announce", "launch", "update", "regulatory", "leadership",
                                "dividend", "buyback", "investment", "partnership", "lawsuit"]
        
        # Check for high impact keywords
        if any(keyword in text for keyword in high_impact_keywords):
            return "high"
        
        # Check for medium impact keywords
        elif any(keyword in text for keyword in medium_impact_keywords):
            return "medium"
        
        # Default to low impact
        else:
            return "low"
    
    def _calculate_overall_sentiment(self, sentiment_distribution: Dict[str, int]) -> str:
        """
        Calculate overall sentiment based on distribution.
        
        Args:
            sentiment_distribution: Count of articles by sentiment
            
        Returns:
            Overall sentiment category
        """
        total = sum(sentiment_distribution.values())
        
        if total == 0:
            return "neutral"
        
        positive_pct = sentiment_distribution["positive"] / total
        negative_pct = sentiment_distribution["negative"] / total
        
        if positive_pct > 0.6:
            return "strongly positive"
        elif positive_pct > 0.4:
            return "moderately positive"
        elif negative_pct > 0.6:
            return "strongly negative"
        elif negative_pct > 0.4:
            return "moderately negative"
        else:
            return "neutral"
    
    def _extract_primary_topics(self, news_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract the primary topics from news articles.
        
        Args:
            news_items: List of news items
            
        Returns:
            List of primary topics with counts
        """
        # Common financial topics
        topics = {
            "interest rates": 0,
            "inflation": 0,
            "earnings": 0,
            "federal reserve": 0,
            "monetary policy": 0,
            "economic growth": 0,
            "recession": 0,
            "stock market": 0,
            "technology": 0,
            "regulation": 0,
            "energy": 0,
            "consumer spending": 0,
            "housing market": 0,
            "unemployment": 0,
            "trade": 0,
            "cryptocurrency": 0,
            "ai": 0,
            "supply chain": 0
        }
        
        # Count mentions
        for item in news_items:
            text = (item.get("title", "") + " " + item.get("summary", "")).lower()
            
            for topic in topics:
                if topic in text:
                    topics[topic] += 1
        
        # Sort by count and return top topics
        sorted_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)
        
        # Filter out topics with no mentions
        primary_topics = [{"topic": topic, "count": count} for topic, count in sorted_topics if count > 0]
        
        return primary_topics[:5]  # Return top 5 topics

# Create an instance of the service for easy importing
news_sentiment_service = NewsSentimentService()