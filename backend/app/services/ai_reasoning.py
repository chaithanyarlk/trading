import logging
from typing import Dict, List, Optional
from app.core.config import settings
from app.models.schemas import TradeSignal, TradeAction
from app.services.ai_provider import ai_provider

logger = logging.getLogger(__name__)

class AIReasoningEngine:
    """AI-powered reasoning engine for trading decisions (supports Anthropic Claude & Ollama)"""
    
    def __init__(self):
        self.ai_provider = ai_provider
        logger.info(f"AI Reasoning Engine initialized with {self.ai_provider.provider}")
    
    async def analyze_trade_signal(
        self,
        asset_name: str,
        asset_id: str,
        current_price: float,
        indicators: Dict,
        market_context: Dict
    ) -> Dict:
        """Use Claude to analyze trade signal and provide AI reasoning"""
        
        if not settings.CLAUDE_API_KEY:
            logger.warning("Claude API key not configured - using basic analysis")
            return self._basic_reasoning(asset_name, indicators)
        
        try:
            prompt = f"""
            Analyze this stock trading opportunity and provide specific, actionable reasoning:
            
            **Stock**: {asset_name} ({asset_id})
            **Current Price**: ₹{current_price:.2f}
            
            **Technical Indicators**:
            {self._format_indicators(indicators)}
            
            **Market Context**:
            {self._format_context(market_context)}
            
            Provide your analysis in this exact format:
            ACTION: [BUY/SELL/HOLD]
            CONFIDENCE: [0-100]%
            REASONING: [2-3 sentences explaining the decision]
            RISK_LEVEL: [LOW/MEDIUM/HIGH]
            TARGET_PRICE: ₹[price]
            STOP_LOSS: ₹[price]
            
            Be concise, data-driven, and specific to this stock's situation.
            """
            
            # Use unified AI provider (Anthropic or Ollama)
            response_text = self.ai_provider.analyze(prompt, system_prompt="You are a financial analyst.", max_tokens=500)
            
            parsed = self._parse_claude_response(response_text, current_price)
            
            logger.info(f"AI analysis for {asset_name}: {parsed['action']} ({parsed['confidence']}%)")
            return parsed
            
        except Exception as e:
            logger.error(f"AI error: {e}")
            return self._basic_reasoning(asset_name, indicators)
    
    async def generate_trade_explanation(
        self,
        trade_data: Dict
    ) -> str:
        """Generate detailed explanation for a trade using Claude"""
        
        if not settings.CLAUDE_API_KEY:
            return "Trade executed based on technical analysis signals"
        
        try:
            prompt = f"""
            Provide a brief (2-3 sentences) professional explanation for this trade decision:
            
            Asset: {trade_data.get('asset_name')}
            Action: {trade_data.get('action')}
            Entry Price: ₹{trade_data.get('price')}
            Indicators Used: {', '.join(trade_data.get('indicators', []))}
            Market Conditions: {trade_data.get('market_conditions', 'Neutral')}
            
            Keep explanation concise and focus on the technical setup that triggered this trade.
            """
            
            # Use unified AI provider
            return self.ai_provider.analyze(prompt, system_prompt="You are a trading analyst.", max_tokens=300)
            
        except Exception as e:
            logger.error(f"Error generating explanation: {e}")
            return "Technical analysis triggered this trade signal"
    
    async def analyze_portfolio_positions(
        self,
        holdings: List[Dict],
        market_data: Dict
    ) -> Dict:
        """Use Claude to analyze current portfolio and suggest adjustments"""
        
        if not settings.CLAUDE_API_KEY:
            return {"recommendations": [], "suggestion": "Monitor current positions"}
        
        try:
            holdings_text = "\n".join([
                f"- {h['asset_name']}: {h['quantity']} @ ₹{h['average_cost']} (Current: ₹{h['current_price']})"
                for h in holdings
            ])
            
            prompt = f"""
            Review this trading portfolio and suggest what to do:
            
            Current Holdings:
            {holdings_text}
            
            Market Conditions: {market_data.get('conditions', 'Neutral')}
            
            Suggest whether to:
            1. HOLD current positions
            2. TRIM positions (sell some)
            3. ADD new positions
            4. ROTATE (sell weak, buy strong)
            
            Keep response to 2-3 sentences with specific reasoning.
            """
            
            # Use unified AI provider
            response_text = self.ai_provider.analyze(prompt, system_prompt="You are a portfolio manager.", max_tokens=300)
            
            return {"suggestion": response_text}
            
        except Exception as e:
            logger.error(f"Error analyzing portfolio: {e}")
            return {"suggestion": "Continue monitoring current positions"}
    
    def _format_indicators(self, indicators: Dict) -> str:
        """Format technical indicators for Claude prompt"""
        formatted = []
        for name, value in indicators.items():
            if isinstance(value, dict):
                formatted.append(f"- {name}: {value.get('current', 'N/A')} (Signal: {value.get('signal', 'N/A')})")
            else:
                formatted.append(f"- {name}: {value}")
        return "\n".join(formatted)
    
    def _format_context(self, context: Dict) -> str:
        """Format market context for Claude prompt"""
        formatted = []
        for key, value in context.items():
            formatted.append(f"- {key.replace('_', ' ').title()}: {value}")
        return "\n".join(formatted) if formatted else "Normal market conditions"
    
    def _parse_claude_response(self, response: str, current_price: float) -> Dict:
        """Parse Claude's response into structured format"""
        
        result = {
            "action": "HOLD",
            "confidence": 50,
            "reasoning": response,
            "risk_level": "MEDIUM",
            "target_price": current_price * 1.05,
            "stop_loss": current_price * 0.98
        }
        
        lines = response.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('ACTION:'):
                action = line.split(':', 1)[1].strip().split()[0]
                result["action"] = "BUY" if "BUY" in action else "SELL" if "SELL" in action else "HOLD"
            elif line.startswith('CONFIDENCE:'):
                try:
                    conf = int(line.split(':', 1)[1].strip().replace('%', ''))
                    result["confidence"] = conf / 100
                except:
                    pass
            elif line.startswith('REASONING:'):
                result["reasoning"] = line.split(':', 1)[1].strip()
            elif line.startswith('RISK_LEVEL:'):
                risk = line.split(':', 1)[1].strip()
                result["risk_level"] = risk if risk in ["LOW", "MEDIUM", "HIGH"] else "MEDIUM"
            elif line.startswith('TARGET_PRICE:'):
                try:
                    target = float(line.split('₹')[1].strip().split()[0])
                    result["target_price"] = target
                except:
                    pass
            elif line.startswith('STOP_LOSS:'):
                try:
                    stop = float(line.split('₹')[1].strip().split()[0])
                    result["stop_loss"] = stop
                except:
                    pass
        
        return result
    
    def _basic_reasoning(self, asset_name: str, indicators: Dict) -> Dict:
        """Fallback reasoning without Claude"""
        
        buy_signals = sum(1 for v in indicators.values() 
                         if isinstance(v, dict) and v.get('signal') == 'BUY')
        sell_signals = sum(1 for v in indicators.values() 
                          if isinstance(v, dict) and v.get('signal') == 'SELL')
        
        if buy_signals > sell_signals:
            action = "BUY"
            confidence = 0.7
        elif sell_signals > buy_signals:
            action = "SELL"
            confidence = 0.7
        else:
            action = "HOLD"
            confidence = 0.5
        
        return {
            "action": action,
            "confidence": confidence,
            "reasoning": f"Technical indicators favor {action} signal",
            "risk_level": "MEDIUM",
            "target_price": None,
            "stop_loss": None
        }
