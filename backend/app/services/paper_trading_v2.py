"""
Paper Trading Simulator — Config-driven from UI.

NO hardcoded values. Every parameter comes from PaperTradingConfig
which the UI sends via API.
"""
import logging
import uuid
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from app.models.agent_schemas import (
    Trade, TradeAction, TradeStatus, PortfolioHolding,
    PortfolioOverview, PerformanceMetrics, ChiefDecision,
    PaperTradingConfig
)

logger = logging.getLogger(__name__)


class PaperTradingEngine:
    """
    Paper trading engine. Config comes from UI, not env vars.

    Usage:
        engine = PaperTradingEngine()
        engine.configure(PaperTradingConfig(initial_capital=500000, ...))
        result = engine.execute_decision(chief_decision)
    """

    def __init__(self):
        self._config: Optional[PaperTradingConfig] = None
        self.cash_balance: float = 0
        self.initial_capital: float = 0
        self.holdings: Dict[str, PortfolioHolding] = {}
        self.trades: List[Trade] = []
        self._configured = False

    @property
    def is_configured(self) -> bool:
        return self._configured

    def configure(self, config: PaperTradingConfig) -> Dict:
        """
        Initialize or reconfigure the paper trading engine.
        Called from the UI when user sets up their config.
        """
        self._config = config
        self.initial_capital = config.initial_capital
        self.cash_balance = config.initial_capital
        self.holdings.clear()
        self.trades.clear()
        self._configured = True

        logger.info(
            f"[PaperTrading] Configured: capital=₹{config.initial_capital}, "
            f"max_pos={config.max_position_size_percent}%, "
            f"sl={config.stop_loss_percent}%, tp={config.take_profit_percent}%, "
            f"symbols={config.trading_symbols}"
        )
        return {
            "status": "configured",
            "initial_capital": config.initial_capital,
            "config": config.model_dump()
        }

    def get_config(self) -> Optional[PaperTradingConfig]:
        """Return current config."""
        return self._config

    def execute_decision(self, decision: ChiefDecision) -> Dict:
        """
        Execute a ChiefDecision as a paper trade.
        Applies slippage and commission from config.
        """
        if not self._configured:
            return {"success": False, "error": "Paper trading not configured. Send config from UI first."}

        if decision.action == TradeAction.HOLD:
            return {
                "success": True,
                "action": "HOLD",
                "message": f"Holding {decision.symbol} — no trade executed",
                "reasoning": decision.chief_reasoning
            }

        if decision.action == TradeAction.BUY:
            return self._execute_buy(decision)
        elif decision.action == TradeAction.SELL:
            return self._execute_sell(decision)

        return {"success": False, "error": f"Unknown action: {decision.action}"}

    def _execute_buy(self, decision: ChiefDecision) -> Dict:
        """Execute a paper BUY."""
        config = self._config
        symbol = decision.symbol
        price = decision.price
        quantity = decision.quantity

        if quantity <= 0:
            return {"success": False, "error": "Quantity must be > 0"}

        # Apply slippage (you buy slightly higher)
        slippage = price * (config.slippage_percent / 100)
        execution_price = price + slippage
        total_cost = execution_price * quantity + config.commission_per_trade

        # Check funds
        if total_cost > self.cash_balance:
            # Reduce quantity to fit
            affordable = int((self.cash_balance - config.commission_per_trade) / execution_price)
            if affordable <= 0:
                return {
                    "success": False,
                    "error": f"Insufficient funds. Need ₹{total_cost:.2f}, have ₹{self.cash_balance:.2f}"
                }
            quantity = affordable
            total_cost = execution_price * quantity + config.commission_per_trade

        # Check max positions
        if len(self.holdings) >= config.max_open_positions and symbol not in self.holdings:
            return {
                "success": False,
                "error": f"Max open positions ({config.max_open_positions}) reached"
            }

        # Update cash
        self.cash_balance -= total_cost

        # Update or create holding
        if symbol in self.holdings:
            h = self.holdings[symbol]
            total_qty = h.quantity + quantity
            new_avg = (h.average_cost * h.quantity + execution_price * quantity) / total_qty
            h.quantity = total_qty
            h.average_cost = new_avg
            h.current_price = execution_price
            h.current_value = execution_price * total_qty
            h.unrealized_pnl = (execution_price - new_avg) * total_qty
            h.unrealized_pnl_percent = ((execution_price - new_avg) / new_avg * 100) if new_avg > 0 else 0
        else:
            self.holdings[symbol] = PortfolioHolding(
                asset_id=symbol,
                asset_name=symbol,
                quantity=quantity,
                average_cost=execution_price,
                current_price=execution_price,
                current_value=execution_price * quantity,
                unrealized_pnl=0,
                unrealized_pnl_percent=0
            )

        # Record trade
        trade = Trade(
            id=decision.trade_id or str(uuid.uuid4())[:8],
            asset_id=symbol,
            asset_name=symbol,
            action=TradeAction.BUY,
            entry_price=execution_price,
            quantity=quantity,
            timestamp=datetime.now(),
            status=TradeStatus.EXECUTED,
            reasoning=decision.chief_reasoning,
            confidence=decision.confidence,
            stop_loss=decision.stop_loss,
            take_profit=decision.take_profit,
            chief_decision=decision,
        )
        self.trades.append(trade)

        logger.info(f"[PaperTrading] BUY {symbol} x{quantity} @ ₹{execution_price:.2f} (cost=₹{total_cost:.2f})")
        return {
            "success": True,
            "action": "BUY",
            "symbol": symbol,
            "quantity": quantity,
            "execution_price": round(execution_price, 2),
            "total_cost": round(total_cost, 2),
            "commission": config.commission_per_trade,
            "slippage": round(slippage, 2),
            "cash_remaining": round(self.cash_balance, 2),
            "trade_id": trade.id,
            "reasoning": decision.chief_reasoning,
        }

    def _execute_sell(self, decision: ChiefDecision) -> Dict:
        """Execute a paper SELL."""
        config = self._config
        symbol = decision.symbol
        price = decision.price
        quantity = decision.quantity

        if symbol not in self.holdings:
            return {"success": False, "error": f"No holdings for {symbol}"}

        holding = self.holdings[symbol]
        quantity = min(quantity, holding.quantity)  # Can't sell more than we have

        if quantity <= 0:
            return {"success": False, "error": "Quantity must be > 0"}

        # Apply slippage (you sell slightly lower)
        slippage = price * (config.slippage_percent / 100)
        execution_price = price - slippage
        proceeds = execution_price * quantity - config.commission_per_trade

        # Calculate PnL
        cost_basis = holding.average_cost * quantity
        pnl = proceeds - cost_basis

        # Update cash
        self.cash_balance += proceeds

        # Update holding
        holding.quantity -= quantity
        if holding.quantity <= 0:
            del self.holdings[symbol]
        else:
            holding.current_price = execution_price
            holding.current_value = execution_price * holding.quantity
            holding.unrealized_pnl = (execution_price - holding.average_cost) * holding.quantity
            holding.unrealized_pnl_percent = (
                (execution_price - holding.average_cost) / holding.average_cost * 100
                if holding.average_cost > 0 else 0
            )

        # Record trade
        trade = Trade(
            id=decision.trade_id or str(uuid.uuid4())[:8],
            asset_id=symbol,
            asset_name=symbol,
            action=TradeAction.SELL,
            entry_price=execution_price,
            quantity=quantity,
            timestamp=datetime.now(),
            status=TradeStatus.EXECUTED,
            reasoning=decision.chief_reasoning,
            confidence=decision.confidence,
            stop_loss=decision.stop_loss,
            take_profit=decision.take_profit,
            pnl=round(pnl, 2),
            chief_decision=decision,
        )
        self.trades.append(trade)

        logger.info(f"[PaperTrading] SELL {symbol} x{quantity} @ ₹{execution_price:.2f} (PnL=₹{pnl:.2f})")
        return {
            "success": True,
            "action": "SELL",
            "symbol": symbol,
            "quantity": quantity,
            "execution_price": round(execution_price, 2),
            "proceeds": round(proceeds, 2),
            "pnl": round(pnl, 2),
            "commission": config.commission_per_trade,
            "slippage": round(slippage, 2),
            "cash_remaining": round(self.cash_balance, 2),
            "trade_id": trade.id,
            "reasoning": decision.chief_reasoning,
        }

    def get_portfolio_overview(self) -> PortfolioOverview:
        """Get portfolio snapshot."""
        total_value = self.cash_balance
        total_invested = 0
        unrealized_pnl = 0

        for h in self.holdings.values():
            total_value += h.current_value
            total_invested += h.average_cost * h.quantity
            unrealized_pnl += h.unrealized_pnl

        realized_pnl = sum(t.pnl or 0 for t in self.trades if t.action == TradeAction.SELL and t.status == TradeStatus.EXECUTED)

        return PortfolioOverview(
            total_value=total_value,
            total_invested=total_invested,
            realized_pnl=realized_pnl,
            unrealized_pnl=unrealized_pnl,
            cash_balance=self.cash_balance,
            holdings=list(self.holdings.values()),
            last_updated=datetime.now(),
        )

    def get_performance_metrics(self) -> PerformanceMetrics:
        """Calculate performance metrics."""
        executed = [t for t in self.trades if t.status == TradeStatus.EXECUTED]
        sells = [t for t in executed if t.action == TradeAction.SELL]

        winning = [t for t in sells if (t.pnl or 0) > 0]
        losing = [t for t in sells if (t.pnl or 0) < 0]

        total_profit = sum(t.pnl for t in winning if t.pnl)
        total_loss = abs(sum(t.pnl for t in losing if t.pnl))
        net_profit = total_profit - total_loss
        roi = (net_profit / self.initial_capital * 100) if self.initial_capital > 0 else 0

        total_count = len(executed)
        win_rate = (len(winning) / len(sells) * 100) if sells else 0

        return PerformanceMetrics(
            total_trades=total_count,
            winning_trades=len(winning),
            losing_trades=len(losing),
            win_rate=round(win_rate, 2),
            total_profit=round(total_profit, 2),
            total_loss=round(total_loss, 2),
            net_profit=round(net_profit, 2),
            roi=round(roi, 2),
            max_drawdown=0,  # TODO
            average_trade_return=round(net_profit / total_count, 2) if total_count > 0 else 0,
        )

    def get_open_position_count(self) -> int:
        return len(self.holdings)

    def get_portfolio_value(self) -> float:
        total = self.cash_balance
        for h in self.holdings.values():
            total += h.current_value
        return total

    def update_prices(self, prices: Dict[str, float]):
        """Update current prices for all holdings (called periodically)."""
        for symbol, price in prices.items():
            if symbol in self.holdings:
                h = self.holdings[symbol]
                h.current_price = price
                h.current_value = price * h.quantity
                h.unrealized_pnl = (price - h.average_cost) * h.quantity
                h.unrealized_pnl_percent = (
                    (price - h.average_cost) / h.average_cost * 100
                    if h.average_cost > 0 else 0
                )


# Module-level singleton
paper_engine = PaperTradingEngine()

