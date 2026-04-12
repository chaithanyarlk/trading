import logging
from typing import List, Dict, Optional
from datetime import datetime
from app.models.schemas import (
    TradeSignal, OptionsStrategy, MutualFundRecommendation,
    TradeAction, PerformanceMetrics
)
from app.services.technical_analysis import TechnicalAnalysisEngine
from app.services.ai_reasoning import AIReasoningEngine
from app.services.groww_api import GrowwAPIClient

logger = logging.getLogger(__name__)

class TradingEngine:
    """Main trading decision engine with AI reasoning"""
    
    def __init__(self, groww_client: Optional[GrowwAPIClient] = None):
        self.analysis_engine = TechnicalAnalysisEngine()
        self.ai_engine = AIReasoningEngine()
        self.groww_client = groww_client
        self.watched_assets = {}
        self.trade_history = []
    
    async def generate_trade_signals(
        self,
        market_data: Dict[str, Dict],
    ) -> List[TradeSignal]:
        """Generate trade signals from market data with AI reasoning"""
        
        signals = []
        
        for asset_id, data in market_data.items():
            try:
                prices = data.get("prices", [])
                volumes = data.get("volumes", [])
                current_price = data.get("current_price", 0)
                asset_name = data.get("name", asset_id)
                
                if not prices or not volumes:
                    logger.warning(f"Incomplete data for {asset_id}")
                    continue
                
                # Technical analysis
                signal = self.analysis_engine.generate_trade_signal(
                    asset_id=asset_id,
                    asset_name=asset_name,
                    prices=prices,
                    volumes=volumes,
                    current_price=current_price
                )
                
                # AI reasoning with Claude
                ai_analysis = await self.ai_engine.analyze_trade_signal(
                    asset_name=asset_name,
                    asset_id=asset_id,
                    current_price=current_price,
                    indicators={ind.name: ind.value for ind in signal.indicators},
                    market_context={"trend": "analyzing", "volume_strength": "analyzing"}
                )
                
                # Merge AI reasoning into signal
                signal.action = TradeAction.BUY if ai_analysis["action"] == "BUY" else TradeAction.SELL
                signal.confidence = ai_analysis["confidence"]
                signal.reasoning = ai_analysis["reasoning"]
                signal.risk_level = ai_analysis["risk_level"]
                
                # Only include high-confidence signals
                if signal.confidence >= 0.6:
                    signals.append(signal)
                    logger.info(
                        f"Signal generated for {asset_name}: "
                        f"{signal.action.value} (AI confidence: {signal.confidence:.0%})"
                    )
            except Exception as e:
                logger.error(f"Error generating signal for {asset_id}: {e}")
                continue
        
        return signals
    
    async def generate_options_suggestions(
        self, underlying_symbol: str, current_price: float
    ) -> List[OptionsStrategy]:
        """Fetch real options data from Groww API"""
        
        suggestions = []
        
        try:
            if self.groww_client:
                # Fetch real options chain from Groww
                options_data = await self.groww_client.get_options_chain(underlying_symbol)
                
                if options_data:
                    logger.info(f"Fetched {len(options_data)} options from Groww API")
                    # Convert Groww data to suggestions
                    for opt in options_data[:5]:  # Top 5 strategies
                        suggestions.append(
                            OptionsStrategy(
                                strategy_name=opt.get('type', 'CALL'),
                                underlying=underlying_symbol,
                                strike_prices=[opt.get('strike')],
                                expiry=opt.get('expiry', '30DTE'),
                                risk_reward_ratio=opt.get('risk_reward', 1/3),
                                max_profit=opt.get('max_profit', 10000),
                                max_loss=opt.get('max_loss', 1000),
                                breakeven=opt.get('breakeven', current_price),
                                reasoning=opt.get('recommendation', 'Analyze market conditions')
                            )
                        )
                else:
                    logger.warning("No options data from Groww API - using fallback")
                    suggestions = self._get_fallback_options(underlying_symbol, current_price)
            else:
                logger.warning("Groww client not initialized - using fallback")
                suggestions = self._get_fallback_options(underlying_symbol, current_price)
                
        except Exception as e:
            logger.error(f"Error fetching options from Groww: {e}")
            suggestions = self._get_fallback_options(underlying_symbol, current_price)
        
        return suggestions
    
    def _get_fallback_options(
        self, underlying_symbol: str, current_price: float
    ) -> List[OptionsStrategy]:
        """Fallback options (minimal) when Groww API unavailable"""
        return [
            OptionsStrategy(
                strategy_name="LONG_CALL",
                underlying=underlying_symbol,
                strike_prices=[current_price * 1.02],
                expiry="30DTE",
                risk_reward_ratio=1/3,
                max_profit=float('inf'),
                max_loss=200,
                breakeven=current_price * 1.02 + 200,
                reasoning="Requires Groww API for detailed options analysis"
            )
        ]
    
    async def generate_mutual_fund_recommendations(self) -> List[MutualFundRecommendation]:
        """Fetch real mutual fund recommendations from Groww API"""
        
        recommendations = []
        
        try:
            if self.groww_client:
                # Fetch real mutual funds from Groww
                funds_data = await self.groww_client.get_mutual_funds()
                
                if funds_data:
                    logger.info(f"Fetched {len(funds_data)} mutual funds from Groww API")
                    # Convert Groww data to recommendations
                    for fund in funds_data[:4]:  # Top 4 funds
                        recommendations.append(
                            MutualFundRecommendation(
                                fund_name=fund.get('name', 'Unknown Fund'),
                                fund_category=fund.get('category', 'Mixed'),
                                sip_amount=fund.get('sip_amount', 5000),
                                lump_sum_amount=fund.get('lump_sum', 100000),
                                expected_return=fund.get('expected_return', 12.0),
                                risk_level=fund.get('risk_level', 'MEDIUM'),
                                reasoning=fund.get('rationale', 'Groww-recommended fund')
                            )
                        )
                else:
                    logger.warning("No funds from Groww API - using fallback")
                    recommendations = self._get_fallback_mutual_funds()
            else:
                logger.warning("Groww client not initialized - using fallback")
                recommendations = self._get_fallback_mutual_funds()
                
        except Exception as e:
            logger.error(f"Error fetching mutual funds from Groww: {e}")
            recommendations = self._get_fallback_mutual_funds()
        
        return recommendations
    
    def _get_fallback_mutual_funds(self) -> List[MutualFundRecommendation]:
        """Fallback funds (minimal) when Groww API unavailable"""
        return [
            MutualFundRecommendation(
                fund_name="SBI Bluechip Fund",
                fund_category="Large Cap",
                sip_amount=5000,
                expected_return=12.0,
                risk_level="LOW",
                reasoning="Requires Groww API for real-time fund data"
            )
        ]
    
    async def get_stocks_to_watch(self) -> List[Dict]:
        """Fetch recommended stocks from Groww API"""
        
        try:
            if self.groww_client:
                # Fetch trending stocks from Groww
                stocks_data = await self.groww_client.get_trending_stocks()
                
                if stocks_data:
                    logger.info(f"Fetched {len(stocks_data)} trending stocks from Groww")
                    return [
                        {
                            "symbol": stock.get('symbol'),
                            "reason": stock.get('reason', 'High momentum'),
                            "technical_score": stock.get('technical_score', 7.5),
                            "fundamental_score": stock.get('fundamental_score', 7.5)
                        }
                        for stock in stocks_data[:5]
                    ]
                else:
                    logger.warning("No stocks from Groww API - using fallback")
                    return self._get_fallback_stocks()
            else:
                logger.warning("Groww client not initialized - using fallback")
                return self._get_fallback_stocks()
                
        except Exception as e:
            logger.error(f"Error fetching stocks from Groww: {e}")
            return self._get_fallback_stocks()
    
    def _get_fallback_stocks(self) -> List[Dict]:
        """Fallback stocks (minimal) when Groww API unavailable"""
        return [
            {
                "symbol": "NSE.RELIANCE",
                "reason": "Market performance tracking",
                "technical_score": 7.0,
                "fundamental_score": 7.0
            }
        ]
    
    def apply_risk_management(
        self, signal: TradeSignal, portfolio_value: float,
        max_position_size_percent: float, stop_loss_percent: float
    ) -> Dict:
        """Apply risk management to a signal"""
        
        max_position_size = (portfolio_value * max_position_size_percent) / 100
        position_size = min(max_position_size, signal.price * signal.recommended_quantity)
        
        quantity = int(position_size / signal.price)
        stop_loss_price = signal.price * (1 - stop_loss_percent / 100)
        
        risk_per_trade = position_size - (quantity * stop_loss_price)
        risk_percent = (risk_per_trade / portfolio_value) * 100
        
        return {
            "quantity": quantity,
            "position_size": position_size,
            "stop_loss_price": stop_loss_price,
            "risk_per_trade": risk_per_trade,
            "risk_percent": risk_percent,
            "approved": risk_percent <= max_position_size_percent
        }

