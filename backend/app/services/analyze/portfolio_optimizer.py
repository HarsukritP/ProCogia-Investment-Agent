import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
from loguru import logger

from ...database.redis import redis_client
from ...services.get.market_data import market_data_service 
from ...services.llm.openai_client import openai_client

class PortfolioOptimizer:
    """Service for optimizing portfolio allocations."""
    
    def __init__(self):
        """Initialize the portfolio optimizer service."""
        self.cache_expiry = 300  # Cache data for 5 minutes
    
    def optimize_portfolio(self, portfolio_data: Dict[str, Any], 
                          target_risk: float = 0.5,
                          constraints: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate portfolio optimization recommendations.
        
        Args:
            portfolio_data: Portfolio information
            target_risk: Target risk level (0-1 scale)
            constraints: Dictionary of constraints for the optimization
            
        Returns:
            Dictionary with optimization recommendations
        """
        # Check cache first
        portfolio_id = portfolio_data.get("id", "unknown")
        constraints_str = json.dumps(constraints) if constraints else "none"
        cache_key = f"portfolio_optimization:{portfolio_id}:{target_risk}:{constraints_str}"
        cached_data = redis_client.get(cache_key)
        
        if cached_data:
            logger.debug(f"Using cached optimization for portfolio {portfolio_id}")
            return json.loads(cached_data)
        
        logger.info(f"Optimizing portfolio {portfolio_id} with target risk {target_risk}")
        
        # Default constraints if not provided
        if constraints is None:
            constraints = {}
        
        # Default constraints
        default_constraints = {
            "max_allocation_per_asset": 0.2,
            "min_bonds_allocation": 0.15,
            "max_alternatives_allocation": 0.1,
            "liquidity_requirement": 0.3  # Portion that should be in liquid assets
        }
        
        # Merge user constraints with defaults
        for key, value in default_constraints.items():
            if key not in constraints:
                constraints[key] = value
        
        # Get market data to inform optimization
        # In a real implementation, this would be more extensive
        market_data = self._get_relevant_market_data(portfolio_data)
        
        # Determine current risk level and allocation
        current_risk = portfolio_data.get("risk_metrics", {}).get("overall_risk_score", 0.65)
        
        # Two approaches to optimization:
        # 1. Rule-based optimization using our own logic
        # 2. AI-driven optimization using OpenAI
        
        # Let's use OpenAI for advanced optimization logic
        if market_data:
            try:
                logger.debug("Using OpenAI for portfolio optimization")
                recommendations = openai_client.generate_trade_recommendations(
                    portfolio_data, market_data, constraints
                )
                
                # If we got valid recommendations, use them
                if recommendations and "error" not in recommendations:
                    # Add optimization ID and metadata
                    optimization_id = f"opt-{int(datetime.now().timestamp())}"
                    recommendations["optimization_id"] = optimization_id
                    recommendations["timestamp"] = datetime.now().isoformat()
                    recommendations["portfolio_id"] = portfolio_id
                    recommendations["current_risk_score"] = current_risk
                    recommendations["target_risk_score"] = target_risk
                    recommendations["constraints_applied"] = constraints
                    
                    # Cache the result
                    redis_client.setex(cache_key, self.cache_expiry, json.dumps(recommendations))
                    logger.debug(f"Cached AI-based optimization for portfolio {portfolio_id}")
                    
                    return recommendations
                
                # If OpenAI fails, fall back to rule-based
                logger.warning("OpenAI optimization failed, falling back to rule-based")
            
            except Exception as e:
                logger.error(f"Error in OpenAI portfolio optimization: {e}")
        
        # Fall back to rule-based optimization
        logger.debug("Using rule-based portfolio optimization")
        
        # Extract assets from portfolio data
        assets = portfolio_data.get("assets", [])
        
        if not assets:
            logger.warning(f"No assets found in portfolio {portfolio_id}")
            return {
                "error": "No assets found in portfolio",
                "timestamp": datetime.now().isoformat()
            }
        
        # Calculate asset values and allocations
        assets_with_values = []
        total_value = 0
        
        for asset in assets:
            if "quantity" in asset and "current_price" in asset:
                asset_value = asset["quantity"] * asset["current_price"]
                asset_with_value = asset.copy()
                asset_with_value["value"] = asset_value
                asset_with_value["allocation"] = 0  # Will be set after total is known
                assets_with_values.append(asset_with_value)
                total_value += asset_value
        
        # Set allocations
        for asset in assets_with_values:
            asset["allocation"] = asset["value"] / total_value if total_value > 0 else 0
        
        # Generate recommendations based on target risk vs current risk
        recommendations = self._generate_rule_based_recommendations(
            assets_with_values, current_risk, target_risk, constraints, market_data
        )
        
        # Estimate outcome
        expected_outcomes = self._estimate_optimization_outcomes(
            assets_with_values, recommendations, current_risk, target_risk
        )
        
        # Generate optimization ID
        optimization_id = f"opt-{int(datetime.now().timestamp())}"
        
        # Prepare result
        result = {
            "optimization_id": optimization_id,
            "timestamp": datetime.now().isoformat(),
            "portfolio_id": portfolio_id,
            "current_risk_score": current_risk,
            "target_risk_score": target_risk,
            "constraints_applied": constraints,
            "recommended_trades": recommendations,
            "expected_impact": expected_outcomes,
            "optimization_strategy": self._generate_strategy_explanation(current_risk, target_risk, recommendations)
        }
        
        # Cache the result
        redis_client.setex(cache_key, self.cache_expiry, json.dumps(result))
        logger.debug(f"Cached rule-based optimization for portfolio {portfolio_id}")
        
        return result
    
    def _get_relevant_market_data(self, portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get relevant market data to inform optimization.
        
        Args:
            portfolio_data: Portfolio data
            
        Returns:
            Dictionary with relevant market data
        """
        # Extract symbols from portfolio
        symbols = []
        for asset in portfolio_data.get("assets", []):
            if "symbol" in asset and asset["symbol"]:
                symbols.append(asset["symbol"])
        
        try:
            # Get market data for the symbols
            market_data = json.loads(market_data_service.get_market_data(symbols=symbols))
            
            # Get current indices data
            # indices_data = json.loads(market_data_service.get_market_data(indices=["S&P 500", "NASDAQ", "Dow Jones"]))
            
            return market_data
        except Exception as e:
            logger.error(f"Error getting market data for optimization: {e}")
            return {}
    
    def _generate_rule_based_recommendations(self, assets: List[Dict[str, Any]],
                                          current_risk: float,
                                          target_risk: float,
                                          constraints: Dict[str, Any],
                                          market_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate rule-based portfolio recommendations.
        
        Args:
            assets: List of assets with values and allocations
            current_risk: Current portfolio risk score
            target_risk: Target risk score
            constraints: Optimization constraints
            market_data: Market data
            
        Returns:
            List of recommended trades
        """
        recommendations = []
        
        # Group assets by type
        asset_groups = {}
        for asset in assets:
            asset_type = asset.get("asset_type", "unknown")
            if asset_type not in asset_groups:
                asset_groups[asset_type] = []
            asset_groups[asset_type].append(asset)
        
        # Calculate current allocations by type
        total_value = sum(asset["value"] for asset in assets)
        current_allocations = {}
        
        for asset_type, assets_list in asset_groups.items():
            type_value = sum(asset["value"] for asset in assets_list)
            current_allocations[asset_type] = type_value / total_value if total_value > 0 else 0
        
        # Determine target allocations based on risk
        target_allocations = self._determine_target_allocations(current_allocations, current_risk, target_risk, constraints)
        
        # Calculate adjustments needed
        allocation_changes = {}
        for asset_type, target in target_allocations.items():
            current = current_allocations.get(asset_type, 0)
            allocation_changes[asset_type] = target - current
        
        # Generate specific asset recommendations
        
        # 1. Handle equities
        if "equity" in allocation_changes:
            equity_change = allocation_changes["equity"]
            if abs(equity_change) > 0.02:  # Only recommend if change is significant
                equity_recs = self._generate_equity_recommendations(
                    asset_groups.get("equity", []), equity_change, constraints, market_data
                )
                recommendations.extend(equity_recs)
        
        # 2. Handle bonds
        if "bond" in allocation_changes:
            bond_change = allocation_changes["bond"]
            if abs(bond_change) > 0.02:
                bond_recs = self._generate_bond_recommendations(
                    asset_groups.get("bond", []), bond_change, constraints
                )
                recommendations.extend(bond_recs)
        
        # 3. Handle alternatives
        if "alternative" in allocation_changes:
            alt_change = allocation_changes["alternative"]
            if abs(alt_change) > 0.02:
                alt_recs = self._generate_alternative_recommendations(
                    asset_groups.get("alternative", []), alt_change
                )
                recommendations.extend(alt_recs)
        
        # 4. Handle cash
        if "cash" in allocation_changes:
            cash_change = allocation_changes["cash"]
            if abs(cash_change) > 0.02:
                cash_recs = self._generate_cash_recommendations(
                    asset_groups.get("cash", []), cash_change
                )
                recommendations.extend(cash_recs)
        
        return recommendations
    
    def _determine_target_allocations(self, current_allocations: Dict[str, float],
                                    current_risk: float,
                                    target_risk: float,
                                    constraints: Dict[str, Any]) -> Dict[str, float]:
        """
        Determine target asset allocations based on risk level.
        
        Args:
            current_allocations: Current asset allocations by type
            current_risk: Current risk score
            target_risk: Target risk score
            constraints: Optimization constraints
            
        Returns:
            Dictionary with target allocations by asset type
        """
        # Standard allocation profiles by risk level
        allocation_profiles = {
            0.1: {"equity": 0.20, "bond": 0.65, "alternative": 0.05, "cash": 0.10},  # Very Conservative
            0.3: {"equity": 0.40, "bond": 0.45, "alternative": 0.05, "cash": 0.10},  # Conservative
            0.5: {"equity": 0.60, "bond": 0.30, "alternative": 0.05, "cash": 0.05},  # Moderate
            0.7: {"equity": 0.75, "bond": 0.15, "alternative": 0.05, "cash": 0.05},  # Aggressive
            0.9: {"equity": 0.85, "bond": 0.05, "alternative": 0.08, "cash": 0.02}   # Very Aggressive
        }
        
        # Find closest risk profiles
        risk_levels = sorted(allocation_profiles.keys())
        lower_idx = 0
        
        for i, risk in enumerate(risk_levels):
            if risk > target_risk:
                lower_idx = max(0, i - 1)
                break
            elif i == len(risk_levels) - 1:
                lower_idx = i
        
        upper_idx = min(lower_idx + 1, len(risk_levels) - 1)
        lower_risk = risk_levels[lower_idx]
        upper_risk = risk_levels[upper_idx]
        
        # Linear interpolation between profiles
        if lower_risk == upper_risk:
            target_allocation = allocation_profiles[lower_risk].copy()
        else:
            weight = (target_risk - lower_risk) / (upper_risk - lower_risk)
            target_allocation = {}
            
            for asset_type in allocation_profiles[lower_risk]:
                lower_alloc = allocation_profiles[lower_risk][asset_type]
                upper_alloc = allocation_profiles[upper_risk][asset_type]
                target_allocation[asset_type] = lower_alloc + weight * (upper_alloc - lower_alloc)
        
        # Apply constraints
        
        # Minimum bond allocation
        min_bonds = constraints.get("min_bonds_allocation", 0.15)
        if target_allocation.get("bond", 0) < min_bonds:
            # Increase bonds to minimum, reduce other asset types proportionally
            shortfall = min_bonds - target_allocation.get("bond", 0)
            target_allocation["bond"] = min_bonds
            
            # Calculate total allocation for other assets
            other_types = [t for t in target_allocation if t != "bond"]
            other_total = sum(target_allocation[t] for t in other_types)
            
            # Reduce other assets proportionally
            for asset_type in other_types:
                weight = target_allocation[asset_type] / other_total if other_total > 0 else 0
                target_allocation[asset_type] -= shortfall * weight
        
        # Maximum alternatives allocation
        max_alt = constraints.get("max_alternatives_allocation", 0.1)
        if target_allocation.get("alternative", 0) > max_alt:
            # Decrease alternatives to maximum, increase other asset types proportionally
            excess = target_allocation.get("alternative", 0) - max_alt
            target_allocation["alternative"] = max_alt
            
            # Calculate total allocation for other assets
            other_types = [t for t in target_allocation if t != "alternative"]
            other_total = sum(target_allocation[t] for t in other_types)
            
            # Increase other assets proportionally
            for asset_type in other_types:
                weight = target_allocation[asset_type] / other_total if other_total > 0 else 0
                target_allocation[asset_type] += excess * weight
        
        # Ensure allocations sum to 1.0
        total = sum(target_allocation.values())
        if total != 1.0:
            scaling_factor = 1.0 / total
            for asset_type in target_allocation:
                target_allocation[asset_type] *= scaling_factor
        
        # Round to 4 decimal places
        return {k: round(v, 4) for k, v in target_allocation.items()}
    
    def _generate_equity_recommendations(self, equity_assets: List[Dict[str, Any]],
                                       allocation_change: float,
                                       constraints: Dict[str, Any],
                                       market_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate recommendations for equity allocation changes.
        
        Args:
            equity_assets: List of equity assets
            allocation_change: Required change in equity allocation
            constraints: Optimization constraints
            market_data: Market data
            
        Returns:
            List of equity-specific recommendations
        """
        recommendations = []
        max_allocation = constraints.get("max_allocation_per_asset", 0.2)
        
        # Case 1: Increasing equity allocation
        if allocation_change > 0:
            # Check if we have existing equities to increase
            if equity_assets:
                # Find stocks with room to increase
                stocks_to_increase = []
                for asset in equity_assets:
                    current_allocation = asset.get("allocation", 0)
                    if current_allocation < max_allocation:
                        stocks_to_increase.append(asset)
                
                # Sort by potential for increase (lowest allocation first)
                stocks_to_increase.sort(key=lambda x: x.get("allocation", 0))
                
                # Allocate the change across stocks
                remaining_change = allocation_change
                for asset in stocks_to_increase:
                    symbol = asset.get("symbol", "")
                    name = asset.get("name", "")
                    current_allocation = asset.get("allocation", 0)
                    
                    # Avoid exceeding max allocation
                    max_increase = max_allocation - current_allocation
                    increase = min(max_increase, remaining_change, 0.05)  # Limit individual increases
                    
                    if increase > 0.01:  # Only recommend if increase is significant
                        target_allocation = current_allocation + increase
                        remaining_change -= increase
                        
                        # Get current price from market data if available
                        current_price = asset.get("current_price", 100)
                        if "stocks" in market_data:
                            for stock in market_data["stocks"]:
                                if stock.get("symbol") == symbol:
                                    current_price = stock.get("current_price", current_price)
                                    break
                        
                        recommendations.append({
                            "symbol": symbol,
                            "name": name,
                            "action": "increase",
                            "current_allocation": round(current_allocation, 4),
                            "target_allocation": round(target_allocation, 4),
                            "current_price": current_price,
                            "rationale": f"Increase position in {name} to optimize risk/return profile"
                        })
                
                # If we still have allocation to add, suggest new equity positions
                if remaining_change > 0.03:
                    # Get S&P 500 ETF for broad market exposure
                    recommendations.append({
                        "symbol": "SPY",
                        "name": "SPDR S&P 500 ETF",
                        "action": "add",
                        "target_allocation": round(remaining_change, 4),
                        "rationale": "Add broad market exposure via S&P 500 ETF"
                    })
            else:
                # No existing equities, recommend ETFs for diversified exposure
                recommendations.append({
                    "symbol": "SPY",
                    "name": "SPDR S&P 500 ETF",
                    "action": "add",
                    "target_allocation": round(allocation_change * 0.6, 4),
                    "rationale": "Add core U.S. large-cap exposure via S&P 500 ETF"
                })
                
                recommendations.append({
                    "symbol": "QQQ",
                    "name": "Invesco QQQ Trust (NASDAQ 100 ETF)",
                    "action": "add",
                    "target_allocation": round(allocation_change * 0.4, 4),
                    "rationale": "Add growth exposure via NASDAQ 100 ETF"
                })
        
        # Case 2: Decreasing equity allocation
        elif allocation_change < 0:
            if equity_assets:
                # Sort by risk (highest beta first)
                stock_betas = {
                    "AAPL": 1.25, "MSFT": 1.15, "AMZN": 1.40, "GOOGL": 1.20, "META": 1.35,
                    "TSLA": 1.60, "NVDA": 1.45, "BRK.B": 0.85, "JPM": 1.30, "JNJ": 0.70,
                    "UNH": 0.80, "V": 1.10, "PG": 0.60, "HD": 1.05, "XOM": 0.95
                }
                
                def get_beta(asset):
                    symbol = asset.get("symbol", "")
                    return stock_betas.get(symbol, 1.0)
                
                # Sort by beta (highest first) and then by allocation (highest first)
                sorted_assets = sorted(equity_assets, key=lambda x: (-get_beta(x), -x.get("allocation", 0)))
                
                # Allocate the reduction across stocks
                remaining_change = allocation_change  # This is negative
                for asset in sorted_assets:
                    symbol = asset.get("symbol", "")
                    name = asset.get("name", "")
                    current_allocation = asset.get("allocation", 0)
                    
                    # Don't reduce below a minimum threshold
                    min_allocation = 0.01
                    max_reduction = current_allocation - min_allocation
                    reduction = min(max_reduction, abs(remaining_change))
                    
                    if reduction > 0.01:  # Only recommend if reduction is significant
                        target_allocation = current_allocation - reduction
                        remaining_change += reduction  # Add because both are negative
                        
                        # Get current price from market data if available
                        current_price = asset.get("current_price", 100)
                        if "stocks" in market_data:
                            for stock in market_data["stocks"]:
                                if stock.get("symbol") == symbol:
                                    current_price = stock.get("current_price", current_price)
                                    break
                        
                        recommendations.append({
                            "symbol": symbol,
                            "name": name,
                            "action": "reduce",
                            "current_allocation": round(current_allocation, 4),
                            "target_allocation": round(target_allocation, 4),
                            "current_price": current_price,
                            "rationale": f"Reduce position in {name} to decrease portfolio volatility"
                        })
                
                # If we couldn't reduce enough with partial reductions, suggest complete sell-offs
                if remaining_change < -0.01:
                    for asset in sorted_assets:
                        if asset.get("allocation", 0) < 0.05:  # Small positions
                            symbol = asset.get("symbol", "")
                            name = asset.get("name", "")
                            current_allocation = asset.get("allocation", 0)
                            
                            recommendations.append({
                                "symbol": symbol,
                                "name": name,
                                "action": "sell",
                                "current_allocation": round(current_allocation, 4),
                                "target_allocation": 0,
                                "rationale": f"Sell entire position in {name} to streamline portfolio and reduce risk"
                            })
                            
                            remaining_change += current_allocation
                            if remaining_change >= -0.01:
                                break
        
        return recommendations
    
    def _generate_bond_recommendations(self, bond_assets: List[Dict[str, Any]],
                                     allocation_change: float,
                                     constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate recommendations for bond allocation changes.
        
        Args:
            bond_assets: List of bond assets
            allocation_change: Required change in bond allocation
            constraints: Optimization constraints
            
        Returns:
            List of bond-specific recommendations
        """
        recommendations = []
        
        # Case 1: Increasing bond allocation
        if allocation_change > 0:
            # Check if we have existing bonds to increase
            if bond_assets:
                # Allocate the increase proportionally across existing bonds
                total_bond_allocation = sum(asset.get("allocation", 0) for asset in bond_assets)
                
                for asset in bond_assets:
                    name = asset.get("name", "")
                    current_allocation = asset.get("allocation", 0)
                    
                    # Calculate proportional increase
                    weight = current_allocation / total_bond_allocation if total_bond_allocation > 0 else 1/len(bond_assets)
                    increase = allocation_change * weight
                    
                    if increase > 0.01:  # Only recommend if increase is significant
                        target_allocation = current_allocation + increase
                        
                        recommendations.append({
                            "name": name,
                            "action": "increase",
                            "current_allocation": round(current_allocation, 4),
                            "target_allocation": round(target_allocation, 4),
                            "rationale": f"Increase allocation to {name} to enhance portfolio stability"
                        })
            else:
                # No existing bonds, recommend new bond positions
                recommendations.append({
                    "name": "US Treasury ETF",
                    "symbol": "GOVT",
                    "action": "add",
                    "target_allocation": round(allocation_change * 0.5, 4),
                    "rationale": "Add US Treasury exposure for stability and safety"
                })
                
                recommendations.append({
                    "name": "Corporate Bond ETF",
                    "symbol": "LQD",
                    "action": "add",
                    "target_allocation": round(allocation_change * 0.5, 4),
                    "rationale": "Add investment-grade corporate bond exposure for enhanced yield"
                })
        
        # Case 2: Decreasing bond allocation
        elif allocation_change < 0:
            if bond_assets:
                # Sort by yield (lowest first)
                sorted_assets = sorted(bond_assets, key=lambda x: x.get("yield", 0))
                
                # Allocate the reduction across bonds
                remaining_change = allocation_change  # This is negative
                for asset in sorted_assets:
                    name = asset.get("name", "")
                    current_allocation = asset.get("allocation", 0)
                    
                    # Calculate reduction (more for lower-yielding bonds)
                    reduction = min(current_allocation - 0.01, abs(remaining_change))
                    
                    if reduction > 0.01:  # Only recommend if reduction is significant
                        target_allocation = current_allocation - reduction
                        remaining_change += reduction  # Add because both are negative
                        
                        recommendations.append({
                            "name": name,
                            "action": "reduce",
                            "current_allocation": round(current_allocation, 4),
                            "target_allocation": round(target_allocation, 4),
                            "rationale": f"Reduce allocation to {name} to optimize yield while maintaining risk profile"
                        })
        
        return recommendations
    
    def _generate_alternative_recommendations(self, alt_assets: List[Dict[str, Any]],
                                            allocation_change: float) -> List[Dict[str, Any]]:
        """
        Generate recommendations for alternative investment allocation changes.
        
        Args:
            alt_assets: List of alternative assets
            allocation_change: Required change in alternative allocation
            
        Returns:
            List of alternative-specific recommendations
        """
        recommendations = []
        
        # Case 1: Increasing alternative allocation
        if allocation_change > 0:
            # Check if we have existing alternative investments to increase
            if alt_assets:
                # Simple approach: increase all proportionally
                total_alt_allocation = sum(asset.get("allocation", 0) for asset in alt_assets)
                
                for asset in alt_assets:
                    name = asset.get("name", "")
                    current_allocation = asset.get("allocation", 0)
                    
                    # Calculate proportional increase
                    weight = current_allocation / total_alt_allocation if total_alt_allocation > 0 else 1/len(alt_assets)
                    increase = allocation_change * weight
                    
                    if increase > 0.005:  # Only recommend if increase is significant
                        target_allocation = current_allocation + increase
                        
                        recommendations.append({
                            "name": name,
                            "action": "increase",
                            "current_allocation": round(current_allocation, 4),
                            "target_allocation": round(target_allocation, 4),
                            "rationale": f"Increase allocation to {name} for improved diversification"
                        })
            else:
                # No existing alternatives, recommend new positions
                recommendations.append({
                    "name": "Real Estate ETF",
                    "symbol": "VNQ",
                    "action": "add",
                    "target_allocation": round(allocation_change * 0.6, 4),
                    "rationale": "Add real estate exposure for income and diversification"
                })
                
                recommendations.append({
                    "name": "Gold ETF",
                    "symbol": "GLD",
                    "action": "add",
                    "target_allocation": round(allocation_change * 0.4, 4),
                    "rationale": "Add gold exposure as a hedge against inflation and market volatility"
                })
        
        # Case 2: Decreasing alternative allocation
        elif allocation_change < 0:
            if alt_assets:
                # Sort by risk (highest first)
                sorted_assets = sorted(alt_assets, key=lambda x: x.get("risk_score", 5), reverse=True)
                
                # Allocate the reduction across alternatives
                remaining_change = allocation_change  # This is negative
                for asset in sorted_assets:
                    name = asset.get("name", "")
                    current_allocation = asset.get("allocation", 0)
                    
                    # Calculate reduction
                    reduction = min(current_allocation - 0.005, abs(remaining_change))
                    
                    if reduction > 0.005:  # Only recommend if reduction is significant
                        target_allocation = current_allocation - reduction
                        remaining_change += reduction  # Add because both are negative
                        
                        recommendations.append({
                            "name": name,
                            "action": "reduce",
                            "current_allocation": round(current_allocation, 4),
                            "target_allocation": round(target_allocation, 4),
                            "rationale": f"Reduce allocation to {name} to decrease portfolio risk"
                        })
        
        return recommendations
    
    def _generate_cash_recommendations(self, cash_assets: List[Dict[str, Any]],
                                     allocation_change: float) -> List[Dict[str, Any]]:
        """
        Generate recommendations for cash allocation changes.
        
        Args:
            cash_assets: List of cash assets
            allocation_change: Required change in cash allocation
            
        Returns:
            List of cash-specific recommendations
        """
        recommendations = []
        
        # Cash adjustments are typically the result of other asset changes
        # but we can add specific recommendations if needed
        
        if abs(allocation_change) > 0.02:
            # For significant changes, add a specific recommendation
            if allocation_change > 0:
                recommendations.append({
                    "action": "increase_cash",
                    "amount_change": round(allocation_change, 4),
                    "rationale": "Increase cash reserves to enhance liquidity and reduce portfolio risk"
                })
            else:
                recommendations.append({
                    "action": "decrease_cash",
                    "amount_change": round(-allocation_change, 4),
                    "rationale": "Reduce cash holdings to improve portfolio returns while maintaining adequate liquidity"
                })
        
        return recommendations
    
    def _estimate_optimization_outcomes(self, assets: List[Dict[str, Any]],
                                     recommendations: List[Dict[str, Any]],
                                     current_risk: float,
                                     target_risk: float) -> Dict[str, Any]:
        """
        Estimate the impact of optimization recommendations.
        
        Args:
            assets: Current asset list
            recommendations: Optimization recommendations
            current_risk: Current risk score
            target_risk: Target risk score
            
        Returns:
            Dictionary with estimated outcomes
        """
        # In a real implementation, this would use more sophisticated models
        # For this demo, we'll use simplified calculations
        
        # Estimate current portfolio return (approximate based on risk level)
        risk_free_rate = 0.04  # Assuming 4% risk-free rate
        market_risk_premium = 0.06  # Assuming 6% market risk premium
        
        current_return = risk_free_rate + current_risk * market_risk_premium
        target_return = risk_free_rate + target_risk * market_risk_premium
        
        # Estimate current volatility (approximate based on risk level)
        current_volatility = current_risk * 0.2  # 20% max volatility at risk=1
        target_volatility = target_risk * 0.2
        
        # Calculate Sharpe ratios
        current_sharpe = (current_return - risk_free_rate) / current_volatility if current_volatility > 0 else 0
        target_sharpe = (target_return - risk_free_rate) / target_volatility if target_volatility > 0 else 0
        
        # Estimate rebalancing cost
        trade_value = 0
        for rec in recommendations:
            if rec.get("action") in ["increase", "reduce"]:
                current_alloc = rec.get("current_allocation", 0)
                target_alloc = rec.get("target_allocation", 0)
                trade_value += abs(target_alloc - current_alloc)
            elif rec.get("action") in ["add", "sell"]:
                target_alloc = rec.get("target_allocation", 0)
                trade_value += target_alloc
                
        # Assuming 0.1% transaction cost
        transaction_cost = trade_value * 0.001
        
        return {
            "current_portfolio": {
                "expected_annual_return": round(current_return, 4),
                "volatility": round(current_volatility, 4),
                "sharpe_ratio": round(current_sharpe, 2)
            },
            "optimized_portfolio": {
                "expected_annual_return": round(target_return, 4),
                "volatility": round(target_volatility, 4),
                "sharpe_ratio": round(target_sharpe, 2)
            },
            "rebalancing_cost_estimate": round(transaction_cost, 4),
            "risk_reduction": round(current_risk - target_risk, 4) if current_risk > target_risk else 0,
            "return_enhancement": round(target_return - current_return, 4) if target_return > current_return else 0
        }
    
    def _generate_strategy_explanation(self, current_risk: float, 
                                     target_risk: float,
                                     recommendations: List[Dict[str, Any]]) -> str:
        """
        Generate a natural language explanation of the optimization strategy.
        
        Args:
            current_risk: Current risk score
            target_risk: Target risk score
            recommendations: Optimization recommendations
            
        Returns:
            Strategy explanation text
        """
        if current_risk > target_risk:
            strategy = "The optimization strategy focuses on reducing portfolio risk "
            if current_risk - target_risk > 0.2:
                strategy += "significantly "
            elif current_risk - target_risk > 0.1:
                strategy += "moderately "
            else:
                strategy += "slightly "
                
            strategy += "while maintaining return potential. This is achieved by "
            
            # Count recommendation types
            actions = {}
            for rec in recommendations:
                action = rec.get("action", "")
                if action in actions:
                    actions[action] += 1
                else:
                    actions[action] = 1
            
            strategy_parts = []
            if actions.get("reduce", 0) > 0:
                strategy_parts.append(f"reducing exposure to higher-volatility assets")
            if actions.get("increase", 0) > 0 and "bond" in str(recommendations):
                strategy_parts.append(f"increasing allocation to bonds for stability")
            if actions.get("add", 0) > 0 and "bond" in str(recommendations):
                strategy_parts.append(f"adding bond positions")
            if actions.get("increase", 0) > 0 and "cash" in str(recommendations):
                strategy_parts.append(f"increasing cash reserves")
                
            strategy += ", ".join(strategy_parts) + "."
            
        else:
            strategy = "The optimization strategy aims to enhance portfolio returns "
            if target_risk - current_risk > 0.2:
                strategy += "significantly "
            elif target_risk - current_risk > 0.1:
                strategy += "moderately "
            else:
                strategy += "slightly "
                
            strategy += "while accepting additional risk. This is achieved by "
            
            # Count recommendation types
            actions = {}
            for rec in recommendations:
                action = rec.get("action", "")
                if action in actions:
                    actions[action] += 1
                else:
                    actions[action] = 1
            
            strategy_parts = []
            if actions.get("increase", 0) > 0 and "equity" in str(recommendations):
                strategy_parts.append(f"increasing equity exposure")
            if actions.get("add", 0) > 0 and "equity" in str(recommendations):
                strategy_parts.append(f"adding equity positions")
            if actions.get("reduce", 0) > 0 and "bond" in str(recommendations):
                strategy_parts.append(f"reducing lower-yielding bond allocations")
                
            strategy += ", ".join(strategy_parts) + "."
        
        return strategy

# Create an instance of the service for easy importing
portfolio_optimizer = PortfolioOptimizer()