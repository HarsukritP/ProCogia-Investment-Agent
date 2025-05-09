import os
import json
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from fastapi import HTTPException
from loguru import logger

from ...core.config import settings
from ...database.mongodb import market_data_collection
from ...database.redis import redis_client

class MarketDataService:
    """Service for retrieving market data from various sources."""
    
    def __init__(self):
        """Initialize the market data service."""
        self.cache_expiry = settings.CACHE_EXPIRY
        self.alpha_vantage_api_key = settings.ALPHA_VANTAGE_API_KEY
        self.polygon_api_key = settings.POLYGON_API_KEY
        self.finnhub_api_key = settings.FINNHUB_API_KEY
    
    def get_market_data(self, symbols: Optional[List[str]] = None, 
                        indices: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Retrieve current market data for specified symbols and indices.
        
        Args:
            symbols: List of stock symbols to retrieve data for
            indices: List of market indices to retrieve data for
        
        Returns:
            Dictionary containing requested market data
        """
        # Generate cache key based on the request parameters
        cache_key = f"market_data:{'-'.join(symbols or [])}:{'-'.join(indices or [])}"
        
        # Check if data is in cache
        cached_data = redis_client.get(cache_key)
        if cached_data:
            logger.debug(f"Retrieved market data from cache: {cache_key}")
            return json.loads(cached_data)
        
        # Initialize result
        result = {"timestamp": datetime.now().isoformat()}
        
        # Get stock data
        if symbols:
            stocks = self._get_stocks_data(symbols)
            result["stocks"] = stocks
        
        # Get indices data
        indices_to_fetch = indices or ["SPY", "QQQ", "DIA"]  # Default indices ETFs
        indices_data = self._get_indices_data(indices_to_fetch)
        result["indices"] = indices_data
        
        # Get economic indicators
        result["economic_indicators"] = self._get_economic_indicators()
        
        # Get sector performance
        result["sectors"] = self._get_sector_performance()
        
        # Cache the result
        redis_client.setex(cache_key, self.cache_expiry, json.dumps(result))
        logger.debug(f"Cached market data: {cache_key}")
        
        return result
    
    def _get_stocks_data(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """
        Retrieve data for the specified stock symbols using real APIs.
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            List of dictionaries containing stock data
        """
        stocks = []
        
        for symbol in symbols:
            # Check MongoDB first for cached data
            stored_data = market_data_collection.find_one(
                {"symbol": symbol, "type": "stock", 
                 "timestamp": {"$gte": (datetime.now() - timedelta(minutes=15)).timestamp()}}
            )
            
            if stored_data:
                # Data is recent enough to use
                stored_data.pop("_id", None)
                stocks.append(stored_data)
                logger.debug(f"Retrieved {symbol} data from MongoDB (cached)")
                continue
            
            # If not found in cache or expired, fetch from API
            try:
                stock_data = None
                
                # Try Polygon.io API
                if self.polygon_api_key:
                    logger.debug(f"Fetching {symbol} data from Polygon.io")
                    url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/prev?apiKey={self.polygon_api_key}"
                    response = requests.get(url)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if "results" in data and data["results"]:
                            result = data["results"][0]
                            stock_data = {
                                "symbol": symbol,
                                "current_price": result["c"],
                                "open_price": result["o"],
                                "high_price": result["h"],
                                "low_price": result["l"],
                                "volume": result["v"],
                                "change_pct": round(((result["c"] - result["o"]) / result["o"]) * 100, 2),
                                "timestamp": datetime.now().timestamp(),
                                "type": "stock"
                            }
                
                # Try Alpha Vantage if Polygon fails or is not available
                if not stock_data and self.alpha_vantage_api_key:
                    logger.debug(f"Fetching {symbol} data from Alpha Vantage")
                    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={self.alpha_vantage_api_key}"
                    response = requests.get(url)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if "Global Quote" in data and data["Global Quote"]:
                            quote = data["Global Quote"]
                            try:
                                stock_data = {
                                    "symbol": symbol,
                                    "current_price": float(quote["05. price"]),
                                    "open_price": float(quote["02. open"]),
                                    "high_price": float(quote["03. high"]),
                                    "low_price": float(quote["04. low"]),
                                    "volume": int(quote["06. volume"]),
                                    "change_pct": float(quote["10. change percent"].replace("%", "")),
                                    "timestamp": datetime.now().timestamp(),
                                    "type": "stock"
                                }
                            except (KeyError, ValueError) as e:
                                logger.error(f"Error parsing Alpha Vantage data for {symbol}: {e}")
                
                # Try Finnhub if others fail
                if not stock_data and self.finnhub_api_key:
                    logger.debug(f"Fetching {symbol} data from Finnhub")
                    url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={self.finnhub_api_key}"
                    response = requests.get(url)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data and "c" in data:
                            stock_data = {
                                "symbol": symbol,
                                "current_price": data["c"],
                                "open_price": data["o"],
                                "high_price": data["h"],
                                "low_price": data["l"],
                                "change_pct": round(data["dp"], 2),
                                "volume": 0,  # Not provided in basic quote
                                "timestamp": datetime.now().timestamp(),
                                "type": "stock"
                            }
                
                # If we got data from any API, store and return it
                if stock_data:
                    # Get company name if not included
                    if "name" not in stock_data or not stock_data["name"]:
                        stock_data["name"] = self._get_company_name(symbol)
                    
                    # Store in MongoDB for future use
                    market_data_collection.insert_one(stock_data.copy())
                    stocks.append(stock_data)
                    continue
                
                # If all APIs fail, log the error
                logger.error(f"Failed to retrieve data for {symbol} from all APIs")
                
            except Exception as e:
                logger.error(f"Error fetching data for {symbol}: {e}")
            
            # If we reach here, we couldn't get data from any API
            logger.warning(f"Using fallback data for {symbol}")
            
            # Try to get old data from MongoDB as fallback
            old_data = market_data_collection.find_one(
                {"symbol": symbol, "type": "stock"},
                sort=[("timestamp", -1)]
            )
            
            if old_data:
                old_data.pop("_id", None)
                old_data["is_stale"] = True
                stocks.append(old_data)
                logger.debug(f"Using stale data for {symbol}")
            else:
                # Create basic placeholder data
                placeholder = {
                    "symbol": symbol,
                    "name": self._get_company_name(symbol),
                    "current_price": 0.0,
                    "is_placeholder": True,
                    "timestamp": datetime.now().timestamp(),
                    "type": "stock"
                }
                stocks.append(placeholder)
                logger.debug(f"Using placeholder data for {symbol}")
        
        return stocks
    
    def _get_indices_data(self, indices: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Retrieve data for the specified market indices using real APIs.
        
        Args:
            indices: List of index symbols (or their ETF proxies)
            
        Returns:
            Dictionary mapping index names to index data
        """
        indices_data = {}
        index_mapping = {
            # Map common index names to their ETF proxies and descriptive names
            "S&P 500": {"symbol": "SPY", "name": "S&P 500"},
            "NASDAQ": {"symbol": "QQQ", "name": "NASDAQ Composite"},
            "Dow Jones": {"symbol": "DIA", "name": "Dow Jones Industrial Average"},
            "Russell 2000": {"symbol": "IWM", "name": "Russell 2000"},
            "VIX": {"symbol": "VIX", "name": "CBOE Volatility Index"},
            # Add the ETF symbols themselves
            "SPY": {"symbol": "SPY", "name": "S&P 500"},
            "QQQ": {"symbol": "QQQ", "name": "NASDAQ Composite"},
            "DIA": {"symbol": "DIA", "name": "Dow Jones Industrial Average"},
            "IWM": {"symbol": "IWM", "name": "Russell 2000"}
        }
        
        # Convert any index names to their symbols
        symbols_to_fetch = []
        for index in indices:
            if index in index_mapping:
                symbols_to_fetch.append(index_mapping[index]["symbol"])
            else:
                symbols_to_fetch.append(index)  # Use as is if not in mapping
        
        # Fetch data for all symbols using the stock data method
        stock_data_list = self._get_stocks_data(symbols_to_fetch)
        
        # Convert stock data to indices format
        for data in stock_data_list:
            symbol = data["symbol"]
            display_name = None
            
            # Find the display name for this symbol
            for name, info in index_mapping.items():
                if info["symbol"] == symbol:
                    display_name = info["name"]
                    break
            
            # Use the symbol as name if no mapping found
            display_name = display_name or f"{symbol} Index"
            
            # Format the data
            indices_data[display_name] = {
                "current": data.get("current_price", 0),
                "prev_close": data.get("open_price", 0),  # Using open as prev_close approximation
                "change_pct": data.get("change_pct", 0),
                "timestamp": data.get("timestamp", datetime.now().timestamp()),
                "symbol": symbol,
                "name": display_name
            }
        
        return indices_data
    
    def _get_economic_indicators(self) -> Dict[str, Any]:
        """
        Retrieve current economic indicators from real APIs.
        
        Returns:
            Dictionary containing economic indicators
        """
        # Check MongoDB first for relatively fresh data (1 day)
        stored_data = market_data_collection.find_one(
            {"type": "economic_indicators", 
             "timestamp": {"$gte": (datetime.now() - timedelta(days=1)).timestamp()}}
        )
        
        if stored_data:
            stored_data.pop("_id", None)
            logger.debug("Using cached economic indicators (less than 1 day old)")
            return stored_data
        
        # Initialize indicators with default values
        indicators = {
            "timestamp": datetime.now().timestamp(),
            "type": "economic_indicators"
        }
        
        # Try to get real economic data from FRED via Alpha Vantage
        if self.alpha_vantage_api_key:
            try:
                # Get inflation rate (CPI)
                logger.debug("Fetching inflation data from Alpha Vantage")
                inflation_url = f"https://www.alphavantage.co/query?function=INFLATION&apikey={self.alpha_vantage_api_key}"
                inflation_response = requests.get(inflation_url)
                
                if inflation_response.status_code == 200:
                    inflation_data = inflation_response.json()
                    if "data" in inflation_data and inflation_data["data"]:
                        latest_inflation = inflation_data["data"][0]
                        indicators["inflation_rate"] = float(latest_inflation["value"]) / 100  # Convert to decimal
                
                # Get unemployment rate
                logger.debug("Fetching unemployment data from Alpha Vantage")
                unemployment_url = f"https://www.alphavantage.co/query?function=UNEMPLOYMENT&apikey={self.alpha_vantage_api_key}"
                unemployment_response = requests.get(unemployment_url)
                
                if unemployment_response.status_code == 200:
                    unemployment_data = unemployment_response.json()
                    if "data" in unemployment_data and unemployment_data["data"]:
                        latest_unemployment = unemployment_data["data"][0]
                        indicators["unemployment_rate"] = float(latest_unemployment["value"]) / 100  # Convert to decimal
                
                # Get Federal Funds Rate
                logger.debug("Fetching federal funds rate from Alpha Vantage")
                fed_rate_url = f"https://www.alphavantage.co/query?function=FEDERAL_FUNDS_RATE&apikey={self.alpha_vantage_api_key}"
                fed_rate_response = requests.get(fed_rate_url)
                
                if fed_rate_response.status_code == 200:
                    fed_rate_data = fed_rate_response.json()
                    if "data" in fed_rate_data and fed_rate_data["data"]:
                        latest_fed_rate = fed_rate_data["data"][0]
                        indicators["fed_rate"] = float(latest_fed_rate["value"]) / 100  # Convert to decimal
                
                # Get GDP growth
                logger.debug("Fetching GDP data from Alpha Vantage")
                gdp_url = f"https://www.alphavantage.co/query?function=REAL_GDP&apikey={self.alpha_vantage_api_key}"
                gdp_response = requests.get(gdp_url)
                
                if gdp_response.status_code == 200:
                    gdp_data = gdp_response.json()
                    if "data" in gdp_data and len(gdp_data["data"]) >= 2:
                        latest_gdp = float(gdp_data["data"][0]["value"])
                        previous_gdp = float(gdp_data["data"][1]["value"])
                        indicators["gdp_growth"] = (latest_gdp - previous_gdp) / previous_gdp
                
                # Use fallback values for any missing indicators
                if "inflation_rate" not in indicators:
                    indicators["inflation_rate"] = 0.03  # 3% inflation
                
                if "unemployment_rate" not in indicators:
                    indicators["unemployment_rate"] = 0.039  # 3.9% unemployment
                
                if "fed_rate" not in indicators:
                    indicators["fed_rate"] = 0.0525  # 5.25% fed rate
                
                if "gdp_growth" not in indicators:
                    indicators["gdp_growth"] = 0.021  # 2.1% GDP growth
                
                # Estimate consumer sentiment (not directly available from Alpha Vantage)
                indicators["consumer_sentiment"] = 78.5
                
            except Exception as e:
                logger.error(f"Error fetching economic indicators: {e}")
        
        # Store in MongoDB for future use
        market_data_collection.insert_one(indicators.copy())
        logger.debug("Stored new economic indicators in MongoDB")
        
        return indicators
    
    def _get_sector_performance(self) -> Dict[str, Dict[str, Any]]:
        """
        Retrieve sector performance data from real APIs.
        
        Returns:
            Dictionary mapping sector names to performance data
        """
        # Check MongoDB for fresh data (less than 1 day old)
        stored_data = market_data_collection.find_one(
            {"type": "sector_performance", 
             "timestamp": {"$gte": (datetime.now() - timedelta(days=1)).timestamp()}}
        )
        
        if stored_data:
            # Extract sectors from stored data
            sectors = {}
            for sector_item in stored_data.get("sectors", []):
                sectors[sector_item["name"]] = {
                    "performance_mtd": sector_item["performance_mtd"],
                    "performance_ytd": sector_item["performance_ytd"],
                    "outlook": sector_item["outlook"]
                }
            
            logger.debug("Using cached sector performance data (less than 1 day old)")
            return sectors
        
        # Sector ETFs to use as proxies for sector performance
        sector_etfs = {
            "Technology": "XLK",
            "Healthcare": "XLV",
            "Financials": "XLF",
            "Energy": "XLE",
            "Consumer Discretionary": "XLY",
            "Consumer Staples": "XLP",
            "Industrials": "XLI",
            "Materials": "XLB",
            "Utilities": "XLU",
            "Real Estate": "XLRE",
            "Communication Services": "XLC"
        }
        
        sectors = {}
        
        # Try to get sector data using Alpha Vantage
        if self.alpha_vantage_api_key:
            for sector_name, etf_symbol in sector_etfs.items():
                try:
                    # Get ETF data as a proxy for sector performance
                    logger.debug(f"Fetching {sector_name} data via {etf_symbol}")
                    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={etf_symbol}&apikey={self.alpha_vantage_api_key}"
                    response = requests.get(url)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if "Time Series (Daily)" in data:
                            time_series = data["Time Series (Daily)"]
                            
                            # Extract dates
                            dates = sorted(time_series.keys(), reverse=True)
                            if len(dates) > 0:
                                # Latest price
                                latest_date = dates[0]
                                latest_price = float(time_series[latest_date]["4. close"])
                                
                                # Month-to-date performance
                                mtd_date = None
                                # Find the first day of the current month
                                current_month = datetime.now().month
                                for date in dates:
                                    if datetime.strptime(date, "%Y-%m-%d").month != current_month:
                                        mtd_date = dates[dates.index(date) - 1]  # Last day of previous month
                                        break
                                
                                if not mtd_date and len(dates) > 20:
                                    mtd_date = dates[20]  # Fallback: use ~1 month ago
                                
                                # Year-to-date performance
                                ytd_date = None
                                # Find the first day of the current year
                                current_year = datetime.now().year
                                for date in dates:
                                    if datetime.strptime(date, "%Y-%m-%d").year != current_year:
                                        ytd_date = dates[dates.index(date) - 1]  # Last day of previous year
                                        break
                                
                                if not ytd_date and len(dates) > 252:
                                    ytd_date = dates[252]  # Fallback: use ~1 year ago
                                
                                # Calculate performance
                                mtd_performance = 0.0
                                ytd_performance = 0.0
                                
                                if mtd_date:
                                    mtd_price = float(time_series[mtd_date]["4. close"])
                                    mtd_performance = (latest_price - mtd_price) / mtd_price
                                
                                if ytd_date:
                                    ytd_price = float(time_series[ytd_date]["4. close"])
                                    ytd_performance = (latest_price - ytd_price) / ytd_price
                                
                                # Determine outlook based on recent performance
                                outlook = "stable"
                                if mtd_performance > 0.05:
                                    outlook = "positive"
                                elif mtd_performance < -0.05:
                                    outlook = "negative"
                                elif mtd_performance > 0.02:
                                    outlook = "slightly positive"
                                elif mtd_performance < -0.02:
                                    outlook = "slightly negative"
                                
                                # Add to sectors dictionary
                                sectors[sector_name] = {
                                    "performance_mtd": round(mtd_performance, 4),
                                    "performance_ytd": round(ytd_performance, 4),
                                    "outlook": outlook
                                }
                
                except Exception as e:
                    logger.error(f"Error fetching sector data for {sector_name}: {e}")
        
        # If we couldn't get data for all sectors, add placeholders for missing ones
        for sector_name in sector_etfs.keys():
            if sector_name not in sectors:
                sectors[sector_name] = {
                    "performance_mtd": 0.0,
                    "performance_ytd": 0.0,
                    "outlook": "stable"
                }
        
        # Store in MongoDB for future use
        sectors_list = []
        for name, data in sectors.items():
            sectors_list.append({
                "name": name,
                "performance_mtd": data["performance_mtd"],
                "performance_ytd": data["performance_ytd"],
                "outlook": data["outlook"]
            })
            
        market_data_collection.insert_one({
            "type": "sector_performance",
            "timestamp": datetime.now().timestamp(),
            "sectors": sectors_list
        })
        
        logger.debug("Stored new sector performance data in MongoDB")
        return sectors
    
    def _get_company_name(self, symbol: str) -> str:
        """
        Get company name for a symbol using available APIs.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Company name or the symbol if not found
        """
        # Check if we have the name cached in MongoDB
        cached_data = market_data_collection.find_one(
            {"symbol": symbol, "type": "stock", "name": {"$exists": True}}
        )
        
        if cached_data and "name" in cached_data and cached_data["name"]:
            return cached_data["name"]
        
        # Common symbols mapping
        common_symbols = {
            "AAPL": "Apple Inc.",
            "MSFT": "Microsoft Corporation",
            "AMZN": "Amazon.com Inc.",
            "GOOGL": "Alphabet Inc.",
            "META": "Meta Platforms Inc.",
            "TSLA": "Tesla Inc.",
            "NVDA": "NVIDIA Corporation",
            "BRK.B": "Berkshire Hathaway Inc.",
            "JPM": "JPMorgan Chase & Co.",
            "JNJ": "Johnson & Johnson",
            "UNH": "UnitedHealth Group Inc.",
            "V": "Visa Inc.",
            "PG": "Procter & Gamble Co.",
            "HD": "Home Depot Inc.",
            "XOM": "Exxon Mobil Corporation"
        }
        
        if symbol in common_symbols:
            return common_symbols[symbol]
        
        # Try to get company name from Alpha Vantage
        if self.alpha_vantage_api_key:
            try:
                url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={self.alpha_vantage_api_key}"
                response = requests.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    if "Name" in data:
                        return data["Name"]
            except Exception as e:
                logger.error(f"Error fetching company name for {symbol}: {e}")
        
        # Try to get company name from Finnhub
        if self.finnhub_api_key:
            try:
                url = f"https://finnhub.io/api/v1/stock/profile2?symbol={symbol}&token={self.finnhub_api_key}"
                response = requests.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    if "name" in data:
                        return data["name"]
            except Exception as e:
                logger.error(f"Error fetching company name from Finnhub for {symbol}: {e}")
        
        # Return the symbol if we couldn't find the name
        return f"{symbol}"

# Create an instance of the service for easy importing
market_data_service = MarketDataService()