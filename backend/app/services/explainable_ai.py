"""
Explainable AI Module - Provides detailed reasoning for every trade decision
Stores comprehensive trade logs with complete transparency
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime
import json
import anthropic
from app.core.config import settings

logger = logging.getLogger(__name__)

class ExplainableAILogger:
    """
    Comprehensive AI reasoning logger
    Stores detailed reasoning for every trade and provides explainability
    """
    
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.CLAUDE_API_KEY)
        self.model = settings.CLAUDE_MODEL
        self.trade_logs = []
    
    async def log_trade_with_reasoning(
        self,
        symbol: str,
        action: str,
        entry_price: float,
        quantity: int,
        ai_analysis: Dict,
        technical_context: Dict,
        market_context: Dict,
        trade_id: Optional[str] = None,
        mode: str = "PAPER"
    ) -> Dict:
        """
        Create comprehensive trade record with full AI reasoning
        
        Returns detailed trade explanation and logging data
        """
        
        timestamp = datetime.utcnow().isoformat()
        
        # Generate detailed explanation
        explanation = await self._generate_detailed_explanation(
            symbol, action, ai_analysis, technical_context, market_context
        )
        
        trade_record = {
            "trade_id": trade_id or f"{symbol}_{timestamp}",
            "symbol": symbol,
            "action": action,
            "timestamp": timestamp,
            "mode": mode,
            "entry": {
                "price": entry_price,
                "quantity": quantity,
                "value": entry_price * quantity,
                "time": timestamp
            },
            "ai_reasoning": {
                "confidence": ai_analysis.get("confidence", 0),
                "score": ai_analysis.get("score", 0),
                "decision": ai_analysis.get("reasoning", ""),
                "risk_level": ai_analysis.get("risk_level", "MEDIUM"),
                "target_price": ai_analysis.get("target_price", entry_price * 1.05),
                "stop_loss": ai_analysis.get("stop_loss", entry_price * 0.98),
            },
            "technical_analysis": {
                "indicators_used": technical_context.get("indicators", []),
                "rsi": technical_context.get("rsi", {}),
                "macd": technical_context.get("macd", {}),
                "bollinger_bands": technical_context.get("bb", {}),
                "moving_averages": technical_context.get("ma", {}),
                "volume": technical_context.get("volume", {}),
            },
            "market_condition": market_context,
            "detailed_explanation": explanation,
            "indicators_agreement": self._calculate_indicator_agreement(technical_context),
            "decision_confidence_factors": self._extract_confidence_factors(ai_analysis),
        }
        
        self.trade_logs.append(trade_record)
        
        logger.info(f"Trade logged: {symbol} {action} @ ₹{entry_price} (ID: {trade_record['trade_id']})")
        
        return trade_record
    
    async def _generate_detailed_explanation(
        self,
        symbol: str,
        action: str,
        ai_analysis: Dict,
        technical_context: Dict,
        market_context: Dict
    ) -> Dict:
        """Generate detailed AI explanation for a trade"""
        
        try:
            prompt = f"""
Generate a comprehensive explanation for this {action} trade on {symbol}.

=== DECISION DATA ===
Action: {action}
Confidence: {ai_analysis.get('confidence', 0):.0%}
AI Score: {ai_analysis.get('score', 0)}/100
Target Price: ₹{ai_analysis.get('target_price', 0)}
Stop Loss: ₹{ai_analysis.get('stop_loss', 0)}

=== TECHNICAL SETUP ===
RSI: {technical_context.get('rsi', {}).get('value', 'N/A')} ({technical_context.get('rsi', {}).get('signal', 'Neutral')})
MACD: {technical_context.get('macd', {}).get('signal', 'Neutral')}
Bollinger Bands: {technical_context.get('bb', {}).get('position', 'Middle')}
Trend: {technical_context.get('ma', {}).get('trend', 'Neutral')}
Volume: {technical_context.get('volume', {}).get('signal', 'Neutral')}

=== MARKET CONTEXT ===
Sentiment: {market_context.get('sentiment', 'Neutral')}
Market Advance/Decline: {market_context.get('ad_ratio', 'N/A')}
VIX Level: {market_context.get('vix', 'N/A')}

Provide:
1. **Why This Trade** (2-3 sentences explaining the setup)
2. **Technical Confirmation** (which indicators confirmed the move)
3. **Risk Management** (why this stop loss and target)
4. **Market Context** (how broader market supports this)
5. **Key Risks** (what could cause this trade to fail)
6. **Exit Strategy** (when to take profits/stop)

Format response as structured JSON for dashboard display.
"""
            
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            response_text = message.content[0].text
            
            # Try to parse as JSON
            try:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    return json.loads(response_text[json_start:json_end])
            except:
                pass
            
            # Return as text if not JSON
            return {
                "explanation": response_text,
                "format": "text"
            }
        except Exception as e:
            logger.error(f"Error generating explanation: {e}")
            return {
                "explanation": f"Trade decision based on {ai_analysis.get('reasoning', 'technical analysis')}",
                "format": "text"
            }
    
    def _calculate_indicator_agreement(self, technical_context: Dict) -> Dict:
        """Calculate how many indicators agree with the signal"""
        
        signals = []
        for indicator_type, data in technical_context.items():
            if isinstance(data, dict) and "signal" in data:
                signals.append(data["signal"])
        
        buy_signals = sum(1 for s in signals if s == "BUY")
        sell_signals = sum(1 for s in signals if s == "SELL")
        total_signals = len(signals)
        
        return {
            "total_indicators": total_signals,
            "buy_signals": buy_signals,
            "sell_signals": sell_signals,
            "agreement_percent": (max(buy_signals, sell_signals) / total_signals * 100) if total_signals > 0 else 0,
            "consensus": "STRONG" if max(buy_signals, sell_signals) >= total_signals * 0.7 else "WEAK"
        }
    
    def _extract_confidence_factors(self, ai_analysis: Dict) -> List[str]:
        """Extract factors that support confidence in this decision"""
        
        factors = []
        
        confidence = ai_analysis.get("confidence", 0)
        if confidence >= 0.8:
            factors.append("Very high AI confidence (>80%)")
        elif confidence >= 0.6:
            factors.append("Good AI confidence (60-80%)")
        
        risk_level = ai_analysis.get("risk_level", "MEDIUM")
        if risk_level == "LOW":
            factors.append("Low risk trade")
        elif risk_level == "HIGH":
            factors.append("High risk trade - treat with caution")
        
        if ai_analysis.get("reasoning"):
            # Try to extract key factors from reasoning
            reasoning = ai_analysis["reasoning"].lower()
            if "breakout" in reasoning:
                factors.append("Technical breakout confirmed")
            if "oversold" in reasoning:
                factors.append("Oversold condition detected")
            if "support" in reasoning:
                factors.append("Support level hold detected")
        
        return factors if factors else ["Trade based on technical setup"]
    
    def get_trade_log(self, trade_id: Optional[str] = None) -> List[Dict]:
        """Retrieve trade logs"""
        if trade_id:
            return [t for t in self.trade_logs if t["trade_id"] == trade_id]
        return self.trade_logs
    
    def export_trade_logs(self, format: str = "json") -> str:
        """Export trade logs in specified format"""
        if format == "json":
            return json.dumps(self.trade_logs, indent=2, default=str)
        elif format == "csv":
            return self._convert_to_csv()
        else:
            return json.dumps(self.trade_logs, indent=2, default=str)
    
    def _convert_to_csv(self) -> str:
        """Convert trade logs to CSV format"""
        import csv
        from io import StringIO
        
        output = StringIO()
        if not self.trade_logs:
            return ""
        
        writer = csv.DictWriter(output, fieldnames=[
            "trade_id", "symbol", "action", "timestamp", "mode",
            "entry_price", "entry_quantity", "entry_value",
            "ai_confidence", "ai_score", "target_price", "stop_loss",
            "risk_level"
        ])
        
        writer.writeheader()
        
        for trade in self.trade_logs:
            row = {
                "trade_id": trade.get("trade_id"),
                "symbol": trade.get("symbol"),
                "action": trade.get("action"),
                "timestamp": trade.get("timestamp"),
                "mode": trade.get("mode"),
                "entry_price": trade["entry"].get("price"),
                "entry_quantity": trade["entry"].get("quantity"),
                "entry_value": trade["entry"].get("value"),
                "ai_confidence": f"{trade['ai_reasoning'].get('confidence', 0):.0%}",
                "ai_score": trade['ai_reasoning'].get('score'),
                "target_price": trade['ai_reasoning'].get('target_price'),
                "stop_loss": trade['ai_reasoning'].get('stop_loss'),
                "risk_level": trade['ai_reasoning'].get('risk_level'),
            }
            writer.writerow(row)
        
        return output.getvalue()
    
    def generate_trade_summary_for_dashboard(self, trade_id: str) -> Dict:
        """Generate trade summary for dashboard display"""
        
        logs = self.get_trade_log(trade_id)
        if not logs:
            return {"error": "Trade not found"}
        
        trade = logs[0]
        
        return {
            "trade_id": trade["trade_id"],
            "symbol": trade["symbol"],
            "action": trade["action"],
            "status": "OPEN",  # Would be updated when trade exits
            "entry": trade["entry"],
            "ai_reasoning": trade["ai_reasoning"],
            "technical_summary": {
                "indicators_agreement": trade.get("indicators_agreement", {}),
                "key_levels": {
                    "target": trade["ai_reasoning"].get("target_price"),
                    "stop_loss": trade["ai_reasoning"].get("stop_loss"),
                    "entry": trade["entry"]["price"]
                }
            },
            "explanation": trade.get("detailed_explanation", {}),
            "confidence_factors": trade.get("decision_confidence_factors", []),
            "market_context": trade.get("market_condition", {}),
            "timestamp": trade["timestamp"]
        }
    
    async def generate_trade_exit_reasoning(
        self,
        trade_record: Dict,
        exit_price: float,
        exit_reason: str,  # PROFIT_TARGET, STOP_LOSS, MANUAL, TIME_EXIT
        pnl: float
    ) -> Dict:
        """Generate reasoning for trade exit"""
        
        try:
            prompt = f"""
Analyze this completed trade and explain the exit decision:

=== TRADE DETAILS ===
Symbol: {trade_record.get('symbol')}
Action: {trade_record.get('action')}
Entry Price: ₹{trade_record['entry'].get('price')}
Exit Price: ₹{exit_price}
Exit Reason: {exit_reason}
P&L: ₹{pnl} ({(pnl / (trade_record['entry'].get('price') * trade_record['entry'].get('quantity')) * 100):.2f}%)

=== ORIGINAL TRADE SETUP ===
Target: ₹{trade_record['ai_reasoning'].get('target_price')}
Stop Loss: ₹{trade_record['ai_reasoning'].get('stop_loss')}
AI Confidence: {trade_record['ai_reasoning'].get('confidence'):.0%}

Provide:
1. Whether the exit was correct
2. Whether the trade played out as expected
3. Lessons learned
4. What to do differently next time

Format as structured JSON.
"""
            
            message = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            response_text = message.content[0].text
            try:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                return json.loads(response_text[json_start:json_end])
            except:
                return {"analysis": response_text}
        except Exception as e:
            logger.error(f"Error generating exit reasoning: {e}")
            return {
                "analysis": f"Trade closed at ₹{exit_price} due to {exit_reason}"
            }

# Global instance
explainable_logger: Optional[ExplainableAILogger] = None

async def get_explainable_logger() -> ExplainableAILogger:
    """Get or create explainable logger"""
    global explainable_logger
    if not explainable_logger:
        explainable_logger = ExplainableAILogger()
    return explainable_logger
