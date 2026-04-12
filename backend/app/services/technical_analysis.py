import pandas as pd
import numpy as np
import ta
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from app.models.schemas import IndicatorSignal, TradeSignal, TradeAction, AssetType
from app.core.config import settings

logger = logging.getLogger(__name__)

class TechnicalAnalysisEngine:
    """Technical analysis and signal generation engine"""
    
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> Tuple[List[float], str, float]:
        """Calculate RSI (Relative Strength Index)"""
        try:
            if len(prices) < period + 1:
                return [], "NEUTRAL", 0
            
            series = pd.Series(prices)
            rsi = ta.momentum.RSIIndicator(close=series, window=period).rsi()
            
            if pd.isna(rsi.iloc[-1]):
                return list(rsi), "NEUTRAL", 0
            
            current_rsi = float(rsi.iloc[-1])
            signal = "NEUTRAL"
            
            if current_rsi < 30:
                signal = "BUY"  # Oversold
            elif current_rsi > 70:
                signal = "SELL"  # Overbought
            
            return list(rsi), signal, current_rsi
        except Exception as e:
            logger.error(f"Error calculating RSI: {e}")
            return [], "NEUTRAL", 0

    @staticmethod
    def calculate_macd(
        prices: List[float], 
        fast: int = 12, 
        slow: int = 26, 
        signal_period: int = 9
    ) -> Tuple[List[float], List[float], List[float], str]:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        try:
            if len(prices) < slow + signal_period:
                return [], [], [], "NEUTRAL"
            
            series = pd.Series(prices)
            macd_indicator = ta.trend.MACD(close=series, window_fast=fast, window_slow=slow, window_sign=signal_period)
            macd_line = macd_indicator.macd()
            signal_line = macd_indicator.macd_signal()
            histogram = macd_indicator.macd_diff()
            
            if pd.isna(histogram.iloc[-1]):
                return list(macd_line), list(signal_line), list(histogram), "NEUTRAL"
            
            # Signal based on histogram
            current_histogram = float(histogram.iloc[-1])
            signal = "NEUTRAL"
            
            if current_histogram > 0:
                signal = "BUY"  # MACD above signal line
            elif current_histogram < 0:
                signal = "SELL"  # MACD below signal line
            
            return list(macd_line), list(signal_line), list(histogram), signal
        except Exception as e:
            logger.error(f"Error calculating MACD: {e}")
            return [], [], [], "NEUTRAL"

    @staticmethod
    def calculate_bollinger_bands(
        prices: List[float], period: int = 20, std_dev: int = 2
    ) -> Tuple[List[float], List[float], List[float], str]:
        """Calculate Bollinger Bands"""
        try:
            if len(prices) < period:
                return [], [], [], "NEUTRAL"
            
            series = pd.Series(prices)
            bb_indicator = ta.volatility.BollingerBands(close=series, window=period, window_dev=std_dev)
            upper_band = bb_indicator.bollinger_hband()
            middle_band = bb_indicator.bollinger_mavg()
            lower_band = bb_indicator.bollinger_lband()
            
            current_price = prices[-1]
            signal = "NEUTRAL"
            
            if current_price <= float(lower_band.iloc[-1]):
                signal = "BUY"  # Price at lower band
            elif current_price >= float(upper_band.iloc[-1]):
                signal = "SELL"  # Price at upper band
            
            return list(upper_band), list(middle_band), list(lower_band), signal
        except Exception as e:
            logger.error(f"Error calculating Bollinger Bands: {e}")
            return [], [], [], "NEUTRAL"

    @staticmethod
    def calculate_moving_average_signal(
        prices: List[float], short_period: int = 20, long_period: int = 50
    ) -> str:
        """Generate signal from moving average crossover"""
        try:
            if len(prices) < long_period:
                return "NEUTRAL"
            
            series = pd.Series(prices)
            short_ma = series.rolling(window=short_period).mean()
            long_ma = series.rolling(window=long_period).mean()
            
            if pd.isna(short_ma.iloc[-1]) or pd.isna(long_ma.iloc[-1]):
                return "NEUTRAL"
            
            # Check if short MA crossed above long MA (Golden Cross)
            if short_ma.iloc[-1] > long_ma.iloc[-1] and short_ma.iloc[-2] <= long_ma.iloc[-2]:
                return "BUY"
            # Check if short MA crossed below long MA (Death Cross)
            elif short_ma.iloc[-1] < long_ma.iloc[-1] and short_ma.iloc[-2] >= long_ma.iloc[-2]:
                return "SELL"
            
            return "NEUTRAL"
        except Exception as e:
            logger.error(f"Error calculating moving average signal: {e}")
            return "NEUTRAL"

    @staticmethod
    def calculate_volume_trend(volumes: List[float], prices: List[float]) -> str:
        """Analyze volume trend"""
        try:
            if len(volumes) < 20:
                return "NEUTRAL"
            
            avg_recent_volume = np.mean(volumes[-5:])
            avg_historical_volume = np.mean(volumes[-20:])
            
            recent_price_change = (prices[-1] - prices[-5]) / prices[-5] * 100
            
            if avg_recent_volume > avg_historical_volume * 1.2 and recent_price_change > 0:
                return "BUY"  # High volume on uptrend
            elif avg_recent_volume > avg_historical_volume * 1.2 and recent_price_change < 0:
                return "SELL"  # High volume on downtrend
            
            return "NEUTRAL"
        except Exception as e:
            logger.error(f"Error calculating volume trend: {e}")
            return "NEUTRAL"

    @classmethod
    def generate_trade_signal(
        cls,
        asset_id: str,
        asset_name: str,
        prices: List[float],
        volumes: List[float],
        current_price: float
    ) -> TradeSignal:
        """Generate comprehensive trade signal using multiple indicators"""
        
        indicators = []
        signals = []
        
        # RSI Analysis
        rsi_list, rsi_signal, rsi_value = cls.calculate_rsi(prices)
        if rsi_list:
            indicators.append(
                IndicatorSignal(
                    name="RSI",
                    value=rsi_value,
                    threshold_upper=70,
                    threshold_lower=30,
                    signal=rsi_signal,
                    confidence=0.8
                )
            )
            signals.append(rsi_signal)
        
        # MACD Analysis
        macd_line, signal_line, histogram, macd_signal = cls.calculate_macd(prices)
        if macd_line:
            indicators.append(
                IndicatorSignal(
                    name="MACD",
                    value=float(macd_line[-1]),
                    signal=macd_signal,
                    confidence=0.75
                )
            )
            signals.append(macd_signal)
        
        # Bollinger Bands Analysis
        upper_band, middle_band, lower_band, bb_signal = cls.calculate_bollinger_bands(prices)
        if upper_band:
            indicators.append(
                IndicatorSignal(
                    name="Bollinger Bands",
                    value=current_price,
                    threshold_upper=float(upper_band[-1]),
                    threshold_lower=float(lower_band[-1]),
                    signal=bb_signal,
                    confidence=0.7
                )
            )
            signals.append(bb_signal)
        
        # Moving Average Signal
        ma_signal = cls.calculate_moving_average_signal(prices)
        indicators.append(
            IndicatorSignal(
                name="Moving Average Crossover",
                value=0,
                signal=ma_signal,
                confidence=0.75
            )
        )
        signals.append(ma_signal)
        
        # Volume Trend Analysis
        volume_signal = cls.calculate_volume_trend(volumes, prices)
        indicators.append(
            IndicatorSignal(
                name="Volume Trend",
                value=volumes[-1] if volumes else 0,
                signal=volume_signal,
                confidence=0.6
            )
        )
        signals.append(volume_signal)
        
        # Aggregate signals
        buy_signals = sum(1 for s in signals if s == "BUY")
        sell_signals = sum(1 for s in signals if s == "SELL")
        
        if buy_signals > sell_signals:
            final_signal = TradeAction.BUY
            confidence = buy_signals / len(signals)
            action_confidence = min(confidence, 0.9)
        elif sell_signals > buy_signals:
            final_signal = TradeAction.SELL
            confidence = sell_signals / len(signals)
            action_confidence = min(confidence, 0.9)
        else:
            final_signal = TradeAction.BUY  # Default to BUY on neutral
            action_confidence = 0.5
        
        # Determine risk level
        if action_confidence >= 0.8:
            risk_level = "LOW"
        elif action_confidence >= 0.6:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"
        
        # Generate reasoning
        reasoning = f"Signal generated based on {len(indicators)} indicators. "
        reasoning += f"Buy signals: {buy_signals}, Sell signals: {sell_signals}. "
        if buy_signals > sell_signals:
            reasoning += "Bullish momentum detected with multiple indicators confirming uptrend."
        elif sell_signals > buy_signals:
            reasoning += "Bearish momentum detected with multiple indicators confirming downtrend."
        else:
            reasoning += "Mixed signals - caution advised."
        
        # Calculate recommended quantity (simplified - should use portfolio management)
        recommended_quantity = max(1, int(current_price / 10))  # Simplified calculation
        
        return TradeSignal(
            asset_id=asset_id,
            asset_name=asset_name,
            asset_type=AssetType.STOCK,
            action=final_signal,
            price=current_price,
            confidence=action_confidence,
            indicators=indicators,
            reasoning=reasoning,
            risk_level=risk_level,
            recommended_quantity=recommended_quantity,
            timestamp=datetime.now()
        )
