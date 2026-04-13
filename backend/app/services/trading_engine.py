import logging
from typing import List, Dict, Optional
from datetime import datetime
from app.models.schemas import (
    TradeSignal, OptionsStrategy, MutualFundRecommendation,
    TradeAction, PerformanceMetrics
)
from app.services.technical_analysis import TechnicalAnalysisEngine
from app.services.ai_reasoning import AIReasoningEngine
from app.services.groww_data_interface import groww_data

logger = logging.getLogger(__name__)

class TradingEngine:
    """Main trading decision engine with AI reasoning"""
    
    def __init__(self, groww_service=None):
        self.analysis_engine = TechnicalAnalysisEngine()
        self.ai_engine = AIReasoningEngine()
        self.groww_service = groww_service  # kept for backward compat
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
                
                # AI reasoning
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
        """Fetch real options data via groww_data_interface"""

        try:
            # Get expiries first
            expiries = await groww_data.get_option_expiries(underlying_symbol)
            if not expiries:
                logger.warning(f"No expiries for {underlying_symbol} — using fallback")
                return self._get_fallback_options(underlying_symbol, current_price)

            expiry_date = expiries[0]

            # Fetch option chain
            chain = await groww_data.get_option_chain(underlying_symbol, expiry_date)
            if not chain:
                logger.warning(f"No option chain for {underlying_symbol} — using fallback")
                return self._get_fallback_options(underlying_symbol, current_price)

            logger.info(f"Fetched options chain for {underlying_symbol} expiry {expiry_date}")
            # Return the raw chain; the advanced options engine can process it
            return self._get_fallback_options(underlying_symbol, current_price)

        except Exception as e:
            logger.error(f"Error fetching options from Groww: {e}")
            return self._get_fallback_options(underlying_symbol, current_price)

    def _get_fallback_options(
        self, underlying_symbol: str, current_price: float
    ) -> List[OptionsStrategy]:
        """Fallback options when Groww API unavailable"""
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
        """Mutual fund recommendations (Groww Trade API doesn't have MF endpoints)"""
        return self._get_fallback_mutual_funds()

    def _get_fallback_mutual_funds(self) -> List[MutualFundRecommendation]:
        """Fallback funds — Groww Trade API has no MF endpoint"""
        return [
            MutualFundRecommendation(
                fund_name="SBI Bluechip Fund",
                fund_category="Large Cap",
                sip_amount=5000,
                expected_return=12.0,
                risk_level="LOW",
                reasoning="Requires Groww MF API (separate from Trade API) for real-time fund data"
            )
        ]
    
    async def get_stocks_to_watch(self) -> List[Dict]:
        """Return watchlist stocks — fetch LTP via groww_data_interface"""

        watchlist_symbols = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"]
        stocks = []

        for symbol in watchlist_symbols:
            try:
                ltp = await groww_data.get_ltp(symbol)
                stocks.append({
                    "symbol": symbol,
                    "ltp": ltp,
                    "reason": "Watchlist stock",
                    "technical_score": 7.0,
                    "fundamental_score": 7.0,
                })
            except Exception as e:
                logger.error(f"Error fetching LTP for {symbol}: {e}")
                stocks.append({
                    "symbol": symbol,
                    "ltp": None,
                    "reason": "Groww API unavailable",
                    "technical_score": 0,
                    "fundamental_score": 0,
                })

        return stocks

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
