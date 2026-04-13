"""
Multi-Agent Trading System — Schemas

New models for:
  - Paper trading config from UI
  - Agent decisions at each level
  - Chief agent final verdict
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ═══════════════════════════════════════════════════════════════════════
#  ENUMS
# ═══════════════════════════════════════════════════════════════════════

class TradeAction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"     # <-- added HOLD, the old schema only had BUY/SELL

class TradeStatus(str, Enum):
    PENDING = "PENDING"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class AssetType(str, Enum):
    STOCK = "STOCK"
    MUTUAL_FUND = "MUTUAL_FUND"
    OPTIONS = "OPTIONS"

class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"

class AgentRole(str, Enum):
    DATA_FETCHER = "DATA_FETCHER"
    ALGO_ANALYST = "ALGO_ANALYST"
    SENTIMENT_ANALYST = "SENTIMENT_ANALYST"
    CHIEF_TRADER = "CHIEF_TRADER"


# ═══════════════════════════════════════════════════════════════════════
#  PAPER TRADING CONFIG — comes from UI, not env vars
# ═══════════════════════════════════════════════════════════════════════

class PaperTradingConfig(BaseModel):
    """All paper trading config sent from the UI — nothing hardcoded."""
    initial_capital: float = Field(1000000, description="Starting capital in INR")
    max_position_size_percent: float = Field(10.0, description="Max % of portfolio per trade")
    stop_loss_percent: float = Field(2.0, description="Default stop loss %")
    take_profit_percent: float = Field(5.0, description="Default take profit %")
    max_open_positions: int = Field(10, description="Max simultaneous positions")
    risk_per_trade_percent: float = Field(1.0, description="Max risk per trade as % of capital")
    trading_symbols: List[str] = Field(
        default=["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"],
        description="Symbols to trade"
    )
    enable_options: bool = Field(False, description="Enable options trading")
    enable_short_selling: bool = Field(False, description="Enable short selling")
    slippage_percent: float = Field(0.05, description="Simulated slippage %")
    commission_per_trade: float = Field(20.0, description="Brokerage per trade in INR")


# ═══════════════════════════════════════════════════════════════════════
#  AGENT DECISION MODELS
# ═══════════════════════════════════════════════════════════════════════

class MarketDataSnapshot(BaseModel):
    """Raw market data collected by DataFetcherAgent."""
    symbol: str
    ltp: Optional[float] = None
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    prev_close: Optional[float] = None
    volume: Optional[int] = None
    change_percent: Optional[float] = None
    historical_prices: List[float] = []
    historical_volumes: List[float] = []
    timestamp: datetime = Field(default_factory=datetime.now)
    source: str = "groww"
    raw_quote: Optional[Dict[str, Any]] = None


class NewsDataSnapshot(BaseModel):
    """News/sentiment data collected by DataFetcherAgent."""
    symbol: str
    headlines: List[str] = []
    sentiment_score: float = Field(0.0, description="-1 (bearish) to +1 (bullish)")
    key_events: List[str] = []
    sector_sentiment: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    source: str = "ai_generated"


class IndicatorSignal(BaseModel):
    """Single technical indicator result."""
    name: str
    value: float
    threshold_upper: Optional[float] = None
    threshold_lower: Optional[float] = None
    signal: str   # BUY, SELL, NEUTRAL
    confidence: float  # 0-1
    explanation: str = ""


class AlgoAgentVerdict(BaseModel):
    """Decision from the Algo/Technical Analysis Agent."""
    symbol: str
    action: TradeAction
    confidence: float = Field(ge=0, le=1)
    indicators: List[IndicatorSignal] = []
    support_price: Optional[float] = None
    resistance_price: Optional[float] = None
    trend: str = "NEUTRAL"   # UPTREND, DOWNTREND, SIDEWAYS, NEUTRAL
    volatility: str = "NORMAL"  # LOW, NORMAL, HIGH
    reasoning: str = ""
    timestamp: datetime = Field(default_factory=datetime.now)


class SentimentAgentVerdict(BaseModel):
    """Decision from the News/Sentiment Agent."""
    symbol: str
    action: TradeAction
    confidence: float = Field(ge=0, le=1)
    sentiment_score: float = Field(ge=-1, le=1)
    key_factors: List[str] = []
    risk_events: List[str] = []
    reasoning: str = ""
    timestamp: datetime = Field(default_factory=datetime.now)


class ChiefDecision(BaseModel):
    """
    Final decision from the Chief Trading Agent.
    This is the ONLY thing that triggers a trade.
    Contains full reasoning chain from all agents.
    """
    symbol: str
    action: TradeAction
    confidence: float = Field(ge=0, le=1)
    price: float
    quantity: int = 0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    risk_level: RiskLevel = RiskLevel.MEDIUM
    position_size_percent: float = 0.0

    # Reasoning chain — every agent's input visible
    algo_verdict: Optional[AlgoAgentVerdict] = None
    sentiment_verdict: Optional[SentimentAgentVerdict] = None
    chief_reasoning: str = ""
    dissenting_opinions: List[str] = []

    # Execution
    executed: bool = False
    execution_mode: str = "PAPER"   # PAPER or LIVE
    trade_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


# ═══════════════════════════════════════════════════════════════════════
#  TRADE & PORTFOLIO (upgraded from old schemas)
# ═══════════════════════════════════════════════════════════════════════

class TradeSignal(BaseModel):
    """AI-generated trade signal — kept for backward compat."""
    asset_id: str
    asset_name: str
    asset_type: AssetType = AssetType.STOCK
    action: TradeAction
    price: float
    confidence: float
    indicators: List[IndicatorSignal] = []
    reasoning: str
    risk_level: str = "MEDIUM"
    recommended_quantity: int = 0
    timestamp: datetime = Field(default_factory=datetime.now)


class Trade(BaseModel):
    """Executed trade record."""
    id: Optional[str] = None
    asset_id: str
    asset_name: str
    action: TradeAction
    entry_price: float
    quantity: int
    timestamp: datetime = Field(default_factory=datetime.now)
    status: TradeStatus = TradeStatus.PENDING
    reasoning: str = ""
    confidence: float = 0.0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    exit_price: Optional[float] = None
    pnl: Optional[float] = None
    # Full agent reasoning chain
    chief_decision: Optional[ChiefDecision] = None


class PortfolioHolding(BaseModel):
    """Current portfolio holding."""
    asset_id: str
    asset_name: str
    quantity: int
    average_cost: float
    current_price: float
    current_value: float
    unrealized_pnl: float
    unrealized_pnl_percent: float


class PortfolioOverview(BaseModel):
    """Portfolio summary."""
    total_value: float
    total_invested: float
    realized_pnl: float
    unrealized_pnl: float
    cash_balance: float
    holdings: List[PortfolioHolding] = []
    last_updated: datetime = Field(default_factory=datetime.now)


class OptionsStrategy(BaseModel):
    """Options trading strategy suggestion."""
    strategy_name: str
    underlying: str
    strike_prices: List[float]
    expiry: str
    risk_reward_ratio: float
    max_profit: float
    max_loss: float
    breakeven: float
    reasoning: str


class MutualFundRecommendation(BaseModel):
    """Mutual fund recommendation."""
    fund_name: str
    fund_category: str
    sip_amount: float
    lump_sum_amount: Optional[float] = None
    expected_return: float
    risk_level: str
    reasoning: str


class PerformanceMetrics(BaseModel):
    """Strategy performance metrics."""
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_profit: float
    total_loss: float
    net_profit: float
    roi: float
    sharpe_ratio: Optional[float] = None
    max_drawdown: float
    average_trade_return: float


# ═══════════════════════════════════════════════════════════════════════
#  AGENT PIPELINE REQUEST/RESPONSE
# ═══════════════════════════════════════════════════════════════════════

class AnalyzeRequest(BaseModel):
    """Request to run the full multi-agent pipeline on symbols."""
    symbols: List[str]
    config: PaperTradingConfig
    auto_execute: bool = Field(False, description="Auto-execute chief's decisions")


class AnalyzeResponse(BaseModel):
    """Response from the multi-agent pipeline."""
    decisions: List[ChiefDecision] = []
    errors: List[str] = []
    timestamp: datetime = Field(default_factory=datetime.now)

