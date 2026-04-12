"""
Advanced Paper Trading Simulator
Simulates real trading with accurate order execution, slippage, and position management
"""
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class PaperTradingSimulator:
    """
    Realistic paper trading simulation engine
    Maintains separate ledger for paper trades vs real trades
    """
    
    def __init__(self, initial_capital: float = 1000000):
        self.initial_capital = initial_capital
        self.cash_balance = initial_capital
        self.positions = {}  # {symbol: {"quantity": int, "avg_cost": float}}
        self.trades = []
        self.portfolio_history = []
        self.created_at = datetime.utcnow()
    
    # ============ POSITION MANAGEMENT ============
    
    def execute_buy(
        self,
        symbol: str,
        quantity: int,
        price: float,
        trade_type: str = "STOCK",
        order_id: Optional[str] = None,
        slippage_percent: float = 0.0,
        commission_percent: float = 0.1  # 0.1% commission
    ) -> Tuple[bool, Dict, str]:
        """Execute buy order in paper trading"""
        
        try:
            # Apply slippage
            actual_price = price * (1 + slippage_percent / 100)
            
            # Calculate costs
            order_value = quantity * actual_price
            commission = order_value * (commission_percent / 100)
            total_cost = order_value + commission
            
            # Check if sufficient cash
            if total_cost > self.cash_balance:
                return False, {}, f"Insufficient funds. Required: ₹{total_cost:.2f}, Available: ₹{self.cash_balance:.2f}"
            
            # Update cash
            self.cash_balance -= total_cost
            
            # Update position
            if symbol in self.positions:
                old_qty = self.positions[symbol]["quantity"]
                old_cost = self.positions[symbol]["avg_cost"]
                
                # Calculate new average cost
                new_qty = old_qty + quantity
                self.positions[symbol]["avg_cost"] = (
                    (old_qty * old_cost + quantity * actual_price) / new_qty
                )
                self.positions[symbol]["quantity"] = new_qty
            else:
                self.positions[symbol] = {
                    "quantity": quantity,
                    "avg_cost": actual_price
                }
            
            # Log trade
            trade_record = {
                "trade_id": order_id or str(uuid.uuid4()),
                "symbol": symbol,
                "action": "BUY",
                "quantity": quantity,
                "price": actual_price,
                "slippage_price": price,
                "value": order_value,
                "commission": commission,
                "total_cost": total_cost,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "EXECUTED"
            }
            self.trades.append(trade_record)
            
            logger.info(f"Paper BUY: {symbol} x{quantity} @ ₹{actual_price:.2f} (Total: ₹{total_cost:.2f})")
            
            return True, trade_record, "Order executed successfully"
        except Exception as e:
            logger.error(f"Error executing buy order: {e}")
            return False, {}, str(e)
    
    def execute_sell(
        self,
        symbol: str,
        quantity: int,
        price: float,
        order_id: Optional[str] = None,
        slippage_percent: float = 0.0,
        commission_percent: float = 0.1
    ) -> Tuple[bool, Dict, str]:
        """Execute sell order in paper trading"""
        
        try:
            # Check if position exists
            if symbol not in self.positions or self.positions[symbol]["quantity"] < quantity:
                available = self.positions.get(symbol, {}).get("quantity", 0)
                return False, {}, f"Position too small. Have: {available}, Sell: {quantity}"
            
            # Apply slippage
            actual_price = price * (1 - slippage_percent / 100)
            
            # Calculate proceeds
            order_value = quantity * actual_price
            commission = order_value * (commission_percent / 100)
            net_proceeds = order_value - commission
            
            # Update cash
            self.cash_balance += net_proceeds
            
            # Calculate P&L
            avg_cost = self.positions[symbol]["avg_cost"]
            pnl = (actual_price - avg_cost) * quantity
            pnl_percent = ((actual_price - avg_cost) / avg_cost) * 100
            
            # Update position
            self.positions[symbol]["quantity"] -= quantity
            if self.positions[symbol]["quantity"] == 0:
                del self.positions[symbol]
            
            # Log trade
            trade_record = {
                "trade_id": order_id or str(uuid.uuid4()),
                "symbol": symbol,
                "action": "SELL",
                "quantity": quantity,
                "price": actual_price,
                "slippage_price": price,
                "value": order_value,
                "commission": commission,
                "net_proceeds": net_proceeds,
                "avg_cost": avg_cost,
                "pnl": pnl,
                "pnl_percent": pnl_percent,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "EXECUTED"
            }
            self.trades.append(trade_record)
            
            logger.info(f"Paper SELL: {symbol} x{quantity} @ ₹{actual_price:.2f} (P&L: ₹{pnl:.2f})")
            
            return True, trade_record, "Order executed successfully"
        except Exception as e:
            logger.error(f"Error executing sell order: {e}")
            return False, {}, str(e)
    
    def execute_stop_loss(
        self,
        symbol: str,
        stop_loss_price: float
    ) -> Tuple[bool, Optional[Dict]]:
        """Execute a stop loss order if position price falls below threshold"""
        
        if symbol not in self.positions:
            return False, None
        
        position = self.positions[symbol]
        if position["quantity"] == 0:
            return False, None
        
        # For paper trading, we assume market sell at stop loss price
        success, trade, _ = self.execute_sell(
            symbol,
            position["quantity"],
            stop_loss_price
        )
        
        if success:
            trade["exit_reason"] = "STOP_LOSS"
        
        return success, trade if success else None
    
    def execute_profit_target(
        self,
        symbol: str,
        target_price: float,
        profit_percent: Optional[float] = None
    ) -> Tuple[bool, Optional[Dict]]:
        """Execute a profit target order"""
        
        if symbol not in self.positions:
            return False, None
        
        position = self.positions[symbol]
        
        # Verify target is profitable
        if profit_percent:
            required_price = position["avg_cost"] * (1 + profit_percent / 100)
            if target_price < required_price:
                logger.warning(f"Target price {target_price} doesn't meet profit target {profit_percent}%")
        
        # Execute partial or full exit
        success, trade, _ = self.execute_sell(
            symbol,
            position["quantity"],
            target_price
        )
        
        if success:
            trade["exit_reason"] = "PROFIT_TARGET"
        
        return success, trade if success else None
    
    # ============ PORTFOLIO ANALYSIS ============
    
    def get_portfolio_value(self, current_prices: Dict[str, float]) -> Dict:
        """
        Calculate current portfolio value and P&L
        
        Args:
            current_prices: Dict of {symbol: current_price}
        """
        
        stock_value = 0
        unrealized_pnl = 0
        
        for symbol, position in self.positions.items():
            current_price = current_prices.get(symbol, position["avg_cost"])
            shares_value = position["quantity"] * current_price
            position_pnl = (current_price - position["avg_cost"]) * position["quantity"]
            
            stock_value += shares_value
            unrealized_pnl += position_pnl
        
        # Calculate realized P&L from closed trades
        realized_pnl = 0
        for trade in self.trades:
            if trade["action"] == "SELL" and "pnl" in trade:
                realized_pnl += trade["pnl"]
        
        total_value = self.cash_balance + stock_value
        total_pnl = realized_pnl + unrealized_pnl
        roi = (total_pnl / self.initial_capital) * 100 if self.initial_capital > 0 else 0
        
        return {
            "total_value": total_value,
            "cash_balance": self.cash_balance,
            "stock_value": stock_value,
            "realized_pnl": realized_pnl,
            "unrealized_pnl": unrealized_pnl,
            "total_pnl": total_pnl,
            "roi_percent": roi,
            "portfolio_change_percent": ((total_value - self.initial_capital) / self.initial_capital) * 100,
            "positions_count": len(self.positions)
        }
    
    def get_positions(self, current_prices: Dict[str, float] = {}) -> List[Dict]:
        """Get detailed position information"""
        
        positions = []
        
        for symbol, position in self.positions.items():
            current_price = current_prices.get(symbol, position["avg_cost"])
            
            position_detail = {
                "symbol": symbol,
                "quantity": position["quantity"],
                "avg_cost": position["avg_cost"],
                "current_price": current_price,
                "position_value": position["quantity"] * current_price,
                "unrealized_pnl": (current_price - position["avg_cost"]) * position["quantity"],
                "unrealized_pnl_percent": ((current_price - position["avg_cost"]) / position["avg_cost"]) * 100,
                "days_held": (datetime.utcnow() - datetime.fromisoformat(
                    next((t["timestamp"] for t in self.trades if t["symbol"] == symbol and t["action"] == "BUY"), 
                    datetime.utcnow().isoformat())
                )).days
            }
            
            positions.append(position_detail)
        
        return positions
    
    # ============ PERFORMANCE ANALYTICS ============
    
    def get_performance_metrics(self, current_prices: Dict[str, float] = {}) -> Dict:
        """Calculate comprehensive performance metrics"""
        
        portfolio = self.get_portfolio_value(current_prices)
        
        # Win rate
        sell_trades = [t for t in self.trades if t["action"] == "SELL"]
        winning_trades = len([t for t in sell_trades if t.get("pnl", 0) > 0])
        total_closed_trades = len(sell_trades)
        win_rate = (winning_trades / total_closed_trades * 100) if total_closed_trades > 0 else 0
        
        # Max drawdown
        cumulative_pnl = []
        running_pnl = 0
        for trade in self.trades:
            if trade["action"] == "SELL":
                running_pnl += trade.get("pnl", 0)
            cumulative_pnl.append(running_pnl)
        
        max_pnl = max(cumulative_pnl) if cumulative_pnl else 0
        min_pnl = min(cumulative_pnl) if cumulative_pnl else 0
        max_drawdown = min_pnl - max_pnl if max_pnl > 0 else 0
        
        # Profit factor
        gross_profit = sum([t.get("pnl", 0) for t in self.trades if t.get("pnl", 0) > 0])
        gross_loss = abs(sum([t.get("pnl", 0) for t in self.trades if t.get("pnl", 0) < 0]))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        return {
            "total_trades": len(self.trades),
            "buy_trades": len([t for t in self.trades if t["action"] == "BUY"]),
            "sell_trades": total_closed_trades,
            "winning_trades": winning_trades,
            "losing_trades": len([t for t in sell_trades if t.get("pnl", 0) <= 0]),
            "win_rate": win_rate,
            "total_pnl": portfolio["total_pnl"],
            "realized_pnl": portfolio["realized_pnl"],
            "unrealized_pnl": portfolio["unrealized_pnl"],
            "roi_percent": portfolio["roi_percent"],
            "max_drawdown": max_drawdown,
            "profit_factor": profit_factor,
            "average_win": (gross_profit / winning_trades) if winning_trades > 0 else 0,
            "average_loss": (gross_loss / (total_closed_trades - winning_trades)) if (total_closed_trades - winning_trades) > 0 else 0,
            "average_trade_return": (portfolio["total_pnl"] / total_closed_trades) if total_closed_trades > 0 else 0,
        }
    
    def get_trade_history(
        self,
        symbol: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get trade history with filtering"""
        
        trades = self.trades
        
        if symbol:
            trades = [t for t in trades if t["symbol"] == symbol]
        
        if action:
            trades = [t for t in trades if t["action"] == action]
        
        # Return most recent trades first
        return sorted(trades, key=lambda t: t["timestamp"], reverse=True)[:limit]
    
    def export_trades_as_table(self) -> str:
        """Export trades as formatted table"""
        
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            "timestamp", "symbol", "action", "quantity", "price",
            "value", "commission", "pnl", "pnl_percent"
        ])
        
        writer.writeheader()
        
        for trade in self.trades:
            writer.writerow({
                "timestamp": trade.get("timestamp"),
                "symbol": trade.get("symbol"),
                "action": trade.get("action"),
                "quantity": trade.get("quantity"),
                "price": f"₹{trade.get('price', 0):.2f}",
                "value": f"₹{trade.get('value', 0):.2f}",
                "commission": f"₹{trade.get('commission', 0):.2f}",
                "pnl": f"₹{trade.get('pnl', 'N/A')}",
                "pnl_percent": f"{trade.get('pnl_percent', 'N/A')}%"
            })
        
        return output.getvalue()

# Global instance
paper_trader: Optional[PaperTradingSimulator] = None

async def get_paper_trader(initial_capital: float = 1000000) -> PaperTradingSimulator:
    """Get or create paper trading simulator"""
    global paper_trader
    if not paper_trader:
        paper_trader = PaperTradingSimulator(initial_capital)
    return paper_trader
