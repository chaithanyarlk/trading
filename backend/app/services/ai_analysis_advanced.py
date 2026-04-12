"""
Advanced AI Analysis Engine - Local Claude for comprehensive market analysis
Performs multi-factor analysis using technical indicators, market context, and risk assessment
Supports both Anthropic Claude and Ollama local LLMs
"""
import logging
from typing import Dict, List, Optional, Tuple
import json
from app.core.config import settings
from app.services.ai_provider import ai_provider
from datetime import datetime

logger = logging.getLogger(__name__)

class AdvancedAIAnalysisEngine:
    """
    Comprehensive AI analysis using local Claude model
    Analyzes:
    - RSI, MACD, Bollinger Bands, Moving Averages
    - Volume and volatility patterns
    - Trend detection and breakout signals
    - Multi-factor decision making
    """
    
    def __init__(self):
        self.ai_provider = ai_provider
        self.max_retries = 3
        logger.info(f"AI Analysis Engine initialized with {self.ai_provider.provider}")

    
    async def analyze_stock_comprehensive(
        self,
        symbol: str,
        current_price: float,
        market_data: Dict,
        technical_indicators: Dict,
        market_context: Dict,
        portfolio_risk_profile: str = "BALANCED"
    ) -> Dict:
        """
        Comprehensive AI analysis combining all factors
        
        Args:
            symbol: Stock symbol
            current_price: Current market price
            market_data: OHLCV data
            technical_indicators: All calculated indicators
            market_context: Market breadth, sentiment, etc.
            portfolio_risk_profile: CONSERVATIVE, BALANCED, AGGRESSIVE
        
        Returns: {
            "action": "BUY/SELL/HOLD",
            "confidence": 0-1,
            "score": 0-100,
            "reasoning": "Detailed reasoning",
            "risk_level": "LOW/MEDIUM/HIGH",
            "target_price": float,
            "stop_loss": float,
            "position_size_percent": float,
            "indicators_supporting": [...],
            "market_factors": {...},
            "ai_confidence": 0-1,
            "recommendation": "Specific trading action"
        }
        """
        try:
            # Prepare analysis context
            analysis_context = self._prepare_analysis_context(
                symbol, current_price, market_data, technical_indicators, market_context
            )
            
            # Use AI for deep analysis
            prompt = self._build_analysis_prompt(
                symbol, analysis_context, portfolio_risk_profile
            )
            
            # Call unified AI provider (supports both Anthropic and Ollama)
            response_text = self.ai_provider.analyze(prompt, system_prompt="You are an expert financial analyst.", max_tokens=2000)
            
            # Parse response
            analysis = self._parse_analysis_response(response_text, current_price)
            
            logger.info(f"AI Analysis for {symbol}: {analysis['action']} (confidence: {analysis['confidence']:.0%})")
            return analysis
            
        except Exception as e:
            logger.error(f"Error in comprehensive analysis: {e}")
            return self._fallback_analysis(symbol, current_price, technical_indicators)
    
    def _prepare_analysis_context(
        self,
        symbol: str,
        current_price: float,
        market_data: Dict,
        technical_indicators: Dict,
        market_context: Dict
    ) -> Dict:
        """Prepare comprehensive context for Claude analysis"""
        
        return {
            "symbol": symbol,
            "price": current_price,
            "market_data": market_data,
            "indicators": {
                "rsi": technical_indicators.get("rsi", {}),
                "macd": technical_indicators.get("macd", {}),
                "bollinger_bands": technical_indicators.get("bb", {}),
                "moving_averages": technical_indicators.get("ma", {}),
                "volume": technical_indicators.get("volume", {}),
                "volatility": technical_indicators.get("volatility", {}),
            },
            "market_context": market_context,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _build_analysis_prompt(
        self,
        symbol: str,
        context: Dict,
        portfolio_risk_profile: str
    ) -> str:
        """Build comprehensive analysis prompt for Claude"""
        
        indicators = context["indicators"]
        market_context = context["market_context"]
        
        prompt = f"""
You are an expert financial analyst. Perform a COMPREHENSIVE analysis of {symbol} at ₹{context['price']}.

=== TECHNICAL INDICATORS ===
RSI (Relative Strength Index):
- Value: {indicators['rsi'].get('value', 'N/A')}
- Status: {indicators['rsi'].get('status', 'Neutral')} ({indicators['rsi'].get('interpretation', '')})

MACD (Moving Average Convergence Divergence):
- Value: {indicators['macd'].get('value', 'N/A')}
- Signal: {indicators['macd'].get('signal', 'Neutral')}
- Histogram: {indicators['macd'].get('histogram', 'N/A')}

Bollinger Bands:
- Upper: {indicators['bollinger_bands'].get('upper', 'N/A')}
- Middle: {indicators['bollinger_bands'].get('middle', 'N/A')}
- Lower: {indicators['bollinger_bands'].get('lower', 'N/A')}
- Position: {indicators['bollinger_bands'].get('position', 'Middle')}

Moving Averages:
- SMA 20: {indicators['moving_averages'].get('sma_20', 'N/A')}
- SMA 50: {indicators['moving_averages'].get('sma_50', 'N/A')}
- SMA 200: {indicators['moving_averages'].get('sma_200', 'N/A')}
- Trend: {indicators['moving_averages'].get('trend', 'Neutral')}

Volume Analysis:
- Current Volume: {indicators['volume'].get('current', 'N/A')}
- Average Volume: {indicators['volume'].get('average', 'N/A')}
- Signal: {indicators['volume'].get('signal', 'Neutral')}

Volatility:
- ATR: {indicators['volatility'].get('atr', 'N/A')}
- Level: {indicators['volatility'].get('level', 'Normal')}

=== MARKET CONTEXT ===
- Market Sentiment: {market_context.get('sentiment', 'Neutral')}
- Market Advance/Decline: {market_context.get('ad_ratio', 'N/A')}
- VIX Level: {market_context.get('vix', 'N/A')}
- Sector Performance: {market_context.get('sector_performance', 'Mixed')}
- Time of Day: {market_context.get('time_of_day', 'During Market')}

=== PORTFOLIO RISK PROFILE ===
Risk Profile: {portfolio_risk_profile}

=== YOUR ANALYSIS TASK ===

1. IDENTIFY PRIMARY SIGNALS:
   - Which indicators show the strongest buy/sell signals?
   - Are indicators aligned or conflicting?
   - What's the agreement level among indicators?

2. ASSESS TREND & MOMENTUM:
   - Is the trend established (up/down/sideways)?
   - Is momentum building or fading?
   - Are there reversal signals?

3. EVALUATE RISK:
   - What are the key support and resistance levels?
   - What's a reasonable stop-loss level?
   - What's the risk/reward ratio?

4. DETERMINE ENTRY & EXIT:
   - Should we BUY, SELL, or HOLD?
   - At what price should we set stop-loss?
   - What's a realistic target price?
   - What position size is appropriate for our risk profile?

5. CALCULATE CONFIDENCE:
   - How many indicators support this decision? (score 0-100)
   - How strong are the signals?
   - What's your confidence percentage (0-100)?

=== RESPONSE FORMAT ===
Provide your analysis in this EXACT JSON format (no markdown, pure JSON):
{{
  "action": "BUY/SELL/HOLD",
  "confidence": 0.85,
  "score": 85,
  "reasoning": "Detailed 3-4 sentence reasoning explaining your decision",
  "indicators_analysis": {{
    "rsi_signal": "Overbought/Oversold/Neutral with details",
    "macd_signal": "Details about MACD setup",
    "bb_signal": "Reversal/Continuation/Range signals",
    "ma_signal": "Trend alignment details",
    "volume_signal": "Volume confirmation details"
  }},
  "risk_level": "LOW/MEDIUM/HIGH",
  "target_price": {context['price'] * 1.05},
  "stop_loss": {context['price'] * 0.95},
  "position_size_percent": 2.5,
  "key_levels": {{
    "support1": {context['price'] * 0.97},
    "support2": {context['price'] * 0.93},
    "resistance1": {context['price'] * 1.03},
    "resistance2": {context['price'] * 1.08}
  }},
  "indicators_supporting": ["RSI", "MACD", "Volume"],
  "indicators_conflicting": [],
  "market_factors": {{
    "trend": "Up/Down/Sideways",
    "momentum": "Strong/Moderate/Weak",
    "volatility": "High/Normal/Low",
    "market_sentiment": "Bullish/Neutral/Bearish"
  }},
  "recommendation": "Specific trading action: e.g., 'Buy on dips below ₹2840 with stop loss at ₹2820'",
  "risk_factors": ["Mention any risks specific to this trade"],
  "profit_targets": [{{
    "level": {context['price'] * 1.03},
    "profit_percent": 3,
    "take_profit_percent": 25
  }}, ...],
  "alerts": "Any specific conditions to watch"
}}

IMPORTANT: 
- Be data-driven and specific
- Consider all indicators in your analysis
- Align with risk profile
- Provide actionable recommendations
- Include specific price levels
"""
        
        return prompt
    
    def _parse_analysis_response(self, response_text: str, current_price: float) -> Dict:
        """Parse Claude's analysis response"""
        try:
            # Extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            json_str = response_text[json_start:json_end]
            
            analysis = json.loads(json_str)
            
            # Validate and normalize
            analysis['confidence'] = min(1.0, max(0, analysis.get('confidence', 0.5)))
            analysis['score'] = analysis.get('score', int(analysis['confidence'] * 100))
            
            # Ensure required fields
            analysis.setdefault('action', 'HOLD')
            analysis.setdefault('reasoning', 'Unable to generate reasoning')
            analysis.setdefault('risk_level', 'MEDIUM')
            analysis.setdefault('target_price', current_price * 1.05)
            analysis.setdefault('stop_loss', current_price * 0.98)
            
            return analysis
        except Exception as e:
            logger.error(f"Error parsing analysis response: {e}")
            return self._fallback_analysis_structure(current_price)
    
    def _fallback_analysis(
        self,
        symbol: str,
        current_price: float,
        technical_indicators: Dict
    ) -> Dict:
        """Fallback analysis when Claude is unavailable"""
        
        logger.warning(f"Using fallback analysis for {symbol}")
        
        # Extract signals from indicators
        rsi = technical_indicators.get("rsi", {}).get("signal", "NEUTRAL")
        macd = technical_indicators.get("macd", {}).get("signal", "NEUTRAL")
        bb = technical_indicators.get("bb", {}).get("signal", "NEUTRAL")
        
        signal_count_buy = sum([1 for s in [rsi, macd, bb] if s == "BUY"])
        signal_count_sell = sum([1 for s in [rsi, macd, bb] if s == "SELL"])
        
        if signal_count_buy > signal_count_sell:
            action = "BUY"
            confidence = 0.6 + (signal_count_buy * 0.1)
        elif signal_count_sell > signal_count_buy:
            action = "SELL"
            confidence = 0.6 + (signal_count_sell * 0.1)
        else:
            action = "HOLD"
            confidence = 0.5
        
        return {
            "action": action,
            "confidence": min(1.0, confidence),
            "score": int(confidence * 100),
            "reasoning": f"Technical indicators align: RSI={rsi}, MACD={macd}, BB={bb}",
            "risk_level": "MEDIUM",
            "target_price": current_price * 1.05,
            "stop_loss": current_price * 0.98,
            "position_size_percent": 2.0,
            "indicators_supporting": [s for s in [rsi, macd, bb] if s == action],
            "recommendation": f"{action} with stop loss at ₹{current_price * 0.98:.2f}"
        }
    
    def _fallback_analysis_structure(self, current_price: float) -> Dict:
        """Minimal fallback structure"""
        return {
            "action": "HOLD",
            "confidence": 0.5,
            "score": 50,
            "reasoning": "Analysis unavailable - manual review recommended",
            "risk_level": "HIGH",
            "target_price": current_price * 1.05,
            "stop_loss": current_price * 0.95,
            "position_size_percent": 1.0,
            "indicators_supporting": [],
            "recommendation": "Unable to generate recommendation - AI analysis failed"
        }
    
    async def generate_trade_explanation(
        self,
        symbol: str,
        action: str,
        analysis: Dict,
        indicators_summary: str
    ) -> str:
        """
        Generate detailed human-readable explanation for a trade
        """
        try:
            prompt = f"""
Generate a brief, professional explanation (2-3 sentences) for this trade decision:

Stock: {symbol}
Action: {action}
AI Confidence: {analysis.get('confidence', 0):.0%}
Reasoning: {analysis.get('reasoning', '')}
Key Indicators: {indicators_summary}

Format: Professional trader explanation focusing on the technical setup that triggered this decision.
"""
            
            message = self.client.messages.create(
                model=self.model,
                max_tokens=300,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return message.content[0].text
        except Exception as e:
            logger.error(f"Error generating explanation: {e}")
            return analysis.get('reasoning', 'Trade executed based on technical analysis')
    
    async def analyze_portfolio_health(
        self,
        portfolio_holdings: List[Dict],
        portfolio_performance: Dict,
        market_data: Dict
    ) -> Dict:
        """
        AI analysis of overall portfolio health and recommendations
        """
        try:
            context = {
                "holdings": portfolio_holdings,
                "performance": portfolio_performance,
                "market": market_data
            }
            
            prompt = f"""
Analyze this trading portfolio and provide insights:

Portfolio Value: ₹{portfolio_performance.get('total_value', 0):,.0f}
Total P&L: ₹{portfolio_performance.get('total_pnl', 0):,.0f} ({portfolio_performance.get('total_pnl_percent', 0):.2f}%)
Win Rate: {portfolio_performance.get('win_rate', 0):.1f}%
Number of Holdings: {len(portfolio_holdings)}

Top Holdings:
{chr(10).join([f"- {h.get('symbol')}: ₹{h.get('current_value', 0):,.0f} ({h.get('pnl_percent', 0):.2f}%)" for h in portfolio_holdings[:5]])}

Provide:
1. Portfolio health assessment
2. Risk exposure analysis
3. Rebalancing suggestions
4. Key risks to monitor
5. Opportunities to consider

Keep response concise and actionable.
"""
            
            message = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return {
                "assessment": message.content[0].text,
                "timestamp": datetime.utcnow().isoformat(),
                "holdings_count": len(portfolio_holdings),
                "performance": portfolio_performance
            }
        except Exception as e:
            logger.error(f"Error analyzing portfolio: {e}")
            return {
                "assessment": "Portfolio analysis unavailable",
                "timestamp": datetime.utcnow().isoformat(),
                "holdings_count": len(portfolio_holdings),
                "performance": portfolio_performance
            }

# Global instance
ai_engine: Optional['AdvancedAIAnalysisEngine'] = None

async def get_ai_engine() -> AdvancedAIAnalysisEngine:
    """Get or create AI analysis engine"""
    global ai_engine
    if not ai_engine:
        ai_engine = AdvancedAIAnalysisEngine()
    return ai_engine
