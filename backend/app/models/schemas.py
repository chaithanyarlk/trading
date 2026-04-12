from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

class TradeAction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class TradeStatus(str, Enum):
    PENDING = "PENDING"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class AssetType(str, Enum):
    STOCK = "STOCK"
    MUTUAL_FUND = "MUTUAL_FUND"
    OPTIONS = "OPTIONS"

class IndicatorSignal(BaseModel):
    """Technical indicator signal"""
    name: str
    value: float
    threshold_upper: Optional[float] = None
    threshold_lower: Optional[float] = None
    signal: str  # BUY, SELL, NEUTRAL
    confidence: float  # 0-1

class TradeSignal(BaseModel):
    """AI-generated trade signal"""
    asset_id: str
    asset_name: str
    asset_type: AssetType
    action: TradeAction
    price: float
    confidence: float  # 0-1
    indicators: List[IndicatorSignal]
    reasoning: str
    risk_level: str  # LOW, MEDIUM, HIGH
    recommended_quantity: int
    timestamp: datetime

class Trade(BaseModel):
    """Executed trade record"""
    id: Optional[str] = None
    asset_id: str
    asset_name: str
    action: TradeAction
    entry_price: float
    quantity: int
    timestamp: datetime
    status: TradeStatus
    reasoning: str
    confidence: float

class PortfolioHolding(BaseModel):
    """Current portfolio holding"""
    asset_id: str
    asset_name: str
    quantity: int
    average_cost: float
    current_price: float
    current_value: float
    unrealized_pnl: float
    unrealized_pnl_percent: float

class PortfolioOverview(BaseModel):
    """Portfolio summary"""
    total_value: float
    total_invested: float
    realized_pnl: float
    unrealized_pnl: float
    cash_balance: float
    holdings: List[PortfolioHolding]
    last_updated: datetime

class OptionsStrategy(BaseModel):
    """Options trading strategy suggestion"""
    strategy_name: str  # CALL, PUT, BULL_SPREAD, BEAR_SPREAD
    underlying: str
    strike_prices: List[float]
    expiry: str
    risk_reward_ratio: float
    max_profit: float
    max_loss: float
    breakeven: float
    reasoning: str

class MutualFundRecommendation(BaseModel):
    """Mutual fund recommendation"""
    fund_name: str
    fund_category: str
    sip_amount: float
    lump_sum_amount: Optional[float] = None
    expected_return: float
    risk_level: str
    reasoning: str

class PerformanceMetrics(BaseModel):
    """Strategy performance metrics"""
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
