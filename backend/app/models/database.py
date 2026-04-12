"""
SQLAlchemy database models for comprehensive trade tracking
"""
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, Boolean, Text, Enum, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()

class TradeActionEnum(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"

class TradeStatusEnum(str, enum.Enum):
    PENDING = "PENDING"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class StrategyTypeEnum(str, enum.Enum):
    DIRECTIONAL = "DIRECTIONAL"
    STRADDLE = "STRADDLE"
    STRANGLE = "STRANGLE"
    IRON_CONDOR = "IRON_CONDOR"
    BULL_CALL_SPREAD = "BULL_CALL_SPREAD"
    BEAR_CALL_SPREAD = "BEAR_CALL_SPREAD"
    BULL_PUT_SPREAD = "BULL_PUT_SPREAD"
    BEAR_PUT_SPREAD = "BEAR_PUT_SPREAD"

class TradingModeEnum(str, enum.Enum):
    PAPER = "PAPER"
    LIVE = "LIVE"

# ============ MARKET DATA ============

class MarketData(Base):
    """Store historical market data"""
    __tablename__ = "market_data"
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Integer)
    vwap = Column(Float)
    
    # Relationships
    trades = relationship("ExecutedTrade", back_populates="market_data")

# ============ TECHNICAL INDICATORS ============

class IndicatorCache(Base):
    """Cache calculated technical indicators"""
    __tablename__ = "indicator_cache"
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False)
    
    # RSI
    rsi_14 = Column(Float)
    rsi_signal = Column(String(20))
    
    # MACD
    macd_value = Column(Float)
    macd_signal = Column(Float)
    macd_histogram = Column(Float)
    macd_signal_type = Column(String(20))
    
    # Bollinger Bands
    bb_upper = Column(Float)
    bb_middle = Column(Float)
    bb_lower = Column(Float)
    bb_signal = Column(String(20))
    
    # Moving Averages
    sma_20 = Column(Float)
    sma_50 = Column(Float)
    sma_200 = Column(Float)
    ema_12 = Column(Float)
    ema_26 = Column(Float)
    
    # Volume
    volume_ma = Column(Float)
    volume_signal = Column(String(20))
    
    # Volatility
    atr = Column(Float)
    volatility = Column(Float)

# ============ TRADE SIGNALS & EXECUTION ============

class TradeSignal(Base):
    """Generated trade signals with AI reasoning"""
    __tablename__ = "trade_signals"
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    action = Column(Enum(TradeActionEnum))
    confidence = Column(Float)  # 0-1
    price = Column(Float)
    
    # AI Reasoning
    reasoning = Column(Text)  # Detailed explanation
    indicators_used = Column(JSON)  # Which indicators triggered signal
    risk_level = Column(String(20))  # LOW, MEDIUM, HIGH
    
    # Target & Stop Loss
    target_price = Column(Float)
    stop_loss = Column(Float)
    
    # Execution link
    executed_trade_id = Column(Integer, ForeignKey("executed_trades.id"))
    executed_trade = relationship("ExecutedTrade", back_populates="signal")

class ExecutedTrade(Base):
    """Record of executed trades (paper or live)"""
    __tablename__ = "executed_trades"
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    mode = Column(Enum(TradingModeEnum))  # PAPER or LIVE
    
    # Entry
    entry_time = Column(DateTime, nullable=False)
    entry_price = Column(Float)
    entry_quantity = Column(Integer)
    entry_reasoning = Column(Text)
    entry_signal_id = Column(Integer, ForeignKey("trade_signals.id"))
    
    # Exit
    exit_time = Column(DateTime)
    exit_price = Column(Float)
    exit_quantity = Column(Integer)
    exit_reason = Column(String(100))  # PROFIT_TARGET, STOP_LOSS, MANUAL, TIME_EXIT
    
    # P&L
    entry_value = Column(Float)
    exit_value = Column(Float)
    profit_loss = Column(Float)
    profit_loss_percent = Column(Float)
    
    # Risk Management
    stop_loss = Column(Float)
    stop_loss_triggered = Column(Boolean, default=False)
    trailing_stop = Column(Float)
    trailing_stop_triggered = Column(Boolean, default=False)
    
    # Strategy
    strategy = Column(String(50))
    holding_duration_minutes = Column(Integer)
    
    # Status
    status = Column(Enum(TradeStatusEnum))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    signal = relationship("TradeSignal", back_populates="executed_trade")

# ============ OPTIONS TRADING ============

class OptionsContract(Base):
    """Options contract details"""
    __tablename__ = "options_contracts"
    
    id = Column(Integer, primary_key=True)
    underlying_symbol = Column(String(20), nullable=False)
    strike_price = Column(Float)
    expiry_date = Column(DateTime)
    contract_type = Column(String(10))  # PUT/CALL
    
    # Market data
    bid_price = Column(Float)
    ask_price = Column(Float)
    last_price = Column(Float)
    iv = Column(Float)  # Implied Volatility
    delta = Column(Float)
    gamma = Column(Float)
    theta = Column(Float)
    vega = Column(Float)
    
    timestamp = Column(DateTime, default=datetime.utcnow)

class OptionsTrade(Base):
    """Options trading records"""
    __tablename__ = "options_trades"
    
    id = Column(Integer, primary_key=True)
    strategy = Column(Enum(StrategyTypeEnum))
    underlying_symbol = Column(String(20))
    
    # Entry
    entry_time = Column(DateTime)
    entry_price = Column(Float)
    contracts = Column(Integer)
    
    # Exit
    exit_time = Column(DateTime)
    exit_price = Column(Float)
    
    # P&L
    premium_collected = Column(Float)
    max_profit = Column(Float)
    max_loss = Column(Float)
    actual_profit_loss = Column(Float)
    
    # AI Decision
    strategy_reason = Column(Text)
    probability_of_profit = Column(Float)
    
    # Status
    status = Column(Enum(TradeStatusEnum))
    mode = Column(Enum(TradingModeEnum))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ============ PORTFOLIO ============

class PortfolioHolding(Base):
    """Current portfolio holdings"""
    __tablename__ = "portfolio_holdings"
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), unique=True)
    quantity = Column(Integer)
    average_cost = Column(Float)
    current_price = Column(Float)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unrealized P&L
    unrealized_pnl = Column(Float)
    unrealized_pnl_percent = Column(Float)

class CashBalance(Base):
    """Track cash balance and transactions"""
    __tablename__ = "cash_balance"
    
    id = Column(Integer, primary_key=True)
    mode = Column(Enum(TradingModeEnum))
    balance = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ============ MUTUAL FUNDS ============

class MutualFund(Base):
    """Mutual fund data"""
    __tablename__ = "mutual_funds"
    
    id = Column(Integer, primary_key=True)
    fund_code = Column(String(50), unique=True)
    fund_name = Column(String(255))
    category = Column(String(100))
    nav = Column(Float)
    
    # Returns
    return_1y = Column(Float)
    return_3y = Column(Float)
    return_5y = Column(Float)
    
    # Metrics
    expense_ratio = Column(Float)
    aum = Column(Float)
    risk_rating = Column(String(20))
    
    # Timestamps
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class MutualFundRecommendation(Base):
    """Recommended mutual funds"""
    __tablename__ = "mutual_fund_recommendations"
    
    id = Column(Integer, primary_key=True)
    fund_code = Column(String(50), ForeignKey("mutual_funds.fund_code"))
    
    # Recommendation
    recommended_at = Column(DateTime, default=datetime.utcnow)
    sip_amount = Column(Float)
    lump_sum_amount = Column(Float)
    reasoning = Column(Text)
    expected_return = Column(Float)
    
    # Status
    invested = Column(Boolean, default=False)
    investment_amount = Column(Float)
    investment_date = Column(DateTime)

# ============ DAILY REPORTS ============

class DailyReport(Base):
    """End-of-day trading report"""
    __tablename__ = "daily_reports"
    
    id = Column(Integer, primary_key=True)
    report_date = Column(DateTime, unique=True, index=True)
    
    # Trade Summary
    total_trades = Column(Integer)
    winning_trades = Column(Integer)
    losing_trades = Column(Integer)
    win_rate = Column(Float)
    
    # P&L
    total_profit = Column(Float)
    total_loss = Column(Float)
    net_profit = Column(Float)
    
    # Strategy Performance
    best_strategy = Column(String(100))
    worst_strategy = Column(String(100))
    strategies_used = Column(JSON)  # List of strategies used
    
    # Insights
    key_insights = Column(Text)
    mistakes = Column(Text)
    recommendations = Column(Text)
    
    # Charts & Data
    trade_details = Column(JSON)  # All trades for the day
    graph_data = Column(JSON)  # Data for generating graphs
    
    created_at = Column(DateTime, default=datetime.utcnow)

# ============ SYSTEM LOGS ============

class SystemLog(Base):
    """Log all system actions and decisions"""
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    level = Column(String(20))  # INFO, WARNING, ERROR, DEBUG
    module = Column(String(100))
    message = Column(Text)
    trade_id = Column(Integer, ForeignKey("executed_trades.id"))
    
    created_at = Column(DateTime, default=datetime.utcnow)
