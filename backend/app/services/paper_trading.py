import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from app.models.schemas import (
    Trade, TradeAction, TradeStatus, PortfolioHolding, 
    PortfolioOverview, PerformanceMetrics, TradeSignal
)

logger = logging.getLogger(__name__)

class PaperTradingSimulator:
    """Simulates trades without real money"""
    
    def __init__(self, initial_capital: float):
        self.initial_capital = initial_capital
        self.cash_balance = initial_capital
        self.holdings: Dict[str, PortfolioHolding] = {}
        self.trades: List[Trade] = []
        self.performance_history = []
    
    def execute_trade(
        self, signal: TradeSignal, current_price: float, quantity: int
    ) -> Tuple[bool, Trade, str]:
        """Execute a simulated trade"""
        
        try:
            if signal.action == TradeAction.BUY:
                return self._execute_buy(signal, current_price, quantity)
            else:
                return self._execute_sell(signal, current_price, quantity)
        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            trade = Trade(
                asset_id=signal.asset_id,
                asset_name=signal.asset_name,
                action=signal.action,
                entry_price=current_price,
                quantity=quantity,
                timestamp=datetime.now(),
                status=TradeStatus.FAILED,
                reasoning=signal.reasoning,
                confidence=signal.confidence
            )
            return False, trade, str(e)
    
    def _execute_buy(
        self, signal: TradeSignal, current_price: float, quantity: int
    ) -> Tuple[bool, Trade, str]:
        """Execute a buy order"""
        
        total_cost = current_price * quantity
        
        # Check if sufficient funds
        if total_cost > self.cash_balance:
            message = f"Insufficient funds. Required: {total_cost}, Available: {self.cash_balance}"
            logger.warning(message)
            trade = Trade(
                asset_id=signal.asset_id,
                asset_name=signal.asset_name,
                action=TradeAction.BUY,
                entry_price=current_price,
                quantity=quantity,
                timestamp=datetime.now(),
                status=TradeStatus.FAILED,
                reasoning=signal.reasoning,
                confidence=signal.confidence
            )
            return False, trade, message
        
        # Update portfolio
        self.cash_balance -= total_cost
        
        if signal.asset_id in self.holdings:
            holding = self.holdings[signal.asset_id]
            # Calculate new average cost
            total_quantity = holding.quantity + quantity
            new_average_cost = (
                (holding.average_cost * holding.quantity + current_price * quantity) /
                total_quantity
            )
            holding.quantity = total_quantity
            holding.average_cost = new_average_cost
            holding.current_price = current_price
            holding.current_value = current_price * total_quantity
            holding.unrealized_pnl = (current_price - new_average_cost) * total_quantity
            holding.unrealized_pnl_percent = (
                (current_price - new_average_cost) / new_average_cost * 100
            )
        else:
            self.holdings[signal.asset_id] = PortfolioHolding(
                asset_id=signal.asset_id,
                asset_name=signal.asset_name,
                quantity=quantity,
                average_cost=current_price,
                current_price=current_price,
                current_value=total_cost,
                unrealized_pnl=0,
                unrealized_pnl_percent=0
            )
        
        trade = Trade(
            asset_id=signal.asset_id,
            asset_name=signal.asset_name,
            action=TradeAction.BUY,
            entry_price=current_price,
            quantity=quantity,
            timestamp=datetime.now(),
            status=TradeStatus.EXECUTED,
            reasoning=signal.reasoning,
            confidence=signal.confidence
        )
        
        self.trades.append(trade)
        logger.info(f"Buy order executed: {signal.asset_name} x{quantity} @ {current_price}")
        return True, trade, "Buy order executed successfully"
    
    def _execute_sell(
        self, signal: TradeSignal, current_price: float, quantity: int
    ) -> Tuple[bool, Trade, str]:
        """Execute a sell order"""
        
        # Check if holding exists
        if signal.asset_id not in self.holdings:
            message = f"No holdings of {signal.asset_name} to sell"
            logger.warning(message)
            trade = Trade(
                asset_id=signal.asset_id,
                asset_name=signal.asset_name,
                action=TradeAction.SELL,
                entry_price=current_price,
                quantity=quantity,
                timestamp=datetime.now(),
                status=TradeStatus.FAILED,
                reasoning=signal.reasoning,
                confidence=signal.confidence
            )
            return False, trade, message
        
        holding = self.holdings[signal.asset_id]
        
        # Check if sufficient quantity
        if quantity > holding.quantity:
            message = (
                f"Insufficient quantity. Required: {quantity}, "
                f"Available: {holding.quantity}"
            )
            logger.warning(message)
            trade = Trade(
                asset_id=signal.asset_id,
                asset_name=signal.asset_name,
                action=TradeAction.SELL,
                entry_price=current_price,
                quantity=quantity,
                timestamp=datetime.now(),
                status=TradeStatus.FAILED,
                reasoning=signal.reasoning,
                confidence=signal.confidence
            )
            return False, trade, message
        
        # Execute sell
        proceeds = current_price * quantity
        self.cash_balance += proceeds
        
        # Calculate P&L
        cost_basis = holding.average_cost * quantity
        realized_pnl = proceeds - cost_basis
        
        # Update holding
        holding.quantity -= quantity
        if holding.quantity == 0:
            del self.holdings[signal.asset_id]
        else:
            holding.current_price = current_price
            holding.current_value = current_price * holding.quantity
            holding.unrealized_pnl = (current_price - holding.average_cost) * holding.quantity
            holding.unrealized_pnl_percent = (
                (current_price - holding.average_cost) / holding.average_cost * 100
            )
        
        trade = Trade(
            asset_id=signal.asset_id,
            asset_name=signal.asset_name,
            action=TradeAction.SELL,
            entry_price=current_price,
            quantity=quantity,
            timestamp=datetime.now(),
            status=TradeStatus.EXECUTED,
            reasoning=signal.reasoning,
            confidence=signal.confidence
        )
        
        self.trades.append(trade)
        logger.info(
            f"Sell order executed: {signal.asset_name} x{quantity} @ {current_price} "
            f"(P&L: {realized_pnl})"
        )
        return True, trade, f"Sell order executed. P&L: {realized_pnl}"
    
    def get_portfolio_overview(self) -> PortfolioOverview:
        """Get current portfolio overview"""
        
        total_value = self.cash_balance
        total_invested = 0
        unrealized_pnl = 0
        
        holdings_list = []
        for holding in self.holdings.values():
            total_value += holding.current_value
            total_invested += holding.average_cost * holding.quantity
            unrealized_pnl += holding.unrealized_pnl
            holdings_list.append(holding)
        
        # Calculate realized P&L from completed trades
        realized_pnl = 0
        for trade in self.trades:
            if trade.action == TradeAction.SELL and trade.status == TradeStatus.EXECUTED:
                # Simplified: use this to track realized gains
                pass
        
        return PortfolioOverview(
            total_value=total_value,
            total_invested=total_invested,
            realized_pnl=realized_pnl,
            unrealized_pnl=unrealized_pnl,
            cash_balance=self.cash_balance,
            holdings=holdings_list,
            last_updated=datetime.now()
        )
    
    def get_performance_metrics(self) -> PerformanceMetrics:
        """Calculate performance metrics"""
        
        executed_trades = [t for t in self.trades if t.status == TradeStatus.EXECUTED]
        
        if not executed_trades:
            return PerformanceMetrics(
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate=0,
                total_profit=0,
                total_loss=0,
                net_profit=0,
                roi=0,
                max_drawdown=0,
                average_trade_return=0
            )
        
        buy_trades = [t for t in executed_trades if t.action == TradeAction.BUY]
        sell_trades = [t for t in executed_trades if t.action == TradeAction.SELL]
        
        winning_trades = 0
        losing_trades = 0
        total_profit = 0
        total_loss = 0
        
        # Simple P&L calculation
        for trade in sell_trades:
            # Find matching buy
            for buy in buy_trades:
                if buy.asset_id == trade.asset_id:
                    pnl = (trade.entry_price - buy.entry_price) * trade.quantity
                    if pnl > 0:
                        total_profit += pnl
                        winning_trades += 1
                    else:
                        total_loss += abs(pnl)
                        losing_trades += 1
                    break
        
        net_profit = total_profit - total_loss
        roi = (net_profit / self.initial_capital) * 100 if self.initial_capital > 0 else 0
        
        total_trades_count = len(executed_trades)
        win_rate = (
            (winning_trades / total_trades_count) * 100
            if total_trades_count > 0 else 0
        )
        
        return PerformanceMetrics(
            total_trades=total_trades_count,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            total_profit=total_profit,
            total_loss=total_loss,
            net_profit=net_profit,
            roi=roi,
            max_drawdown=0,  # TODO: Calculate actual max drawdown
            average_trade_return=net_profit / total_trades_count if total_trades_count > 0 else 0
        )
