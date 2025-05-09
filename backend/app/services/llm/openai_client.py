import os
import json
from typing import Dict, List, Any, Optional
import openai
from loguru import logger

from ...core.config import settings

class OpenAIClient:
    def __init__(self, model: Optional[str] = None):
        """
        Initialize OpenAI client with specified model.
        
        Args:
            model: Model identifier to use (default to config settings)
        """
        self.api_key = settings.OPENAI_API_KEY
        self.model = model or settings.OPENAI_MODEL
        
        # Set up OpenAI client
        openai.api_key = self.api_key
        
        logger.debug(f"Initialized OpenAI client with model: {self.model}")
    
    def generate_response(self, messages: List[Dict[str, str]], system_prompt: Optional[str] = None) -> str:
        """
        Generate a response from OpenAI based on message history.
        
        Args:
            messages: List of message objects with role and content
            system_prompt: Optional system prompt to include
        
        Returns:
            Generated text response
        """
        try:
            # Format messages for OpenAI API
            formatted_messages = []
            
            # Add system message if provided
            if system_prompt:
                formatted_messages.append({"role": "system", "content": system_prompt})
            
            # Add conversation messages
            for msg in messages:
                if msg["role"] in ["user", "assistant", "system"]:
                    formatted_messages.append({"role": msg["role"], "content": msg["content"]})
            
            # Generate response
            logger.debug(f"Sending request to OpenAI API with {len(formatted_messages)} messages")
            response = openai.chat.completions.create(
                model=self.model,
                messages=formatted_messages,
                temperature=0.7,
                max_tokens=2048
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            logger.error(f"Error generating response from OpenAI: {e}")
            return f"Error generating response: {str(e)}"
    
    def analyze_portfolio(self, portfolio_data: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze portfolio data and provide insights using OpenAI.
        
        Args:
            portfolio_data: Portfolio information
            market_data: Current market conditions
        
        Returns:
            Dictionary with analysis results
        """
        try:
            system_prompt = """
            You are an expert financial analyst and portfolio manager. 
            Analyze the portfolio and market data provided to generate insights and recommendations.
            Focus on risk assessment, performance evaluation, and optimization opportunities.
            Your response should be structured as JSON with the following sections:
            - risk_assessment: Analysis of the portfolio's risk profile
            - performance_evaluation: Evaluation of portfolio performance
            - optimization_recommendations: Specific recommendations for improvement
            - market_outlook: Analysis of current market conditions and implications
            
            Provide specific, actionable insights based on the data provided.
            Return ONLY valid JSON with no markdown formatting or explanation.
            """
            
            # Format input for OpenAI
            portfolio_json = json.dumps(portfolio_data, indent=2)
            market_json = json.dumps(market_data, indent=2)
            
            user_message = f"""
            Please analyze this portfolio data:
            
            {portfolio_json}
            
            And the current market conditions:
            
            {market_json}
            
            Provide a comprehensive analysis in the JSON format specified.
            """
            
            # Generate analysis
            logger.debug("Sending portfolio analysis request to OpenAI")
            response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.2,
                max_tokens=2048
            )
            
            # Extract JSON from response
            text_response = response.choices[0].message.content
            logger.debug("Received response from OpenAI")
            
            try:
                # Parse JSON response
                analysis = json.loads(text_response)
                return analysis
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from OpenAI response: {e}")
                
                # Try to extract JSON if it's embedded in text
                json_start = text_response.find('{')
                json_end = text_response.rfind('}') + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_content = text_response[json_start:json_end]
                    try:
                        analysis = json.loads(json_content)
                        return analysis
                    except json.JSONDecodeError:
                        pass
                
                # Return error if JSON parsing fails
                return {
                    "error": "Could not extract valid JSON",
                    "text_response": text_response[:500]  # Include part of the response for debugging
                }
                
        except Exception as e:
            logger.error(f"Portfolio analysis failed: {e}")
            return {
                "error": f"Analysis failed: {str(e)}",
                "status": "failed"
            }
    
    def generate_trade_recommendations(self, portfolio_data: Dict[str, Any], 
                                     market_data: Dict[str, Any],
                                     constraints: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate specific trade recommendations based on portfolio and market data.
        
        Args:
            portfolio_data: Portfolio information
            market_data: Current market conditions
            constraints: Trading constraints and preferences
        
        Returns:
            Dictionary with recommended trades
        """
        try:
            system_prompt = """
            You are an expert portfolio manager with a focus on optimization.
            Based on the portfolio data, market conditions, and specified constraints,
            generate actionable trade recommendations.
            Your response should be structured as JSON with the following:
            - recommended_trades: array of trade objects with symbol, action, quantity, and rationale
            - expected_impact: expected impact on portfolio performance and risk
            - optimization_strategy: brief explanation of the strategy
            
            Return ONLY valid JSON with no markdown formatting or explanation.
            """
            
            # Format input for OpenAI
            portfolio_json = json.dumps(portfolio_data, indent=2)
            market_json = json.dumps(market_data, indent=2)
            constraints_json = json.dumps(constraints, indent=2)
            
            user_message = f"""
            Please generate trade recommendations based on this portfolio:
            
            {portfolio_json}
            
            Current market conditions:
            
            {market_json}
            
            With these constraints:
            
            {constraints_json}
            
            Provide recommendations in the JSON format specified.
            """
            
            # Generate recommendations
            logger.debug("Sending trade recommendations request to OpenAI")
            response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.2,
                max_tokens=2048
            )
            
            # Extract JSON from response
            text_response = response.choices[0].message.content
            logger.debug("Received response from OpenAI")
            
            try:
                # Parse JSON response
                recommendations = json.loads(text_response)
                return recommendations
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from OpenAI response: {e}")
                
                # Try to extract JSON if it's embedded in text
                json_start = text_response.find('{')
                json_end = text_response.rfind('}') + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_content = text_response[json_start:json_end]
                    try:
                        recommendations = json.loads(json_content)
                        return recommendations
                    except json.JSONDecodeError:
                        pass
                
                # Return error if JSON parsing fails
                return {
                    "error": "Could not extract valid JSON",
                    "text_response": text_response[:500]  # Include part of the response for debugging
                }
                
        except Exception as e:
            logger.error(f"Trade recommendation generation failed: {e}")
            return {
                "error": f"Recommendation generation failed: {str(e)}",
                "status": "failed"
            }

# Create an instance of the client for easy importing
openai_client = OpenAIClient()