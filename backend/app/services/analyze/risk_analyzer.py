import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime
from loguru import logger

from ...database.redis import redis_client
from ...services.get.market_data import market_data_service
import json

class RiskAnalyzer:
    """Service for analyzing portfolio risk."""
    
    def __init__(self):
        """Initialize the risk analyzer service."""
        self.cache_expiry = 300  # Cache data for 5 minutes
    
    def analyze_portfolio_risk(self, portfolio_data: Dict[str, Any], 
                             risk_threshold: float = 0.5) -> Dict[str, Any]:
        """
        Analyze the current portfolio risk profile.
        
        Args:
            portfolio_data: Portfolio information
            risk_threshold: Threshold above which to flag high risk assets
        
        Returns:
            Dictionary containing risk analysis
        """
        # Check cache first
        portfolio_id = portfolio_data.get("id", "unknown")
        cache_key = f"risk_analysis:{portfolio_id}:{risk_threshold}"
        cached_data = redis_client.get(cache_key)
        
        if cached_data:
            logger.debug(f"Using cached risk analysis for portfolio {portfolio_id}")
            return json.loads(cached_data)
        
        logger.info(f"Analyzing risk for portfolio {portfolio_id}")
        
        # Extract assets from portfolio data
        assets = portfolio_data.get("assets", [])
        
        if not assets:
            logger.warning(f"No assets found in portfolio {portfolio_id}")
            return {
                "error": "No assets found in portfolio",
                "timestamp": datetime.now().isoformat()
            }
        
        # Calculate asset values and total portfolio value
        assets_with_values = []
        for asset in assets:
            if "quantity" in asset and "current_price" in asset:
                asset_value = asset["quantity"] * asset["current_price"]
                asset_with_value = asset.copy()
                asset_with_value["value"] = asset_value
                assets_with_values.append(asset_with_value)
        
        # Calculate total portfolio value
        total_value = sum(asset["value"] for asset in assets_with_values)
        
        if total_value == 0:
            logger.warning(f"Portfolio {portfolio_id} has zero total value")
            return {
                "error": "Portfolio has zero total value",
                "timestamp": datetime.now().isoformat()
            }
        
        # Group assets by type
        asset_groups = {}
        for asset in assets_with_values:
            asset_type = asset.get("asset_type", "unknown")
            if asset_type not in asset_groups:
                asset_groups[asset_type] = []
            asset_groups[asset_type].append(asset)
        
        # Calculate values and allocation by asset type
        asset_type_values = {}
        asset_type_allocations = {}
        
        for asset_type, assets_list in asset_groups.items():
            type_value = sum(asset["value"] for asset in assets_list)
            asset_type_values[asset_type] = type_value
            asset_type_allocations[asset_type] = type_value / total_value
        
        # Calculate sector concentrations
        sectors = {
            "Technology": ["AAPL", "MSFT", "GOOGL", "META", "NVDA", "CSCO", "ADBE", "ORCL", "CRM", "INTC"],
            "E-commerce": ["AMZN", "EBAY", "ETSY", "BABA", "JD", "SHOP", "MELI"],
            "Financial": ["BRK.B", "JPM", "V", "MA", "BAC", "GS", "MS", "AXP", "C", "WFC"],
            "Healthcare": ["JNJ", "UNH", "PFE", "MRK", "ABT", "TMO", "LLY", "DHR", "BMY", "AMGN"],
            "Consumer": ["PG", "KO", "PEP", "WMT", "COST", "NKE", "MCD", "SBUX", "DIS", "HD"],
            "Energy": ["XOM", "CVX", "COP", "SLB", "EOG", "OXY", "PSX", "VLO", "MPC", "KMI"],
            "Industrials": ["HON", "UNP", "UPS", "BA", "CAT", "DE", "GE", "MMM", "LMT", "RTX"],
            "Utilities": ["NEE", "DUK", "SO", "D", "AEP", "XEL", "SRE", "ED", "EXC", "WEC"],
            "Real Estate": ["AMT", "PLD", "CCI", "SPG", "PSA", "EQIX", "DLR", "O", "WELL", "AVB"],
            "Telecom": ["T", "VZ", "TMUS", "CMCSA", "CHTR", "LUMN", "T-CA", "BCE", "RCI", "TU"]
        }
        
        sector_values = {}
        sector_allocations = {}
        
        # Only consider equity assets for sector analysis
        equity_assets = asset_groups.get("equity", [])
        equity_value = sum(asset["value"] for asset in equity_assets)
        
        for sector, symbols in sectors.items():
            sector_assets = [asset for asset in equity_assets if asset.get("symbol", "") in symbols]
            sector_value = sum(asset["value"] for asset in sector_assets)
            sector_values[sector] = sector_value
            
            # Allocation as percentage of total portfolio
            sector_allocations[sector] = sector_value / total_value if total_value > 0 else 0
        
        # Calculate volatility metrics (real values if possible, otherwise estimates)
        volatility_metrics = self._calculate_volatility_metrics(assets_with_values, asset_type_allocations)
        
        # Identify high risk assets based on various risk factors
        high_risk_assets = self._identify_high_risk_assets(
            assets_with_values, total_value, sector_allocations, risk_threshold
        )
        
        # Calculate correlation matrix (estimates based on asset classes)
        correlation_matrix = self._calculate_correlation_matrix(asset_type_allocations)
        
        # Calculate overall portfolio risk score
        risk_score = self._calculate_overall_risk(
            asset_type_allocations, sector_allocations, volatility_metrics
        )
        
        # Prepare result
        result = {
            "timestamp": datetime.now().isoformat(),
            "portfolio_id": portfolio_id,
            "total_value": round(total_value, 2),
            "asset_class_allocation": {
                "equities": round(asset_type_allocations.get("equity", 0), 4),
                "bonds": round(asset_type_allocations.get("bond", 0), 4),
                "alternatives": round(asset_type_allocations.get("alternative", 0), 4),
                "cash": round(asset_type_allocations.get("cash", 0), 4)
            },
            "sector_allocation": {k: round(v, 4) for k, v in sector_allocations.items() if v > 0},
            "volatility_metrics": volatility_metrics,
            "high_risk_assets": high_risk_assets,
            "overall_risk_score": risk_score,
            "correlation_matrix": correlation_matrix,
            "risk_threshold_used": risk_threshold
        }
        
        # Cache the result
        redis_client.setex(cache_key, self.cache_expiry, json.dumps(result))
        logger.debug(f"Cached risk analysis for portfolio {portfolio_id}")
        
        return result
    
    def _calculate_volatility_metrics(self, assets: List[Dict[str, Any]], 
                                    asset_type_allocations: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate volatility metrics for the portfolio.
        
        Args:
            assets: List of assets with values
            asset_type_allocations: Asset allocations by type
            
        Returns:
            Dictionary with volatility metrics
        """
        # Get stock beta information for equity assets
        equity_assets = [asset for asset in assets if asset.get("asset_type") == "equity"]
        
        # Calculate portfolio beta
        equity_value = sum(asset["value"] for asset in equity_assets)
        weighted_beta = 0
        
        if equity_value > 0:
            # Try to get real beta values from market data if possible
            stock_betas = self._get_stock_betas([asset.get("symbol") for asset in equity_assets])
            
            for asset in equity_assets:
                symbol = asset.get("symbol", "")
                beta = stock_betas.get(symbol, 1.0)  # Default to 1.0 if not found
                weight = asset["value"] / equity_value
                weighted_beta += beta * weight
        
        # Apply equity allocation to get portfolio beta
        portfolio_beta = weighted_beta * asset_type_allocations.get("equity", 0)
        
        # Estimate volatility based on asset allocation
        # Typical annualized volatility by asset class
        volatility_by_class = {
            "equity": 0.15,  # 15% for stocks
            "bond": 0.05,    # 5% for bonds
            "alternative": 0.12,  # 12% for alternatives
            "cash": 0.01     # 1% for cash
        }
        
        # Calculate weighted volatility
        portfolio_volatility = sum(
            allocation * volatility_by_class.get(asset_type, 0.1) 
            for asset_type, allocation in asset_type_allocations.items()
        )
        
        # Calculate Value at Risk (95% confidence)
        # For a normal distribution, 95% VaR is approximately 1.65 * volatility
        var_95 = 1.65 * portfolio_volatility
        
        # Estimate maximum drawdown
        # In practice, maximum drawdown is often around 2-3x volatility
        max_drawdown = 2.5 * portfolio_volatility
        
        return {
            "portfolio_beta": round(portfolio_beta, 2),
            "portfolio_volatility": round(portfolio_volatility, 4),
            "value_at_risk_95": round(var_95, 4),
            "max_drawdown": round(max_drawdown, 4),
            "sharpe_ratio": round(self._calculate_sharpe_ratio(portfolio_volatility), 2)
        }
    
    def _calculate_sharpe_ratio(self, volatility: float, risk_free_rate: float = 0.04) -> float:
        """
        Calculate Sharpe ratio for the portfolio.
        
        Args:
            volatility: Portfolio volatility
            risk_free_rate: Risk-free rate (default 4%)
            
        Returns:
            Estimated Sharpe ratio
        """
        # Estimate expected return based on CAPM-like model
        # Expected return = risk-free rate + risk premium
        expected_return = risk_free_rate + volatility * 0.5  # Simplified risk premium
        
        # Sharpe ratio = (Expected return - Risk-free rate) / Volatility
        if volatility == 0:
            return 0
            
        sharpe_ratio = (expected_return - risk_free_rate) / volatility
        return sharpe_ratio
    
    def _get_stock_betas(self, symbols: List[str]) -> Dict[str, float]:
        """
        Get beta values for the specified stock symbols.
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            Dictionary mapping symbols to beta values
        """
        # Common beta values for major stocks
        # In a real implementation, these would be retrieved from a financial data API
        common_betas = {
            "AAPL": 1.25,
            "MSFT": 1.15,
            "AMZN": 1.40,
            "GOOGL": 1.20,
            "META": 1.35,
            "TSLA": 1.60,
            "NVDA": 1.45,
            "BRK.B": 0.85,
            "JPM": 1.30,
            "JNJ": 0.70,
            "UNH": 0.80,
            "V": 1.10,
            "PG": 0.60,
            "HD": 1.05,
            "XOM": 0.95
        }
        
        result = {}
        for symbol in symbols:
            result[symbol] = common_betas.get(symbol, 1.0)
            
        return result
    
    def _identify_high_risk_assets(self, assets: List[Dict[str, Any]], 
                                 total_value: float,
                                 sector_allocations: Dict[str, float],
                                 risk_threshold: float) -> List[Dict[str, Any]]:
        """
        Identify high risk assets in the portfolio.
        
        Args:
            assets: List of assets with values
            total_value: Total portfolio value
            sector_allocations: Sector allocations
            risk_threshold: Threshold for flagging high risk assets
            
        Returns:
            List of high risk assets with risk factors
        """
        high_risk_assets = []
        
        for asset in assets:
            risk_factors = []
            risk_score = 0.0
            
            # Factor 1: Asset type risk
            asset_type = asset.get("asset_type", "unknown")
            asset_type_risk = {
                "equity": 0.7,
                "bond": 0.3,
                "alternative": 0.6,
                "cash": 0.1
            }.get(asset_type, 0.5)
            
            risk_score += asset_type_risk * 0.3  # 30% weight
            
            # Factor 2: Concentration risk
            allocation = asset.get("value", 0) / total_value if total_value > 0 else 0
            if allocation > 0.1:
                risk_factors.append(f"High concentration ({int(allocation * 100)}% of portfolio)")
                risk_score += min(allocation * 2, 0.3)  # 0-30% based on allocation
            
            # Factor 3: Sector concentration (for equities)
            if asset_type == "equity":
                symbol = asset.get("symbol", "")
                sector = None
                
                # Find which sector this asset belongs to
                for sec_name, symbols in {
                    "Technology": ["AAPL", "MSFT", "GOOGL", "META", "NVDA"],
                    "E-commerce": ["AMZN"],
                    "Financial": ["BRK.B", "JPM", "V"],
                    "Healthcare": ["JNJ", "UNH"],
                    "Consumer": ["PG"],
                    "Energy": ["XOM", "CVX"],
                    "Industrials": ["HON", "CAT", "GE"],
                    "Utilities": ["NEE", "DUK", "SO"],
                    "Real Estate": ["AMT", "PLD", "SPG"],
                    "Telecom": ["T", "VZ", "TMUS"]
                }.items():
                    if symbol in symbols:
                        sector = sec_name
                        break
                
                if sector and sector_allocations.get(sector, 0) > 0.25:
                    risk_factors.append(f"High sector concentration in {sector}")
                    risk_score += 0.2  # 20% weight for sector concentration
            
            # Factor 4: Volatility risk (for equities)
            if asset_type == "equity":
                symbol = asset.get("symbol", "")
                beta = self._get_stock_betas([symbol]).get(symbol, 1.0)
                
                if beta > 1.2:
                    risk_factors.append(f"High volatility (beta = {beta})")
                    risk_score += (beta - 1) * 0.2  # 0-20% based on beta above 1
            
            # Add to high risk assets if risk score exceeds threshold
            if risk_score > risk_threshold:
                high_risk_assets.append({
                    "symbol": asset.get("symbol", ""),
                    "name": asset.get("name", ""),
                    "risk_score": round(risk_score, 2),
                    "allocation": round(allocation, 4),
                    "risk_factors": risk_factors
                })
        
        return high_risk_assets
    
    def _calculate_correlation_matrix(self, asset_type_allocations: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate correlation matrix between asset classes.
        
        Args:
            asset_type_allocations: Asset allocations by type
            
        Returns:
            Dictionary with correlation coefficients
        """
        # Typical correlation values between asset classes
        # In a real implementation, these would be calculated from historical data
        correlations = {
            "stocks_bonds": -0.2,     # Negative correlation (diversification benefit)
            "stocks_alternatives": 0.3,  # Moderate positive correlation
            "stocks_cash": 0.0,         # No correlation
            "bonds_alternatives": 0.1,   # Low positive correlation
            "bonds_cash": 0.0,           # No correlation
            "alternatives_cash": 0.0     # No correlation
        }
        
        return correlations
    
    def _calculate_overall_risk(self, asset_type_allocations: Dict[str, float],
                              sector_allocations: Dict[str, float],
                              volatility_metrics: Dict[str, float]) -> float:
        """
        Calculate overall portfolio risk score (0-1 scale).
        
        Args:
            asset_type_allocations: Asset allocations by type
            sector_allocations: Sector allocations
            volatility_metrics: Volatility metrics
            
        Returns:
            Overall risk score from 0 to 1
        """
        # Component 1: Asset allocation risk (0-40%)
        equity_allocation = asset_type_allocations.get("equity", 0)
        alt_allocation = asset_type_allocations.get("alternative", 0)
        bond_allocation = asset_type_allocations.get("bond", 0)
        
        asset_allocation_risk = (
            equity_allocation * 0.7 +  # Equities are highest risk
            alt_allocation * 0.5 +    # Alternatives are medium-high risk
            bond_allocation * 0.2      # Bonds are low-medium risk
        ) * 0.4  # 40% weight in overall score
        
        # Component 2: Concentration risk (0-20%)
        max_sector_allocation = max(sector_allocations.values()) if sector_allocations else 0
        max_allocation_penalty = max(0, max_sector_allocation - 0.25) * 0.8  # Penalize allocations above 25%
        
        # Component 3: Volatility risk (0-40%)
        volatility_risk = min(volatility_metrics.get("portfolio_volatility", 0) / 0.2, 1) * 0.4
        
        # Calculate final risk score (0-1 scale)
        risk_score = asset_allocation_risk + max_allocation_penalty + volatility_risk
        
        # Cap at 1.0
        return min(round(risk_score, 2), 1.0)

# Create an instance of the service for easy importing
risk_analyzer = RiskAnalyzer()