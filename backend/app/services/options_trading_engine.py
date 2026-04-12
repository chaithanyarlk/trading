"""
Algorithmic Options Trading Strategies Module
Implements advanced options strategies with AI-driven selection and execution
"""
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import anthropic
from app.core.config import settings
import json

logger = logging.getLogger(__name__)

class OptionsStrategy:
    """Base class for options strategies"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    def calculate_Greeks_exposure(self, options_data: Dict) -> Dict:
        """Calculate combined Greeks exposure"""
        raise NotImplementedError

class AdvancedOptionsEngine:
    """
    AI-driven options trading engine
    Analyzes market conditions and selects optimal strategies
    """
    
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.CLAUDE_API_KEY)
        self.model = settings.CLAUDE_MODEL
        
        # Define available strategies
        self.strategies = {
            "STRADDLE": self._straddle,
            "STRANGLE": self._strangle,
            "IRON_CONDOR": self._iron_condor,
            "CALL_SPREAD": self._bull_call_spread,
            "PUT_SPREAD": self._bull_put_spread,
            "DIRECTIONAL_CALL": self._directional_call,
            "DIRECTIONAL_PUT": self._directional_put,
        }
    
    async def analyze_and_select_strategy(
        self,
        symbol: str,
        current_price: float,
        options_chain: List[Dict],
        market_data: Dict,
        ai_signal: Dict,
        portfolio_risk_profile: str = "BALANCED"
    ) -> Dict:
        """
        AI-driven strategy selection based on market conditions
        
        Returns: {
            "strategy": "STRADDLE",
            "reason": "High volatility expected before earnings",
            "recommended_strike": 2850,
            "expiry": "2026-04-16",
            "call_contract": "RELIANCE_CE_2850",
            "put_contract": "RELIANCE_PE_2850",
            "entry_price": 95.50,
            "max_profit": 1000,
            "max_loss": 9550,
            "probability_of_profit": 0.65,
            "setup": {...}
        }
        """
        try:
            # Use Claude to select optimal strategy
            strategy_analysis = await self._claude_strategy_selection(
                symbol, current_price, market_data, ai_signal, portfolio_risk_profile
            )
            
            # Get strategy setup
            strategy_name = strategy_analysis.get("strategy", "DIRECTIONAL_CALL")
            strategy_func = self.strategies.get(strategy_name, self._directional_call)
            
            setup = strategy_func(
                symbol, current_price, options_chain, market_data, ai_signal
            )
            
            return {
                "strategy": strategy_name,
                "reason": strategy_analysis.get("reason", "Strategic selection"),
                "probability_of_profit": strategy_analysis.get("probability_of_profit", 0.50),
                "expected_return_percent": strategy_analysis.get("expected_return", 10),
                "risk_reward_ratio": strategy_analysis.get("risk_reward_ratio", 1),
                "setup": setup,
                "ai_reasoning": strategy_analysis.get("full_reasoning", ""),
                "warnings": strategy_analysis.get("warnings", [])
            }
        except Exception as e:
            logger.error(f"Error in strategy selection: {e}")
            return self._default_strategy(symbol, current_price, options_chain)
    
    async def _claude_strategy_selection(
        self,
        symbol: str,
        current_price: float,
        market_data: Dict,
        ai_signal: Dict,
        portfolio_risk_profile: str
    ) -> Dict:
        """Use Claude to select optimal strategy"""
        try:
            prompt = f"""
Analyze market conditions and select the BEST options strategy for {symbol} at ₹{current_price}.

=== MARKET CONDITIONS ===
Current Price: ₹{current_price}
Trend: {market_data.get('trend', 'Neutral')}
Volatility: {market_data.get('volatility', 'Normal')}
Market Sentiment: {market_data.get('sentiment', 'Neutral')}
Time to Earnings: {market_data.get('days_to_earnings', 'Unknown')}

=== AI SIGNAL ===
Action: {ai_signal.get('action', 'HOLD')}
Confidence: {ai_signal.get('confidence', 0.5):.0%}
Target Price: ₹{ai_signal.get('target_price', current_price)}
Risk Level: {ai_signal.get('risk_level', 'MEDIUM')}

=== AVAILABLE STRATEGIES ===
1. STRADDLE: Long both call and put at same strike (profit on large move in either direction)
2. STRANGLE: Long call and put at different strikes (spreads cost, lower profit)
3. IRON_CONDOR: Sell both call and put spreads (high probability, limited profit)
4. BULL_CALL_SPREAD: Buy call, sell higher call (directional bullish, limited risk)
5. BULL_PUT_SPREAD: Sell put, buy lower put (directional bullish, high probability)
6. DIRECTIONAL_CALL: Buy call (bullish, unlimited upside, defined risk)
7. DIRECTIONAL_PUT: Buy put (bearish, unlimited downside, defined risk)

=== SELECTION CRITERIA ===
- Risk Profile: {portfolio_risk_profile}
- Expected Win Probability: Target 60%+
- Risk/Reward Ratio: Target 1:2 or better
- Capital Efficiency: Minimize capital tied up
- Pre-earnings Volatility: Consider expectations

=== RESPONSE FORMAT ===
Provide ONLY valid JSON (no markdown):
{{
  "strategy": "STRADDLE/STRANGLE/IRON_CONDOR/CALL_SPREAD/PUT_SPREAD/DIRECTIONAL_CALL/DIRECTIONAL_PUT",
  "reason": "Why this strategy is optimal for current conditions",
  "strike_price": {current_price},
  "expiry_days": 7,
  "probability_of_profit": 0.65,
  "expected_return": 15,
  "risk_reward_ratio": 1.5,
  "capital_required": 5000,
  "max_profit_potential": 10000,
  "max_loss_potential": 2500,
  "key_factors": ["Earnings within X days", "High IV expansion expected", "Support/resistance nearby"],
  "warnings": ["Execution near market close", "Wide bid-ask spreads"],
  "full_reasoning": "Detailed explanation of why this strategy was selected"
}}
"""
            
            message = self.client.messages.create(
                model=self.model,
                max_tokens=800,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            response_text = message.content[0].text
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            return json.loads(response_text[json_start:json_end])
        except Exception as e:
            logger.error(f"Claude strategy selection error: {e}")
            return {
                "strategy": "DIRECTIONAL_CALL",
                "reason": "Fallback strategy",
                "probability_of_profit": 0.50,
                "expected_return": 10,
                "risk_reward_ratio": 1
            }
    
    # ============ STRATEGY IMPLEMENTATIONS ============
    
    def _straddle(
        self,
        symbol: str,
        current_price: float,
        options_chain: List[Dict],
        market_data: Dict,
        ai_signal: Dict
    ) -> Dict:
        """
        STRADDLE: Long call + Long put at same strike
        Profit on large move in either direction
        Lose on small move (theta decay)
        Best for: High volatility expected
        """
        atm_strike = self._find_atm_strike(current_price, options_chain)
        
        call = self._find_contract(options_chain, atm_strike, "CALL")
        put = self._find_contract(options_chain, atm_strike, "PUT")
        
        entry_cost = (call.get("ask_price", 0) + put.get("ask_price", 0)) * 100
        max_profit = float('inf')  # Unlimited upside
        max_loss = entry_cost  # Limited to premium paid
        
        return {
            "strike": atm_strike,
            "long_call": call.get("symbol", ""),
            "long_put": put.get("symbol", ""),
            "entry_price_per_spread": entry_cost / 100,
            "max_profit": max_profit,
            "max_loss": max_loss,
            "breakeven_up": atm_strike + (entry_cost / 100),
            "breakeven_down": atm_strike - (entry_cost / 100),
            "probability_of_profit": 0.50,
            "best_when": "High volatility expected, range-bound market"
        }
    
    def _strangle(
        self,
        symbol: str,
        current_price: float,
        options_chain: List[Dict],
        market_data: Dict,
        ai_signal: Dict
    ) -> Dict:
        """
        STRANGLE: Long OTM call + Long OTM put
        Lower cost than straddle
        Requires larger move to profit
        Best for: Lower cost volatility play
        """
        call_strike = self._find_otm_strike(current_price, options_chain, "above", offset_percent=1.0)
        put_strike = self._find_otm_strike(current_price, options_chain, "below", offset_percent=1.0)
        
        call = self._find_contract(options_chain, call_strike, "CALL")
        put = self._find_contract(options_chain, put_strike, "PUT")
        
        entry_cost = (call.get("ask_price", 0) + put.get("ask_price", 0)) * 100
        
        return {
            "call_strike": call_strike,
            "put_strike": put_strike,
            "long_call": call.get("symbol", ""),
            "long_put": put.get("symbol", ""),
            "entry_price_per_spread": entry_cost / 100,
            "max_profit": float('inf'),
            "max_loss": entry_cost,
            "breakeven_up": call_strike + (entry_cost / 100),
            "breakeven_down": put_strike - (entry_cost / 100),
            "probability_of_profit": 0.40,
            "best_when": "High volatility at lower cost, earnings play"
        }
    
    def _iron_condor(
        self,
        symbol: str,
        current_price: float,
        options_chain: List[Dict],
        market_data: Dict,
        ai_signal: Dict
    ) -> Dict:
        """
        IRON CONDOR: Short call spread + Short put spread
        Profit on no movement or small move
        Limited risk, high probability
        Best for: Neutral outlook, high probability
        """
        # sell call spread
        short_call = self._find_otm_strike(current_price, options_chain, "above", offset_percent=1.5)
        long_call = self._find_otm_strike(current_price, options_chain, "above", offset_percent=3.0)
        
        # Short put spread
        short_put = self._find_otm_strike(current_price, options_chain, "below", offset_percent=1.5)
        long_put = self._find_otm_strike(current_price, options_chain, "below", offset_percent=3.0)
        
        call_spread_width = long_call - short_call
        put_spread_width = short_put - long_put
        
        credit = (
            (self._find_contract(options_chain, short_call, "CALL").get("bid_price", 0) -
             self._find_contract(options_chain, long_call, "CALL").get("ask_price", 0)) +
            (self._find_contract(options_chain, short_put, "PUT").get("bid_price", 0) -
             self._find_contract(options_chain, long_put, "PUT").get("ask_price", 0))
        ) * 100
        
        max_profit = credit
        max_loss = (min(call_spread_width, put_spread_width) * 100) - credit
        
        return {
            "short_call": short_call,
            "long_call": long_call,
            "short_put": short_put,
            "long_put": long_put,
            "credit_received": credit / 100,
            "max_profit": max_profit,
            "max_loss": max_loss,
            "probability_of_profit": 0.70,
            "best_when": "Neutral outlook, high probability strategy"
        }
    
    def _bull_call_spread(
        self,
        symbol: str,
        current_price: float,
        options_chain: List[Dict],
        market_data: Dict,
        ai_signal: Dict
    ) -> Dict:
        """
        BULL CALL SPREAD: Long call + Short higher call
        Lower cost than long call
        Limited profit potential
        Best for: Mildly bullish, defined risk
        """
        long_strike = self._find_atm_strike(current_price, options_chain)
        short_strike = self._find_otm_strike(current_price, options_chain, "above", offset_percent=2.0)
        
        long_call = self._find_contract(options_chain, long_strike, "CALL")
        short_call = self._find_contract(options_chain, short_strike, "CALL")
        
        debit = (long_call.get("ask_price", 0) - short_call.get("bid_price", 0)) * 100
        max_profit = ((short_strike - long_strike) * 100) - debit
        
        return {
            "long_call_strike": long_strike,
            "short_call_strike": short_strike,
            "debit_paid": debit / 100,
            "max_profit": max_profit,
            "max_loss": debit,
            "breakeven": long_strike + (debit / 100),
            "probability_of_profit": 0.60,
            "best_when": "Moderately bullish, known risk"
        }
    
    def _bull_put_spread(
        self,
        symbol: str,
        current_price: float,
        options_chain: List[Dict],
        market_data: Dict,
        ai_signal: Dict
    ) -> Dict:
        """
        BULL PUT SPREAD: Sell OTM put + Buy lower OTM put
        High probability strategy
        Limited profit and risk
        Best for: High probability trades
        """
        short_strike = self._find_otm_strike(current_price, options_chain, "below", offset_percent=1.5)
        long_strike = self._find_otm_strike(current_price, options_chain, "below", offset_percent=3.0)
        
        short_put = self._find_contract(options_chain, short_strike, "PUT")
        long_put = self._find_contract(options_chain, long_strike, "PUT")
        
        credit = (short_put.get("bid_price", 0) - long_put.get("ask_price", 0)) * 100
        max_profit = credit
        max_loss = ((short_strike - long_strike) * 100) - credit
        
        return {
            "short_put_strike": short_strike,
            "long_put_strike": long_strike,
            "credit_received": credit / 100,
            "max_profit": max_profit,
            "max_loss": max_loss,
            "breakeven": short_strike - (credit / 100),
            "probability_of_profit": 0.70,
            "best_when": "Bullish or neutral, high probability"
        }
    
    def _directional_call(
        self,
        symbol: str,
        current_price: float,
        options_chain: List[Dict],
        market_data: Dict,
        ai_signal: Dict
    ) -> Dict:
        """Long call - Bullish position"""
        strike = self._find_atm_strike(current_price, options_chain)
        contract = self._find_contract(options_chain, strike, "CALL")
        
        return {
            "strike": strike,
            "contract": contract.get("symbol", ""),
            "entry_price": contract.get("ask_price", 0),
            "max_profit": float('inf'),
            "max_loss": contract.get("ask_price", 0) * 100,
            "breakeven": strike + contract.get("ask_price", 0),
            "probability_of_profit": 0.45,
            "best_when": "Bullish outlook"
        }
    
    def _directional_put(
        self,
        symbol: str,
        current_price: float,
        options_chain: List[Dict],
        market_data: Dict,
        ai_signal: Dict
    ) -> Dict:
        """Long put - Bearish position"""
        strike = self._find_atm_strike(current_price, options_chain)
        contract = self._find_contract(options_chain, strike, "PUT")
        
        return {
            "strike": strike,
            "contract": contract.get("symbol", ""),
            "entry_price": contract.get("ask_price", 0),
            "max_profit": strike * 100 - (contract.get("ask_price", 0) * 100),
            "max_loss": contract.get("ask_price", 0) * 100,
            "breakeven": strike - contract.get("ask_price", 0),
            "probability_of_profit": 0.45,
            "best_when": "Bearish outlook"
        }
    
    # ============ UTILITY METHODS ============
    
    def _find_atm_strike(self, current_price: float, options_chain: List[Dict]) -> float:
        """Find strike closest to current price"""
        strikes = set()
        for opt in options_chain:
            strikes.add(opt.get("strike"))
        
        return min(strikes, key=lambda x: abs(x - current_price)) if strikes else current_price
    
    def _find_otm_strike(
        self,
        current_price: float,
        options_chain: List[Dict],
        direction: str,
        offset_percent: float = 1.0
    ) -> float:
        """Find OTM strike at specified distance"""
        target_price = current_price * (1 + offset_percent / 100) if direction == "above" else current_price * (1 - offset_percent / 100)
        
        strikes = set()
        for opt in options_chain:
            strikes.add(opt.get("strike"))
        
        if direction == "above":
            return min([s for s in strikes if s >= target_price], default=max(strikes) if strikes else current_price)
        else:
            return max([s for s in strikes if s <= target_price], default=min(strikes) if strikes else current_price)
    
    def _find_contract(self, options_chain: List[Dict], strike: float, contract_type: str) -> Dict:
        """Find contract in chain"""
        for opt in options_chain:
            if opt.get("strike") == strike and opt.get("type") == contract_type:
                return opt
        return {}
    
    def _default_strategy(
        self,
        symbol: str,
        current_price: float,
        options_chain: List[Dict]
    ) -> Dict:
        """Default fallback strategy"""
        return {
            "strategy": "DIRECTIONAL_CALL",
            "setup": self._directional_call(symbol, current_price, options_chain, {}, {"action": "BUY"}),
            "reason": "Default bullish strategy",
            "probability_of_profit": 0.45
        }
