"""
Task Scheduler and Trade Execution Orchestrator
Handles automated end-of-day reports at 3:30 PM IST and continuous trade monitoring
"""
import logging
import asyncio
from typing import Dict, Optional, Callable, List
from datetime import datetime, time
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

class TradeExecutionOrchestrator:
    """
    Main orchestrator for the AI trading system
    Coordinates all components for trade execution and reporting
    """
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
        self.daily_report_callbacks = []
        self.market_data_callbacks = []
        self.trade_callbacks = []
        
        # IST timezone
        self.ist = pytz.timezone('Asia/Kolkata')
    
    def start(self):
        """Start the orchestrator and scheduler"""
        try:
            # Schedule end-of-day report at 3:30 PM IST
            self.scheduler.add_job(
                self.end_of_day_report,
                CronTrigger(
                    hour=15,  # 3 PM
                    minute=30,
                    timezone=self.ist
                ),
                id='eod_report',
                name='End of Day Report at 3:30 PM IST'
            )
            
            # Schedule market data updates every 5 minutes during market hours
            self.scheduler.add_job(
                self.update_market_data,
                CronTrigger(
                    minute='*/5',  # Every 5 minutes
                    hour='9-15',  # 9 AM to 3 PM IST
                    day_of_week='0-4'  # Monday to Friday
                ),
                id='market_data',
                name='Market Data Update'
            )
            
            # Schedule trade signal scanning every minute
            self.scheduler.add_job(
                self.scan_trade_signals,
                CronTrigger(
                    minute='*',  # Every minute
                    hour='9-15',  # During market hours
                    day_of_week='0-4'
                ),
                id='trade_signals',
                name='Trade Signal Scan'
            )
            
            self.scheduler.start()
            self.is_running = True
            logger.info("Trade Execution Orchestrator started")
        except Exception as e:
            logger.error(f"Error starting orchestrator: {e}")
            raise
    
    def stop(self):
        """Stop the orchestrator and scheduler"""
        try:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Trade Execution Orchestrator stopped")
        except Exception as e:
            logger.error(f"Error stopping orchestrator: {e}")
    
    async def end_of_day_report(self):
        """
        Generate end-of-day report at 3:30 PM IST
        Called automatically by scheduler
        """
        try:
            logger.info("=" * 50)
            logger.info("END OF DAY REPORT - 3:30 PM IST")
            logger.info("=" * 50)
            
            # Execute all registered EOD callbacks
            for callback in self.daily_report_callbacks:
                try:
                    await callback()
                except Exception as e:
                    logger.error(f"Error in EOD callback: {e}")
            
            logger.info("End of day report completed")
        except Exception as e:
            logger.error(f"Error generating end of day report: {e}")
    
    async def update_market_data(self):
        """
        Update market data every 5 minutes
        Called automatically by scheduler
        """
        try:
            logger.debug("Updating market data...")
            
            for callback in self.market_data_callbacks:
                try:
                    await callback()
                except Exception as e:
                    logger.error(f"Error in market data callback: {e}")
        except Exception as e:
            logger.error(f"Error updating market data: {e}")
    
    async def scan_trade_signals(self):
        """
        Scan for trade signals every minute
        Called automatically by scheduler
        """
        try:
            for callback in self.trade_callbacks:
                try:
                    await callback()
                except Exception as e:
                    logger.error(f"Error in trade signal callback: {e}")
        except Exception as e:
            logger.error(f"Error scanning trade signals: {e}")
    
    def register_eod_callback(self, callback: Callable):
        """Register callback for end-of-day report"""
        self.daily_report_callbacks.append(callback)
        logger.info(f"Registered EOD callback: {callback.__name__}")
    
    def register_market_data_callback(self, callback: Callable):
        """Register callback for market data updates"""
        self.market_data_callbacks.append(callback)
        logger.info(f"Registered market data callback: {callback.__name__}")
    
    def register_trade_callback(self, callback: Callable):
        """Register callback for trade signal scanning"""
        self.trade_callbacks.append(callback)
        logger.info(f"Registered trade callback: {callback.__name__}")
    
    def is_market_open(self) -> bool:
        """Check if Indian market is open"""
        now = datetime.now(self.ist)
        
        # Market hours: 9:15 AM to 3:30 PM, Monday to Friday
        if now.weekday() >= 5:  # Saturday or Sunday
            return False
        
        market_open = time(9, 15)
        market_close = time(15, 30)
        
        return market_open <= now.time() <= market_close
    
    def get_scheduler_status(self) -> Dict:
        """Get current scheduler status"""
        
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None
            })
        
        return {
            "running": self.is_running,
            "market_open": self.is_market_open(),
            "jobs": jobs,
            "current_time_ist": datetime.now(self.ist).isoformat()
        }

class AutomatedTradeExecutor:
    """
    Automated trade execution engine
    Executes trades based on AI signals with proper risk management
    """
    
    def __init__(
        self,
        paper_trader,
        groww_client,
        ai_engine,
        explainable_logger
    ):
        self.paper_trader = paper_trader
        self.groww_client = groww_client
        self.ai_engine = ai_engine
        self.explainable_logger = explainable_logger
        self.live_mode_trades = []
        self.paper_mode_trades = []
    
    async def execute_signal(
        self,
        signal: Dict,
        mode: str = "PAPER",  # PAPER or LIVE
        slippage_percent: float = 0.05,
        use_limit_order: bool = True
    ) -> Dict:
        """
        Execute a trade signal with proper error handling
        
        Args:
            signal: AI trade signal
            mode: PAPER (simulation) or LIVE (real trading)
            slippage_percent: Expected price slippage
            use_limit_order: Use limit orders for better pricing
        """
        
        try:
            symbol = signal["symbol"]
            action = signal["action"]
            price = signal["price"]
            quantity = signal.get("quantity", 1)
            
            logger.info(f"Executing {action} signal for {symbol} ({mode} mode)")
            
            if mode == "PAPER":
                return await self._execute_paper_trade(
                    symbol, action, price, quantity, signal, slippage_percent
                )
            elif mode == "LIVE":
                return await self._execute_live_trade(
                    symbol, action, price, quantity, signal, use_limit_order
                )
            else:
                raise ValueError(f"Unknown mode: {mode}")
        except Exception as e:
            logger.error(f"Error executing signal: {e}")
            return {
                "success": False,
                "error": str(e),
                "signal": signal
            }
    
    async def _execute_paper_trade(
        self,
        symbol: str,
        action: str,
        price: float,
        quantity: int,
        signal: Dict,
        slippage_percent: float
    ) -> Dict:
        """Execute paper trade"""
        
        try:
            if action == "BUY":
                success, trade, message = self.paper_trader.execute_buy(
                    symbol, quantity, price, slippage_percent=slippage_percent
                )
            else:  # SELL
                success, trade, message = self.paper_trader.execute_sell(
                    symbol, quantity, price, slippage_percent=slippage_percent
                )
            
            if success:
                # Log with reasoning
                await self.explainable_logger.log_trade_with_reasoning(
                    symbol=symbol,
                    action=action,
                    entry_price=price,
                    quantity=quantity,
                    ai_analysis=signal,
                    technical_context=signal.get("technical_context", {}),
                    market_context=signal.get("market_context", {}),
                    trade_id=trade["trade_id"],
                    mode="PAPER"
                )
                
                self.paper_mode_trades.append(trade)
                logger.info(f"Paper trade executed: {message}")
            else:
                logger.warning(f"Paper trade failed: {message}")
            
            return {
                "success": success,
                "trade": trade,
                "message": message,
                "mode": "PAPER"
            }
        except Exception as e:
            logger.error(f"Error executing paper trade: {e}")
            return {
                "success": False,
                "error": str(e),
                "mode": "PAPER"
            }
    
    async def _execute_live_trade(
        self,
        symbol: str,
        action: str,
        price: float,
        quantity: int,
        signal: Dict,
        use_limit_order: bool = True
    ) -> Dict:
        """Execute live trade via Groww API"""
        
        try:
            # Only execute if live trading is enabled
            if not settings.LIVE_TRADING_ENABLED:
                logger.warning("Live trading is disabled")
                return {
                    "success": False,
                    "error": "Live trading is disabled",
                    "mode": "LIVE"
                }
            
            # Place order via Groww API
            order_type = "LIMIT" if use_limit_order else "MARKET"
            
            result = await self.groww_client.place_order(
                symbol=symbol,
                action=action,
                quantity=quantity,
                order_type=order_type,
                price=price if use_limit_order else None
            )
            
            if result:
                # Log with reasoning
                await self.explainable_logger.log_trade_with_reasoning(
                    symbol=symbol,
                    action=action,
                    entry_price=result.get("execution_price", price),
                    quantity=quantity,
                    ai_analysis=signal,
                    technical_context=signal.get("technical_context", {}),
                    market_context=signal.get("market_context", {}),
                    trade_id=result.get("order_id"),
                    mode="LIVE"
                )
                
                self.live_mode_trades.append(result)
                logger.info(f"Live trade executed: {symbol} {action}")
            else:
                logger.warning("Order placement failed")
            
            return {
                "success": bool(result),
                "order": result,
                "mode": "LIVE"
            }
        except Exception as e:
            logger.error(f"Error executing live trade: {e}")
            return {
                "success": False,
                "error": str(e),
                "mode": "LIVE"
            }
    
    async def set_stop_loss(
        self,
        symbol: str,
        stop_loss_price: float,
        mode: str = "PAPER"
    ) -> bool:
        """Set stop loss for a position"""
        
        try:
            if mode == "PAPER":
                success, _ = self.paper_trader.execute_stop_loss(
                    symbol, stop_loss_price
                )
            else:
                # Would need Groww API support for live stop loss
                logger.warning("Live stop loss orders need API integration")
                success = False
            
            return success
        except Exception as e:
            logger.error(f"Error setting stop loss: {e}")
            return False
    
    async def set_profit_target(
        self,
        symbol: str,
        target_price: float,
        mode: str = "PAPER"
    ) -> bool:
        """Set profit target for a position"""
        
        try:
            if mode == "PAPER":
                success, _ = self.paper_trader.execute_profit_target(
                    symbol, target_price
                )
            else:
                logger.warning("Live profit targets need API integration")
                success = False
            
            return success
        except Exception as e:
            logger.error(f"Error setting profit target: {e}")
            return False
    
    def get_execution_stats(self) -> Dict:
        """Get trade execution statistics"""
        
        return {
            "paper_trades": len(self.paper_mode_trades),
            "live_trades": len(self.live_mode_trades),
            "total_trades": len(self.paper_mode_trades) + len(self.live_mode_trades),
            "paper_performance": self._calculate_performance(self.paper_mode_trades),
            "live_performance": self._calculate_performance(self.live_mode_trades)
        }
    
    def _calculate_performance(self, trades: List[Dict]) -> Dict:
        """Calculate performance metrics for trades"""
        
        if not trades:
            return {
                "trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0,
                "total_pnl": 0
            }
        
        sell_trades = [t for t in trades if t.get("action") == "SELL"]
        winning = [t for t in sell_trades if t.get("pnl", 0) > 0]
        losing = [t for t in sell_trades if t.get("pnl", 0) < 0]
        
        return {
            "trades": len(trades),
            "winning_trades": len(winning),
            "losing_trades": len(losing),
            "win_rate": (len(winning) / len(sell_trades) * 100) if sell_trades else 0,
            "total_pnl": sum([t.get("pnl", 0) for t in sell_trades])
        }

# Global instances
orchestrator: Optional[TradeExecutionOrchestrator] = None
executor: Optional[AutomatedTradeExecutor] = None

async def get_orchestrator() -> TradeExecutionOrchestrator:
    """Get or create orchestrator"""
    global orchestrator
    if not orchestrator:
        orchestrator = TradeExecutionOrchestrator()
    return orchestrator

async def get_executor(
    paper_trader,
    groww_client,
    ai_engine,
    explainable_logger
) -> AutomatedTradeExecutor:
    """Get or create trade executor"""
    global executor
    if not executor:
        executor = AutomatedTradeExecutor(
            paper_trader, groww_client, ai_engine, explainable_logger
        )
    return executor
