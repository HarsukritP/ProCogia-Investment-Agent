import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
from loguru import logger

from ...database.redis import redis_client
from ...services.get.market_data import market_data_service
from ...services.get.news_sentiment import news_sentiment_service
from ...services.llm.openai_client import openai_client

class MarketAnalyzer:
    """Service for analyzing market conditions and trends."""
    
    def __init__(self):
        """Initialize the market analyzer service."""
        self.cache_expiry = 300  # Cache data for 5 minutes
    
    def analyze_market_conditions(self, market_data: Optional[Dict[str, Any]] = None, 
                                news_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze current market conditions and trends.
        
        Args:
            market_data: Current market data (optional, will be fetched if not provided)
            news_data: Recent market news and sentiment (optional, will be fetched if not provided)
            
        Returns:
            Dictionary containing market analysis
        """
        # Check cache first
        cache_key = f"market_analysis:{datetime.now().strftime('%Y-%m-%d-%H')}"
        cached_data = redis_client.get(cache_key)
        
        if cached_data:
            logger.debug(f"Using cached market analysis")
            return json.loads(cached_data)
        
        logger.info("Analyzing market conditions")
        
        # Fetch data if not provided
        if market_data is None:
            try:
                market_data = json.loads(market_data_service.get_market_data(
                    indices=["S&P 500", "NASDAQ", "Dow Jones", "Russell 2000", "VIX"]
                ))
            except Exception as e:
                logger.error(f"Error fetching market data: {e}")
                market_data = {}
        
        if news_data is None:
            try:
                news_data = json.loads(news_sentiment_service.get_market_news(
                    topics=["market", "economy", "federal reserve", "inflation"]
                ))
            except Exception as e:
                logger.error(f"Error fetching news data: {e}")
                news_data = {}
        
        # Try to use OpenAI for more sophisticated analysis
        try:
            logger.debug("Attempting to use OpenAI for market analysis")
            combined_data = {
                "market_data": market_data,
                "news_data": news_data,
                "timestamp": datetime.now().isoformat()
            }
            
            system_prompt = """
            You are an expert financial market analyst.
            Analyze the provided market data and news to generate a comprehensive market assessment.
            Your analysis should cover market indices performance, sector trends, economic indicators, and news sentiment.
            
            Return a valid JSON object with these sections:
            1. market_summary: Brief overview of current market conditions
            2. indices_analysis: Analysis of major indices performance 
            3. sector_analysis: Insights on sector performance and rotation
            4. economic_analysis: Assessment of economic indicators
            5. sentiment_analysis: Analysis of news sentiment and impact
            6. market_outlook: Short-term and medium-term market outlook
            7. key_drivers: Main factors currently driving markets
            8. risk_factors: Current market risks to monitor
            
            Your analysis should be data-driven, balanced, and avoid excessive speculation.
            Return ONLY valid JSON with no markdown formatting or explanation.
            """
            
            response = openai_client.generate_response(
                [{"role": "user", "content": json.dumps(combined_data)}],
                system_prompt=system_prompt
            )
            
            try:
                # Try to parse JSON from response
                result = json.loads(response)
                
                # Add timestamp
                result["timestamp"] = datetime.now().isoformat()
                result["analysis_type"] = "ai"
                
                # Cache the result
                redis_client.setex(cache_key, self.cache_expiry, json.dumps(result))
                logger.debug("Cached AI-based market analysis")
                
                return result
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract JSON portion
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                
                if json_start >= 0 and json_end > json_start:
                    try:
                        json_content = response[json_start:json_end]
                        result = json.loads(json_content)
                        
                        # Add timestamp
                        result["timestamp"] = datetime.now().isoformat()
                        result["analysis_type"] = "ai"
                        
                        # Cache the result
                        redis_client.setex(cache_key, self.cache_expiry, json.dumps(result))
                        logger.debug("Cached AI-based market analysis (extracted from text)")
                        
                        return result
                    except json.JSONDecodeError:
                        logger.warning("Failed to extract JSON from OpenAI response")
        
        except Exception as e:
            logger.error(f"Error using OpenAI for market analysis: {e}")
        
        # Fall back to rule-based analysis
        logger.debug("Using rule-based market analysis")
        
        # Analyze market indices
        indices_analysis = self._analyze_indices(market_data.get("indices", {}))
        
        # Analyze sectors
        sectors_analysis = self._analyze_sectors(market_data.get("sectors", {}))
        
        # Analyze economic indicators
        economic_analysis = self._analyze_economic_indicators(market_data.get("economic_indicators", {}))
        
        # Analyze news sentiment
        sentiment_analysis = self._analyze_news_sentiment(news_data)
        
        # Determine overall market outlook
        market_outlook = self._determine_market_outlook(
            indices_analysis, sectors_analysis, economic_analysis, sentiment_analysis
        )
        
        # Identify key market drivers
        key_drivers = self._identify_key_drivers(
            indices_analysis, sectors_analysis, economic_analysis, sentiment_analysis
        )
        
        # Identify risk factors
        risk_factors = self._identify_risk_factors(
            indices_analysis, sectors_analysis, economic_analysis, sentiment_analysis
        )
        
        # Create market summary
        market_summary = self._create_market_summary(
            indices_analysis, sectors_analysis, economic_analysis, sentiment_analysis, market_outlook
        )
        
        # Prepare result
        result = {
            "timestamp": datetime.now().isoformat(),
            "analysis_type": "rule-based",
            "market_summary": market_summary,
            "indices_analysis": indices_analysis,
            "sector_analysis": sectors_analysis,
            "economic_analysis": economic_analysis,
            "sentiment_analysis": sentiment_analysis,
            "market_outlook": market_outlook,
            "key_drivers": key_drivers,
            "risk_factors": risk_factors
        }
        
        # Cache the result
        redis_client.setex(cache_key, self.cache_expiry, json.dumps(result))
        logger.debug("Cached rule-based market analysis")
        
        return result
    
    def _analyze_indices(self, indices_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze market indices performance.
        
        Args:
            indices_data: Market indices data
            
        Returns:
            Dictionary containing indices analysis
        """
        # Calculate average performance
        avg_change = 0
        positive_count = 0
        negative_count = 0
        
        for name, data in indices_data.items():
            change_pct = data.get("change_pct", 0)
            avg_change += change_pct
            
            if change_pct > 0:
                positive_count += 1
            elif change_pct < 0:
                negative_count += 0
        
        if indices_data:
            avg_change /= len(indices_data)
        
        # Determine market breadth
        market_breadth = "neutral"
        if positive_count > 2 * negative_count and len(indices_data) >= 3:
            market_breadth = "strongly positive"
        elif positive_count > negative_count:
            market_breadth = "positive"
        elif negative_count > 2 * positive_count and len(indices_data) >= 3:
            market_breadth = "strongly negative"
        elif negative_count > positive_count:
            market_breadth = "negative"
        
        # Check for significant moves
        significant_moves = []
        for name, data in indices_data.items():
            change_pct = data.get("change_pct", 0)
            
            # Consider > 1% move significant for major indices
            if abs(change_pct) > 1:
                significant_moves.append({
                    "index": name,
                    "change_pct": change_pct,
                    "direction": "up" if change_pct > 0 else "down"
                })
        
        # Get historical context (simplified for this implementation)
        historical_performance = {
            "one_week": avg_change * 5 * 0.8,  # Approximation
            "one_month": avg_change * 20 * 0.6,  # Dampened effect over time
            "ytd": 0.08 if avg_change > 0 else -0.04  # Simplified approximation
        }
        
        # Determine market trend
        trend = "neutral"
        if avg_change > 0.5:
            trend = "strongly bullish"
        elif avg_change > 0.1:
            trend = "bullish"
        elif avg_change < -0.5:
            trend = "strongly bearish"
        elif avg_change < -0.1:
            trend = "bearish"
        
        return {
            "average_change": round(avg_change, 4),
            "market_breadth": market_breadth,
            "significant_moves": significant_moves,
            "historical_performance": historical_performance,
            "trend": trend,
            "vix_level": indices_data.get("VIX", {}).get("current", 20) if "VIX" in indices_data else 20
        }
    
    def _analyze_sectors(self, sectors_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze sector performance and rotation.
        
        Args:
            sectors_data: Market sector data
            
        Returns:
            Dictionary containing sector analysis
        """
        if not sectors_data:
            return {
                "top_sectors": [],
                "bottom_sectors": [],
                "sector_rotation": "unknown",
                "market_sentiment": "unknown"
            }
        
        # Sort sectors by monthly performance
        sorted_sectors_mtd = sorted(
            [(name, data.get("performance_mtd", 0)) for name, data in sectors_data.items()],
            key=lambda x: x[1],
            reverse=True
        )
        
        # Sort sectors by YTD performance
        sorted_sectors_ytd = sorted(
            [(name, data.get("performance_ytd", 0)) for name, data in sectors_data.items()],
            key=lambda x: x[1],
            reverse=True
        )
        
        # Identify leadership shifts
        leadership_shifts = []
        for i, (sector, _) in enumerate(sorted_sectors_mtd[:3]):
            ytd_rank = next((i for i, (s, _) in enumerate(sorted_sectors_ytd) if s == sector), -1)
            
            if ytd_rank > 2:  # A sector moved from outside top 3 YTD into top 3 MTD
                leadership_shifts.append({
                    "sector": sector,
                    "prior_rank": ytd_rank + 1,
                    "current_rank": i + 1,
                    "mtd_performance": sectors_data[sector].get("performance_mtd", 0)
                })
        
        # Check for weakness in previous leaders
        for i, (sector, _) in enumerate(sorted_sectors_ytd[:3]):
            mtd_rank = next((i for i, (s, _) in enumerate(sorted_sectors_mtd) if s == sector), -1)
            
            if mtd_rank > 2:  # A previous leader dropped below top 3 MTD
                leadership_shifts.append({
                    "sector": sector,
                    "prior_rank": i + 1,
                    "current_rank": mtd_rank + 1,
                    "mtd_performance": sectors_data[sector].get("performance_mtd", 0)
                })
        
        # Calculate sector divergence (difference between best and worst performers)
        best_mtd = sorted_sectors_mtd[0][1] if sorted_sectors_mtd else 0
        worst_mtd = sorted_sectors_mtd[-1][1] if sorted_sectors_mtd else 0
        sector_divergence = best_mtd - worst_mtd
        
        # Determine if there's sector rotation
        sector_rotation = "minimal"
        if len(leadership_shifts) >= 2:
            sector_rotation = "significant"
        elif len(leadership_shifts) == 1:
            sector_rotation = "moderate"
        
        # Determine broad sentiment based on sector performance
        defensive_sectors = ["Utilities", "Consumer Staples", "Healthcare"]
        cyclical_sectors = ["Technology", "Consumer Discretionary", "Industrials", "Financials"]
        
        defensive_perf = np.mean([sectors_data.get(name, {}).get("performance_mtd", 0) 
                               for name in defensive_sectors if name in sectors_data])
        
        cyclical_perf = np.mean([sectors_data.get(name, {}).get("performance_mtd", 0) 
                               for name in cyclical_sectors if name in sectors_data])
        
        market_sentiment = "balanced"
        if cyclical_perf > defensive_perf + 0.01 and not np.isnan(cyclical_perf) and not np.isnan(defensive_perf):
            market_sentiment = "risk-on"
        elif defensive_perf > cyclical_perf + 0.01 and not np.isnan(cyclical_perf) and not np.isnan(defensive_perf):
            market_sentiment = "risk-off"
        
        # Format top and bottom sectors
        top_sectors = [{"name": name, "performance": round(perf * 100, 2)} 
                     for name, perf in sorted_sectors_mtd[:3] if not np.isnan(perf)]
        
        bottom_sectors = [{"name": name, "performance": round(perf * 100, 2)} 
                       for name, perf in sorted_sectors_mtd[-3:] if not np.isnan(perf)]
        
        return {
            "top_sectors": top_sectors,
            "bottom_sectors": bottom_sectors,
            "leadership_shifts": leadership_shifts,
            "sector_divergence": round(sector_divergence * 100, 2),
            "sector_rotation": sector_rotation,
            "market_sentiment": market_sentiment
        }
    
    def _analyze_economic_indicators(self, economic_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze economic indicators.
        
        Args:
            economic_data: Economic indicator data
            
        Returns:
            Dictionary containing economic analysis
        """
        if not economic_data:
            return {
                "inflation_status": "unknown",
                "unemployment_status": "unknown",
                "interest_rate_status": "unknown",
                "growth_status": "unknown",
                "policy_trajectory": "unknown",
                "recession_risk": "unknown"
            }
        
        # Analyze inflation
        inflation_rate = economic_data.get("inflation_rate", 0.03)
        inflation_status = "high"
        if inflation_rate < 0.02:
            inflation_status = "low"
        elif inflation_rate < 0.035:
            inflation_status = "moderate"
        
        # Analyze unemployment
        unemployment_rate = economic_data.get("unemployment_rate", 0.04)
        unemployment_status = "high"
        if unemployment_rate < 0.035:
            unemployment_status = "low"
        elif unemployment_rate < 0.05:
            unemployment_status = "moderate"
        
        # Analyze interest rates
        fed_rate = economic_data.get("fed_rate", 0.05)
        rate_status = "restrictive"
        if fed_rate < 0.03:
            rate_status = "accommodative"
        elif fed_rate < 0.045:
            rate_status = "neutral"
        
        # Analyze GDP growth
        gdp_growth = economic_data.get("gdp_growth", 0.02)
        growth_status = "strong"
        if gdp_growth < 0.015:
            growth_status = "weak"
        elif gdp_growth < 0.025:
            growth_status = "moderate"
        
        # Analyze consumer sentiment
        consumer_sentiment = economic_data.get("consumer_sentiment", 75)
        sentiment_status = "positive"
        if consumer_sentiment < 65:
            sentiment_status = "negative"
        elif consumer_sentiment < 80:
            sentiment_status = "neutral"
        
        # Determine policy trajectory
        policy_trajectory = "neutral"
        
        # High inflation + low unemployment = tightening bias
        if inflation_status in ["high", "moderate"] and unemployment_status == "low":
            policy_trajectory = "tightening"
        
        # Low inflation + high unemployment = easing bias
        elif inflation_status == "low" and unemployment_status in ["high", "moderate"]:
            policy_trajectory = "easing"
        
        # High inflation + high unemployment = stagflation concerns
        elif inflation_status == "high" and unemployment_status == "high":
            policy_trajectory = "stagflation concerns"
        
        # Determine recession risk
        recession_risk = "low"
        if gdp_growth < 0.01 and unemployment_status == "high":
            recession_risk = "high"
        elif gdp_growth < 0.02 and unemployment_status == "moderate":
            recession_risk = "moderate"
        
        return {
            "inflation": {
                "rate": inflation_rate,
                "status": inflation_status
            },
            "unemployment": {
                "rate": unemployment_rate,
                "status": unemployment_status
            },
            "interest_rates": {
                "fed_rate": fed_rate,
                "status": rate_status
            },
            "gdp_growth": {
                "rate": gdp_growth,
                "status": growth_status
            },
            "consumer_sentiment": {
                "value": consumer_sentiment,
                "status": sentiment_status
            },
            "policy_trajectory": policy_trajectory,
            "recession_risk": recession_risk
        }
    
    def _analyze_news_sentiment(self, news_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze news sentiment and its potential market impact.
        
        Args:
            news_data: News and sentiment data
            
        Returns:
            Dictionary containing sentiment analysis
        """
        if not news_data:
            return {
                "overall_sentiment": "neutral",
                "primary_topics": [],
                "potential_impact": "unknown"
            }
        
        # Extract sentiment distribution
        sentiment_distribution = news_data.get("analysis", {}).get("sentiment_distribution", {})
        
        # Extract impact distribution
        impact_distribution = news_data.get("analysis", {}).get("impact_distribution", {})
        
        # Extract primary topics
        primary_topics = news_data.get("analysis", {}).get("primary_topics", [])
        
        # Calculate overall sentiment
        overall_sentiment = news_data.get("analysis", {}).get("overall_sentiment", "neutral")
        
        # Calculate potential market impact
        potential_impact = "moderate"
        
        # If high-impact news with strong sentiment, the impact is high
        high_impact_count = impact_distribution.get("high", 0)
        high_sentiment_count = max(sentiment_distribution.get("positive", 0), 
                                 sentiment_distribution.get("negative", 0))
        
        if high_impact_count > 2 and high_sentiment_count > high_impact_count / 2:
            potential_impact = "high"
        elif high_impact_count == 0 and high_sentiment_count == 0:
            potential_impact = "low"
        
        # Extract key news items (high impact)
        key_news = []
        if "news_items" in news_data:
            for item in news_data["news_items"]:
                if item.get("impact") == "high":
                    key_news.append({
                        "title": item.get("title", ""),
                        "sentiment": item.get("sentiment", "neutral"),
                        "source": item.get("source", "")
                    })
        
        return {
            "overall_sentiment": overall_sentiment,
            "sentiment_distribution": sentiment_distribution,
            "impact_distribution": impact_distribution,
            "primary_topics": primary_topics[:5] if primary_topics else [],
            "potential_impact": potential_impact,
            "key_news": key_news[:3]  # Include top 3 key news items
        }
    
    def _determine_market_outlook(self, indices_analysis: Dict[str, Any],
                                economic_analysis: Dict[str, Any],
                                sectors_analysis: Dict[str, Any],
                                sentiment_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine overall market outlook based on all analyses.
        
        Args:
            indices_analysis: Analysis of market indices
            economic_analysis: Analysis of economic indicators
            sectors_analysis: Analysis of sector performance
            sentiment_analysis: Analysis of news sentiment
            
        Returns:
            Dictionary with market outlook
        """
        # Short-term outlook (1-3 months)
        short_term_factors = []
        
        # Market trend contribution (highest weight)
        trend_score = 0
        trend = indices_analysis.get("trend", "neutral")
        if trend == "strongly bullish":
            trend_score = 2
            short_term_factors.append("Strong positive market momentum")
        elif trend == "bullish":
            trend_score = 1
            short_term_factors.append("Positive market momentum")
        elif trend == "strongly bearish":
            trend_score = -2
            short_term_factors.append("Strong negative market momentum")
        elif trend == "bearish":
            trend_score = -1
            short_term_factors.append("Negative market momentum")
        
        # Sentiment contribution
        sentiment_score = 0
        overall_sentiment = sentiment_analysis.get("overall_sentiment", "neutral")
        if "strongly positive" in overall_sentiment:
            sentiment_score = 1.5
            short_term_factors.append("Very positive market sentiment")
        elif "positive" in overall_sentiment:
            sentiment_score = 1
            short_term_factors.append("Positive market sentiment")
        elif "strongly negative" in overall_sentiment:
            sentiment_score = -1.5
            short_term_factors.append("Very negative market sentiment")
        elif "negative" in overall_sentiment:
            sentiment_score = -1
            short_term_factors.append("Negative market sentiment")
        
        # VIX contribution (volatility)
        vix_score = 0
        vix = indices_analysis.get("vix_level", 20)
        if vix > 30:
            vix_score = -1
            short_term_factors.append("Elevated market volatility (VIX)")
        elif vix < 15:
            vix_score = 0.5
            short_term_factors.append("Low market volatility (VIX)")
        
        # Calculate short-term score (weighted)
        short_term_score = 0.5 * trend_score + 0.3 * sentiment_score + 0.2 * vix_score
        
        # Determine short-term outlook
        short_term_outlook = "neutral"
        if short_term_score > 1:
            short_term_outlook = "strongly bullish"
        elif short_term_score > 0.3:
            short_term_outlook = "bullish"
        elif short_term_score < -1:
            short_term_outlook = "strongly bearish"
        elif short_term_score < -0.3:
            short_term_outlook = "bearish"
        
        # Medium-term outlook (6-12 months)
        medium_term_factors = []
        
        # Economic indicators contribution
        economic_score = 0
        
        # GDP growth
        gdp_status = economic_analysis.get("gdp_growth", {}).get("status", "moderate")
        if gdp_status == "strong":
            economic_score += 1
            medium_term_factors.append("Strong economic growth")
        elif gdp_status == "weak":
            economic_score -= 1
            medium_term_factors.append("Weak economic growth")
        
        # Inflation
        inflation_status = economic_analysis.get("inflation", {}).get("status", "moderate")
        if inflation_status == "high":
            economic_score -= 0.5
            medium_term_factors.append("High inflation")
        elif inflation_status == "low":
            economic_score += 0.5
            medium_term_factors.append("Low inflation")
        
        # Interest rates
        rate_status = economic_analysis.get("interest_rates", {}).get("status", "neutral")
        if rate_status == "restrictive":
            economic_score -= 0.5
            medium_term_factors.append("Restrictive monetary policy")
        elif rate_status == "accommodative":
            economic_score += 0.5
            medium_term_factors.append("Accommodative monetary policy")
        
        # Policy trajectory
        policy = economic_analysis.get("policy_trajectory", "neutral")
        if policy == "easing":
            economic_score += 1
            medium_term_factors.append("Easing policy trajectory")
        elif policy == "tightening":
            economic_score -= 1
            medium_term_factors.append("Tightening policy trajectory")
        elif policy == "stagflation concerns":
            economic_score -= 1.5
            medium_term_factors.append("Stagflation concerns")
        
        # Recession risk
        recession_risk = economic_analysis.get("recession_risk", "low")
        if recession_risk == "high":
            economic_score -= 1.5
            medium_term_factors.append("High recession risk")
        elif recession_risk == "moderate":
            economic_score -= 0.5
            medium_term_factors.append("Moderate recession risk")
        
        # Sector rotation contribution
        rotation_score = 0
        rotation = sectors_analysis.get("sector_rotation", "minimal")
        
        if rotation == "significant":
            # Check if rotation is toward cyclicals (positive) or defensives (negative)
            sentiment = sectors_analysis.get("market_sentiment", "balanced")
            if sentiment == "risk-on":
                rotation_score = 0.5
                medium_term_factors.append("Rotation toward cyclical sectors")
            elif sentiment == "risk-off":
                rotation_score = -0.5
                medium_term_factors.append("Rotation toward defensive sectors")
        
        # Calculate medium-term score (weighted)
        medium_term_score = 0.6 * economic_score + 0.2 * rotation_score + 0.2 * (trend_score / 2)
        
        # Determine medium-term outlook
        medium_term_outlook = "neutral"
        if medium_term_score > 1:
            medium_term_outlook = "strongly bullish"
        elif medium_term_score > 0.3:
            medium_term_outlook = "bullish"
        elif medium_term_score < -1:
            medium_term_outlook = "strongly bearish"
        elif medium_term_score < -0.3:
            medium_term_outlook = "bearish"
        
        return {
            "short_term": {
                "outlook": short_term_outlook,
                "score": round(short_term_score, 2),
                "key_factors": short_term_factors
            },
            "medium_term": {
                "outlook": medium_term_outlook,
                "score": round(medium_term_score, 2),
                "key_factors": medium_term_factors
            }
        }
    
    def _identify_key_drivers(self, indices_analysis: Dict[str, Any],
                            sectors_analysis: Dict[str, Any],
                            economic_analysis: Dict[str, Any],
                            sentiment_analysis: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Identify key market drivers based on analyses.
        
        Args:
            indices_analysis: Analysis of market indices
            sectors_analysis: Analysis of sector performance
            economic_analysis: Analysis of economic indicators
            sentiment_analysis: Analysis of news sentiment
            
        Returns:
            List of key market drivers
        """
        drivers = []
        
        # Check for significant index moves
        for move in indices_analysis.get("significant_moves", []):
            drivers.append({
                "factor": f"{move['index']} {move['direction']} {abs(move['change_pct'])}%",
                "impact": "positive" if move["direction"] == "up" else "negative",
                "category": "market"
            })
        
        # Check for economic factors
        if economic_analysis:
            # Inflation
            inflation = economic_analysis.get("inflation", {})
            if inflation.get("status") == "high":
                drivers.append({
                    "factor": f"High inflation ({inflation.get('rate', 0) * 100:.1f}%)",
                    "impact": "negative",
                    "category": "economic"
                })
            elif inflation.get("status") == "low":
                drivers.append({
                    "factor": f"Low inflation ({inflation.get('rate', 0) * 100:.1f}%)",
                    "impact": "positive",
                    "category": "economic"
                })
            
            # Interest rates
            rates = economic_analysis.get("interest_rates", {})
            if rates.get("status") == "restrictive":
                drivers.append({
                    "factor": f"Restrictive monetary policy (Fed rate: {rates.get('fed_rate', 0) * 100:.2f}%)",
                    "impact": "negative",
                    "category": "economic"
                })
            elif rates.get("status") == "accommodative":
                drivers.append({
                    "factor": f"Accommodative monetary policy (Fed rate: {rates.get('fed_rate', 0) * 100:.2f}%)",
                    "impact": "positive",
                    "category": "economic"
                })
            
            # Growth
            growth = economic_analysis.get("gdp_growth", {})
            if growth.get("status") == "strong":
                drivers.append({
                    "factor": f"Strong economic growth (GDP: {growth.get('rate', 0) * 100:.1f}%)",
                    "impact": "positive",
                    "category": "economic"
                })
            elif growth.get("status") == "weak":
                drivers.append({
                    "factor": f"Weak economic growth (GDP: {growth.get('rate', 0) * 100:.1f}%)",
                    "impact": "negative",
                    "category": "economic"
                })
        
        # Check for sector leadership
        if sectors_analysis and "top_sectors" in sectors_analysis:
            for sector in sectors_analysis["top_sectors"][:1]:  # Just the top sector
                drivers.append({
                    "factor": f"Strong {sector['name']} sector performance ({sector['performance']}%)",
                    "impact": "positive",
                    "category": "sector"
                })
        
        # Check for sentiment factors
        if sentiment_analysis:
            sentiment = sentiment_analysis.get("overall_sentiment", "neutral")
            
            if "positive" in sentiment:
                drivers.append({
                    "factor": f"{sentiment.title()} market sentiment",
                    "impact": "positive",
                    "category": "sentiment"
                })
            elif "negative" in sentiment:
                drivers.append({
                    "factor": f"{sentiment.title()} market sentiment",
                    "impact": "negative", 
                    "category": "sentiment"
                })
            
            # Add key news items
            for news in sentiment_analysis.get("key_news", [])[:1]:  # Just the top news
                impact = "positive" if news.get("sentiment") == "positive" else "negative" if news.get("sentiment") == "negative" else "neutral"
                drivers.append({
                    "factor": news.get("title", ""),
                    "impact": impact,
                    "category": "news"
                })
        
        return drivers[:5]  # Return top 5 drivers
    
    def _identify_risk_factors(self, indices_analysis: Dict[str, Any],
                             sectors_analysis: Dict[str, Any],
                             economic_analysis: Dict[str, Any],
                             sentiment_analysis: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Identify current market risk factors.
        
        Args:
            indices_analysis: Analysis of market indices
            sectors_analysis: Analysis of sector performance
            economic_analysis: Analysis of economic indicators
            sentiment_analysis: Analysis of news sentiment
            
        Returns:
            List of risk factors
        """
        risks = []
        
        # Check volatility (VIX)
        vix = indices_analysis.get("vix_level", 20)
        if vix > 25:
            risks.append({
                "factor": f"Elevated market volatility (VIX: {vix})",
                "severity": "high" if vix > 30 else "medium",
                "category": "market"
            })
        
        # Check economic risks
        if economic_analysis:
            # Recession risk
            recession_risk = economic_analysis.get("recession_risk", "low")
            if recession_risk != "low":
                risks.append({
                    "factor": f"{recession_risk.title()} recession risk",
                    "severity": recession_risk,
                    "category": "economic"
                })
            
            # Inflation risk
            inflation = economic_analysis.get("inflation", {})
            if inflation.get("status") == "high":
                risks.append({
                    "factor": f"Persistent inflation ({inflation.get('rate', 0) * 100:.1f}%)",
                    "severity": "high" if inflation.get("rate", 0) > 0.04 else "medium",
                    "category": "economic"
                })
            
            # Policy trajectory
            policy = economic_analysis.get("policy_trajectory", "neutral")
            if policy == "tightening":
                risks.append({
                    "factor": "Monetary policy tightening",
                    "severity": "medium",
                    "category": "policy"
                })
            elif policy == "stagflation concerns":
                risks.append({
                    "factor": "Stagflation concerns",
                    "severity": "high",
                    "category": "economic"
                })
        
        # Check sentiment risks
        if sentiment_analysis:
            sentiment = sentiment_analysis.get("overall_sentiment", "neutral")
            if "negative" in sentiment:
                risks.append({
                    "factor": f"{sentiment.title()} market sentiment",
                    "severity": "high" if "strongly" in sentiment else "medium",
                    "category": "sentiment"
                })
            
            # Check for negative news in primary topics
            for topic in sentiment_analysis.get("primary_topics", [])[:2]:  # Top 2 topics
                if type(topic) == dict and "topic" in topic:
                    topic_name = topic["topic"]
                    if topic_name in ["recession", "inflation", "interest rates", "federal reserve"]:
                        risks.append({
                            "factor": f"Heightened focus on {topic_name}",
                            "severity": "medium",
                            "category": "sentiment"
                        })
        
        # Check sector risks
        if sectors_analysis:
            rotation = sectors_analysis.get("sector_rotation", "minimal")
            if rotation != "minimal":
                risks.append({
                    ""factor": f"{rotation.title()} sector rotation",
                    "severity": "medium",
                    "category": "market"
                })
            
            # Check for defensive shift
            sentiment = sectors_analysis.get("market_sentiment", "balanced")
            if sentiment == "risk-off":
                risks.append({
                    "factor": "Rotation toward defensive sectors",
                    "severity": "medium",
                    "category": "market"
                })
            
            # Check sector divergence
            divergence = sectors_analysis.get("sector_divergence", 0)
            if divergence > 10:  # More than 10% difference
                risks.append({
                    "factor": f"High sector performance divergence ({divergence:.1f}%)",
                    "severity": "medium",
                    "category": "market"
                })
        
        return risks[:5]  # Return top 5 risk factors
    
    def _create_market_summary(self, indices_analysis: Dict[str, Any],
                             sectors_analysis: Dict[str, Any],
                             economic_analysis: Dict[str, Any],
                             sentiment_analysis: Dict[str, Any],
                             market_outlook: Dict[str, Any]) -> str:
        """
        Create a concise market summary based on analyses.
        
        Args:
            indices_analysis: Analysis of market indices
            sectors_analysis: Analysis of sector performance
            economic_analysis: Analysis of economic indicators
            sentiment_analysis: Analysis of news sentiment
            market_outlook: Market outlook assessment
            
        Returns:
            Market summary text
        """
        # Build summary components
        summary_parts = []
        
        # Market direction
        trend = indices_analysis.get("trend", "neutral")
        if trend != "neutral":
            trend_text = trend.replace("strongly ", "very ") if "strongly" in trend else trend
            summary_parts.append(f"Markets are {trend_text}")
        else:
            summary_parts.append("Markets are range-bound")
        
        # Economic context
        econ_factors = []
        
        if economic_analysis:
            # Growth
            growth = economic_analysis.get("gdp_growth", {}).get("status", "moderate")
            if growth != "moderate":
                econ_factors.append(f"{growth} economic growth")
            
            # Inflation
            inflation = economic_analysis.get("inflation", {}).get("status", "moderate")
            if inflation != "moderate":
                econ_factors.append(f"{inflation} inflation")
            
            # Interest rates
            rates = economic_analysis.get("interest_rates", {}).get("status", "neutral")
            if rates != "neutral":
                econ_factors.append(f"{rates} monetary policy")
        
        if econ_factors:
            summary_parts.append("with " + ", ".join(econ_factors))
        
        # Sector performance
        if sectors_analysis and "top_sectors" in sectors_analysis and sectors_analysis["top_sectors"]:
            top_sector = sectors_analysis["top_sectors"][0]["name"]
            summary_parts.append(f"led by {top_sector}")
        
        # Sentiment
        sentiment = sentiment_analysis.get("overall_sentiment", "neutral")
        if sentiment != "neutral":
            summary_parts.append(f"amid {sentiment} investor sentiment")
        
        # Outlook
        short_term = market_outlook.get("short_term", {}).get("outlook", "neutral")
        medium_term = market_outlook.get("medium_term", {}).get("outlook", "neutral")
        
        if short_term != "neutral" or medium_term != "neutral":
            outlook_text = ""
            if short_term != "neutral":
                outlook_text += f"{short_term} short-term"
            
            if medium_term != "neutral":
                if outlook_text:
                    outlook_text += f" and {medium_term} medium-term"
                else:
                    outlook_text += f"{medium_term} medium-term"
            
            outlook_text += " outlook"
            summary_parts.append(f"with a {outlook_text}")
        
        # Join all parts
        summary = ". ".join(part.capitalize() for part in summary_parts)
        if not summary.endswith("."):
            summary += "."
        
        return summary

# Create an instance of the service for easy importing
market_analyzer = MarketAnalyzer()