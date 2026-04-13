"""
Agent 2: ALGO / TECHNICAL ANALYSIS AGENT
──────────────────────────────────────────
The numbers guy. Takes raw market data from DataFetcherAgent,
runs every technical indicator, and produces a purely data-driven verdict.

No emotions, no news — just math.

Responsibilities:
  - RSI, MACD, Bollinger Bands, Moving Averages, Volume analysis
  - Support/resistance detection
  - Trend identification
  - Outputs: AlgoAgentVerdict with action + confidence + reasoning
"""
import logging
from typing import Optional
from datetime import datetime

from app.models.agent_schemas import (
    MarketDataSnapshot, AlgoAgentVerdict, IndicatorSignal, TradeAction
)
from app.services.technical_analysis import TechnicalAnalysisEngine

logger = logging.getLogger(__name__)


class AlgoAgent:
    """
    Level 2 Agent — pure technical/quantitative analysis.
    Receives MarketDataSnapshot, returns AlgoAgentVerdict.
    """

    ROLE = "ALGO_ANALYST"

    def __init__(self):
        self.ta = TechnicalAnalysisEngine()

    async def analyze(self, snapshot: MarketDataSnapshot) -> AlgoAgentVerdict:
        """
        Run full technical analysis on a market data snapshot.
        Returns a verdict: BUY / SELL / HOLD with confidence and reasoning.
        """
        symbol = snapshot.symbol
        prices = snapshot.historical_prices
        volumes = snapshot.historical_volumes
        current_price = snapshot.ltp or (prices[-1] if prices else 0)

        logger.info(f"[AlgoAgent] Analyzing {symbol} | LTP=₹{current_price} | {len(prices)} data points")

        if not prices or len(prices) < 30:
            logger.warning(f"[AlgoAgent] Insufficient data for {symbol} ({len(prices)} points)")
            return AlgoAgentVerdict(
                symbol=symbol,
                action=TradeAction.HOLD,
                confidence=0.0,
                reasoning=f"Insufficient historical data ({len(prices)} points, need 30+)"
            )

        indicators = []
        signals = []

        # ── RSI ───────────────────────────────────────────────────
        rsi_list, rsi_signal, rsi_value = self.ta.calculate_rsi(prices)
        if rsi_list:
            explanation = ""
            if rsi_value < 30:
                explanation = f"RSI at {rsi_value:.1f} — OVERSOLD territory, potential bounce"
            elif rsi_value > 70:
                explanation = f"RSI at {rsi_value:.1f} — OVERBOUGHT territory, potential pullback"
            else:
                explanation = f"RSI at {rsi_value:.1f} — neutral zone"

            indicators.append(IndicatorSignal(
                name="RSI", value=rsi_value,
                threshold_upper=70, threshold_lower=30,
                signal=rsi_signal, confidence=0.8,
                explanation=explanation
            ))
            signals.append(rsi_signal)

        # ── MACD ──────────────────────────────────────────────────
        macd_line, signal_line, histogram, macd_signal = self.ta.calculate_macd(prices)
        if macd_line:
            macd_val = float(macd_line[-1])
            hist_val = float(histogram[-1]) if histogram else 0
            explanation = ""
            if hist_val > 0:
                explanation = f"MACD histogram positive ({hist_val:.2f}) — bullish momentum"
            elif hist_val < 0:
                explanation = f"MACD histogram negative ({hist_val:.2f}) — bearish momentum"
            else:
                explanation = "MACD histogram flat — no clear momentum"

            indicators.append(IndicatorSignal(
                name="MACD", value=macd_val,
                signal=macd_signal, confidence=0.75,
                explanation=explanation
            ))
            signals.append(macd_signal)

        # ── Bollinger Bands ───────────────────────────────────────
        upper, middle, lower, bb_signal = self.ta.calculate_bollinger_bands(prices)
        if upper:
            bb_position = "middle"
            if current_price <= float(lower[-1]):
                bb_position = "at lower band"
            elif current_price >= float(upper[-1]):
                bb_position = "at upper band"

            indicators.append(IndicatorSignal(
                name="Bollinger Bands", value=current_price,
                threshold_upper=float(upper[-1]),
                threshold_lower=float(lower[-1]),
                signal=bb_signal, confidence=0.7,
                explanation=f"Price {bb_position} (Upper: ₹{float(upper[-1]):.2f}, Lower: ₹{float(lower[-1]):.2f})"
            ))
            signals.append(bb_signal)

        # ── Moving Average Crossover ──────────────────────────────
        ma_signal = self.ta.calculate_moving_average_signal(prices)
        if ma_signal != "NEUTRAL":
            indicators.append(IndicatorSignal(
                name="MA Crossover (20/50)", value=current_price,
                signal=ma_signal, confidence=0.85,
                explanation=f"{'Golden' if ma_signal == 'BUY' else 'Death'} cross detected on 20/50 MA"
            ))
        signals.append(ma_signal)

        # ── Volume Trend ──────────────────────────────────────────
        if volumes and len(volumes) >= 20:
            vol_signal = self.ta.calculate_volume_trend(volumes, prices)
            indicators.append(IndicatorSignal(
                name="Volume Trend", value=float(volumes[-1]) if volumes else 0,
                signal=vol_signal, confidence=0.65,
                explanation=f"Volume {'confirming' if vol_signal != 'NEUTRAL' else 'not confirming'} price action"
            ))
            signals.append(vol_signal)

        # ── Aggregate verdict ─────────────────────────────────────
        buy_count = signals.count("BUY")
        sell_count = signals.count("SELL")
        total = len(signals)

        if total == 0:
            action = TradeAction.HOLD
            confidence = 0.0
        elif buy_count > sell_count and buy_count >= 2:
            action = TradeAction.BUY
            confidence = buy_count / total
        elif sell_count > buy_count and sell_count >= 2:
            action = TradeAction.SELL
            confidence = sell_count / total
        else:
            action = TradeAction.HOLD
            confidence = 0.3

        # Determine trend
        if len(prices) >= 50:
            sma20 = sum(prices[-20:]) / 20
            sma50 = sum(prices[-50:]) / 50
            if sma20 > sma50 * 1.02:
                trend = "UPTREND"
            elif sma20 < sma50 * 0.98:
                trend = "DOWNTREND"
            else:
                trend = "SIDEWAYS"
        else:
            trend = "NEUTRAL"

        # Support / Resistance (simple min/max of recent 20 days)
        recent_prices = prices[-20:]
        support = min(recent_prices)
        resistance = max(recent_prices)

        # Build reasoning
        indicator_summary = "; ".join(
            [f"{ind.name}: {ind.signal} ({ind.explanation})" for ind in indicators]
        )
        reasoning = (
            f"Technical Analysis for {symbol}: "
            f"{buy_count} BUY vs {sell_count} SELL signals out of {total}. "
            f"Trend: {trend}. "
            f"Indicators: {indicator_summary}"
        )

        verdict = AlgoAgentVerdict(
            symbol=symbol,
            action=action,
            confidence=round(confidence, 3),
            indicators=indicators,
            support_price=support,
            resistance_price=resistance,
            trend=trend,
            volatility="NORMAL",
            reasoning=reasoning,
            timestamp=datetime.now()
        )

        logger.info(
            f"[AlgoAgent] {symbol}: {action.value} "
            f"(confidence={confidence:.0%}, trend={trend}, "
            f"buy={buy_count}, sell={sell_count})"
        )
        return verdict

