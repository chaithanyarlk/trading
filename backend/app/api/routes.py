from fastapi import APIRouter, HTTPException, WebSocket
from typing import List, Dict
from datetime import datetime
import json
import asyncio
import logging

from app.models.schemas import (
    TradeSignal, TradeAction, PortfolioOverview, PerformanceMetrics,
    OptionsStrategy, MutualFundRecommendation, Trade
)
from app.services.trading_engine import TradingEngine
from app.services.paper_trading import PaperTradingSimulator
from app.services.groww_api import GrowwAPIClient
from app.services.ai_reasoning import AIReasoningEngine
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Global instances (would use better state management in production)
ai_engine = AIReasoningEngine()
paper_trader = PaperTradingSimulator(settings.PAPER_TRADING_INITIAL_CAPITAL)
groww_client = GrowwAPIClient(settings.GROWW_API_KEY, settings.GROWW_API_BASE_URL)
trading_engine = TradingEngine(groww_client=groww_client)

# Store connected websocket clients
connected_clients: List[WebSocket] = []

@router.on_event("startup")
async def startup():
    """Initialize services on startup"""
    await groww_client.connect()
    logger.info("Trading system started")

@router.on_event("shutdown")
async def shutdown():
    """Clean up on shutdown"""
    await groww_client.disconnect()
    logger.info("Trading system stopped")

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": settings.APP_VERSION
    }

@router.get("/api/ai/provider")
async def get_ai_provider():
    """Get current AI provider configuration"""
    from app.services.ai_provider import ai_provider
    return {
        "status": "active",
        **ai_provider.get_provider_info()
    }

@router.post("/api/signals/generate")
async def generate_signals(market_data: Dict) -> List[TradeSignal]:
    """Generate trade signals from market data with Claude AI reasoning"""
    try:
        # Generate signals with Claude AI analysis
        signals = await trading_engine.generate_trade_signals(market_data)
        
        # Enhance with AI explanations
        enhanced_signals = []
        for signal in signals:
            try:
                explanation = await ai_engine.generate_trade_explanation({
                    "asset": signal.asset_name,
                    "action": signal.action.value,
                    "price": signal.price,
                    "indicators": {ind.name: ind.value for ind in signal.indicators}
                })
                # Add explanation to signal
                signal_dict = signal.dict()
                signal_dict["reasoning"] = explanation.get("reasoning", "AI analysis unavailable")
                enhanced_signals.append(signal_dict)
            except Exception as e:
                logger.error(f"Error getting AI explanation: {e}")
                enhanced_signals.append(signal.dict())
        
        # Broadcast to connected clients
        for client in connected_clients:
            try:
                for signal_dict in enhanced_signals:
                    await client.send_json({
                        "type": "signal",
                        "data": signal_dict
                    })
            except Exception as e:
                logger.error(f"Error broadcasting signal: {e}")
        
        return enhanced_signals
    except Exception as e:
        logger.error(f"Error generating signals: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/portfolio")
async def get_portfolio() -> PortfolioOverview:
    """Get current portfolio overview"""
    try:
        overview = paper_trader.get_portfolio_overview()
        return overview
    except Exception as e:
        logger.error(f"Error fetching portfolio: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/performance")
async def get_performance() -> PerformanceMetrics:
    """Get performance metrics"""
    try:
        metrics = paper_trader.get_performance_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Error calculating performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/trades/execute")
async def execute_trade(signal: TradeSignal, quantity: int) -> Dict:
    """Execute a paper trade"""
    try:
        success, trade, message = paper_trader.execute_trade(
            signal, signal.price, quantity
        )
        
        return {
            "success": success,
            "trade": trade.dict() if trade else None,
            "message": message
        }
    except Exception as e:
        logger.error(f"Error executing trade: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/trades")
async def get_trades() -> List[Trade]:
    """Get all trades"""
    try:
        return paper_trader.trades
    except Exception as e:
        logger.error(f"Error fetching trades: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/options/suggestions")
async def get_options_suggestions(underlying: str, current_price: float) -> List[OptionsStrategy]:
    """Get options trading suggestions from Groww API"""
    try:
        suggestions = await trading_engine.generate_options_suggestions(underlying, current_price)
        logger.info(f"Fetched options for {underlying} from API (real or fallback)")
        return suggestions
    except Exception as e:
        logger.error(f"Error generating options suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/mutual-funds/recommendations")
async def get_mutual_fund_recommendations() -> List[MutualFundRecommendation]:
    """Get mutual fund recommendations from Groww API"""
    try:
        recommendations = await trading_engine.generate_mutual_fund_recommendations()
        logger.info(f"Fetched {len(recommendations)} mutual funds from API")
        return recommendations
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/stocks/watch")
async def get_stocks_to_watch() -> List[Dict]:
    """Get stocks to watch"""
    try:
        stocks = trading_engine.get_stocks_to_watch()
        return stocks
    except Exception as e:
        logger.error(f"Error fetching stocks to watch: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/trading/mode")
async def set_trading_mode(live_mode: bool) -> Dict:
    """Toggle between live and paper trading modes"""
    try:
        if live_mode and not settings.LIVE_TRADING_ENABLED:
            raise HTTPException(
                status_code=403,
                detail="Live trading is not enabled. Enable it in environment settings."
            )
        
        return {
            "mode": "LIVE" if live_mode else "PAPER",
            "message": f"Trading mode set to {'LIVE' if live_mode else 'PAPER'}",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error setting trading mode: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.websocket("/ws/trades")
async def websocket_trade_stream(websocket: WebSocket):
    """WebSocket connection for real-time trade stream"""
    await websocket.accept()
    connected_clients.append(websocket)
    
    try:
        while True:
            # Keep connection open and receive any messages
            data = await websocket.receive_text()
            # Echo back or process incoming commands
            if data:
                await websocket.send_json({
                    "type": "ack",
                    "message": "Command received"
                })
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        connected_clients.remove(websocket)

@router.get("/api/market/quote")
async def get_market_quote(symbol: str) -> Dict:
    """Get stock quote from market"""
    try:
        quote = await groww_client.get_stock_quote(symbol)
        if not quote:
            raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")
        return quote
    except Exception as e:
        logger.error(f"Error fetching quote: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/market/historical")
async def get_historical_data(
    symbol: str, period: str = "1y", interval: str = "1d"
) -> List[Dict]:
    """Get historical market data"""
    try:
        data = await groww_client.get_historical_data(symbol, period, interval)
        if not data:
            raise HTTPException(
                status_code=404,
                detail=f"Historical data for {symbol} not available"
            )
        return data
    except Exception as e:
        logger.error(f"Error fetching historical data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/portfolio/analyze")
async def analyze_portfolio(holdings: Dict) -> Dict:
    """Get Claude AI analysis of current portfolio"""
    try:
        analysis = await ai_engine.analyze_portfolio_positions(
            holdings=holdings.get("positions", []),
            market_data=holdings.get("market_data", {})
        )
        logger.info("Generated portfolio analysis via Claude AI")
        return {
            "analysis": analysis,
            "source": "Claude AI",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error analyzing portfolio: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============= NEW ADVANCED ROUTES (AI TRADING PLATFORM) =============

# STOCK ANALYSIS ROUTES
@router.post("/api/advanced/analysis/comprehensive")
async def comprehensive_stock_analysis(symbol: str, risk_profile: str = "BALANCED") -> Dict:
    """
    Comprehensive AI analysis of a stock using advanced local Claude model
    
    Returns: AI signal (BUY/SELL/HOLD), confidence, target price, stop loss, reasoning
    """
    try:
        from app.services.ai_analysis_advanced import ai_engine as advanced_ai
        
        # Get market data
        quote = await groww_client.get_stock_quote(symbol)
        historical = await groww_client.get_historical_data(symbol, period="1y", interval="1d")
        
        if not quote or not historical:
            raise HTTPException(status_code=404, detail=f"Data for {symbol} not available")
        
        # Perform advanced analysis
        analysis = await advanced_ai.analyze_stock_comprehensive(
            symbol=symbol,
            current_price=quote.get("price", 0),
            market_data=historical,
            risk_profile=risk_profile
        )
        
        logger.info(f"Advanced analysis completed for {symbol}")
        return {
            "symbol": symbol,
            "action": analysis.get("action"),
            "confidence": analysis.get("confidence"),
            "score": analysis.get("score"),
            "reasoning": analysis.get("reasoning"),
            "target_price": analysis.get("target_price"),
            "stop_loss": analysis.get("stop_loss"),
            "position_size_percent": analysis.get("position_size_percent"),
            "key_levels": analysis.get("key_levels"),
            "risk_level": analysis.get("risk_level"),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in advanced stock analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# TRADE EXECUTION ROUTES
@router.post("/api/advanced/trades/execute")
async def execute_advanced_trade(
    symbol: str,
    action: str,
    quantity: int,
    mode: str = "PAPER"
) -> Dict:
    """
    Execute a trade with full reasoning logging and position management
    
    Modes: PAPER (simulation) or LIVE (real trading, if enabled)
    """
    try:
        from app.services.orchestrator import get_executor
        from app.services.paper_trading_advanced import paper_trader as pt
        from app.services.ai_analysis_advanced import ai_engine as advanced_ai
        from app.services.explainable_ai import explainable_logger
        
        # Get current price
        quote = await groww_client.get_stock_quote(symbol)
        price = quote.get("price", 0)
        
        if not price:
            raise HTTPException(status_code=404, detail=f"Price for {symbol} not available")
        
        # Create signal
        signal = {
            "symbol": symbol,
            "action": action,
            "price": price,
            "quantity": quantity,
            "timestamp": datetime.now().isoformat()
        }
        
        # Get executor
        executor = await get_executor(pt, groww_client, advanced_ai, explainable_logger)
        
        # Execute trade
        result = await executor.execute_signal(signal, mode=mode)
        
        logger.info(f"Trade executed: {symbol} {action} x{quantity} ({mode})")
        return result
    except Exception as e:
        logger.error(f"Error executing trade: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/advanced/trades/set-stop-loss")
async def set_stop_loss(symbol: str, stop_loss_price: float, mode: str = "PAPER") -> Dict:
    """Set stop loss for an existing position"""
    try:
        from app.services.orchestrator import get_executor
        from app.services.paper_trading_advanced import paper_trader as pt
        from app.services.ai_analysis_advanced import ai_engine as advanced_ai
        from app.services.explainable_ai import explainable_logger
        
        executor = await get_executor(pt, groww_client, advanced_ai, explainable_logger)
        success = await executor.set_stop_loss(symbol, stop_loss_price, mode)
        
        logger.info(f"Stop loss set: {symbol} @ {stop_loss_price} ({mode})")
        return {
            "success": success,
            "symbol": symbol,
            "stop_loss": stop_loss_price,
            "mode": mode
        }
    except Exception as e:
        logger.error(f"Error setting stop loss: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/advanced/trades/set-target")
async def set_profit_target(symbol: str, target_price: float, mode: str = "PAPER") -> Dict:
    """Set profit target for an existing position"""
    try:
        from app.services.orchestrator import get_executor
        from app.services.paper_trading_advanced import paper_trader as pt
        from app.services.ai_analysis_advanced import ai_engine as advanced_ai
        from app.services.explainable_ai import explainable_logger
        
        executor = await get_executor(pt, groww_client, advanced_ai, explainable_logger)
        success = await executor.set_profit_target(symbol, target_price, mode)
        
        logger.info(f"Profit target set: {symbol} @ {target_price} ({mode})")
        return {
            "success": success,
            "symbol": symbol,
            "target": target_price,
            "mode": mode
        }
    except Exception as e:
        logger.error(f"Error setting profit target: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# PORTFOLIO ROUTES
@router.get("/api/advanced/portfolio/performance")
async def get_advanced_portfolio_performance(mode: str = "PAPER") -> Dict:
    """Get detailed portfolio performance metrics"""
    try:
        from app.services.paper_trading_advanced import paper_trader as pt
        
        portfolio_value = pt.get_portfolio_value()
        metrics = pt.get_performance_metrics()
        positions = pt.get_positions()
        
        logger.info(f"Portfolio performance retrieved ({mode})")
        return {
            "portfolio_value": portfolio_value,
            "performance_metrics": metrics,
            "positions": positions,
            "mode": mode,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching portfolio performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# OPTIONS TRADING ROUTES
@router.post("/api/advanced/options/select-strategy")
async def select_options_strategy(
    symbol: str,
    market_sentiment: str = "NEUTRAL",
    volatility_level: str = "NORMAL"
) -> Dict:
    """
    AI-driven options strategy selection
    
    Returns recommended strategy with Greeks, probability of profit, risk/reward
    """
    try:
        from app.services.options_trading_engine import options_engine
        
        # Get options chain
        chain = await groww_client.get_options_chain(symbol)
        
        if not chain:
            raise HTTPException(status_code=404, detail=f"Options data for {symbol} not available")
        
        # Select strategy using AI
        strategy = await options_engine.analyze_and_select_strategy(
            symbol=symbol,
            options_chain=chain,
            market_sentiment=market_sentiment,
            volatility_level=volatility_level
        )
        
        logger.info(f"Options strategy selected for {symbol}: {strategy.get('strategy_type')}")
        return {
            "symbol": symbol,
            "strategy_type": strategy.get("strategy_type"),
            "recommendation": strategy.get("recommendation"),
            "probability_of_profit": strategy.get("probability_of_profit"),
            "expected_return_percent": strategy.get("expected_return_percent"),
            "risk_reward_ratio": strategy.get("risk_reward_ratio"),
            "greeks": strategy.get("greeks"),
            "breakevens": strategy.get("breakevens"),
            "max_profit": strategy.get("max_profit"),
            "max_loss": strategy.get("max_loss"),
            "reasoning": strategy.get("reasoning"),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error selecting options strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# MUTUAL FUNDS ROUTES
@router.post("/api/advanced/mutual-funds/recommend")
async def recommend_mutual_funds(
    amount: float,
    investment_horizon: str = "LONG",
    risk_profile: str = "BALANCED",
    objective: str = "GROWTH"
) -> Dict:
    """
    AI-powered mutual fund recommendations based on investor profile
    """
    try:
        from app.services.mutual_fund_analyzer import fund_analyzer
        
        # Get all available funds
        all_funds = await groww_client.get_mutual_funds()
        
        if not all_funds:
            raise HTTPException(status_code=404, detail="Mutual funds data not available")
        
        # Get AI recommendations
        recommendations = await fund_analyzer.recommend_funds(
            all_funds=all_funds,
            amount=amount,
            investment_horizon=investment_horizon,
            risk_profile=risk_profile,
            objective=objective
        )
        
        logger.info(f"Mutual fund recommendations generated for ₹{amount}")
        return {
            "recommended_funds": recommendations.get("recommended_funds"),
            "total_allocation": amount,
            "investment_horizon": investment_horizon,
            "risk_profile": risk_profile,
            "objective": objective,
            "reasoning": recommendations.get("reasoning"),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error recommending mutual funds: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/advanced/mutual-funds/sip-plan")
async def create_sip_plan(
    fund_name: str,
    monthly_amount: float,
    duration_months: int,
    expected_annual_return: float = 12.0
) -> Dict:
    """Create SIP plan with maturity projections"""
    try:
        from app.services.mutual_fund_analyzer import fund_analyzer
        
        plan = await fund_analyzer.create_sip_plan(
            fund_name=fund_name,
            monthly_amount=monthly_amount,
            duration_months=duration_months,
            expected_annual_return=expected_annual_return
        )
        
        logger.info(f"SIP plan created: {fund_name} - ₹{monthly_amount}/month x{duration_months}m")
        return {
            "fund_name": fund_name,
            "monthly_investment": monthly_amount,
            "duration_months": duration_months,
            "total_investment": plan.get("total_investment"),
            "expected_maturity_value": plan.get("maturity_value"),
            "expected_gain": plan.get("gain"),
            "gain_percent": (plan.get("gain", 0) / plan.get("total_investment", 1) * 100) if plan.get("total_investment") else 0,
            "cagr": plan.get("cagr"),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error creating SIP plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# REPORTING ROUTES
@router.post("/api/advanced/reports/generate-daily")
async def generate_daily_report() -> Dict:
    """
    Generate comprehensive end-of-day report with AI insights
    
    Includes: trades summary, performance metrics, strategy analysis, AI insights, watchlist
    """
    try:
        from app.services.report_generator import report_generator
        
        # Generate report
        report = await report_generator.generate_daily_report()
        
        logger.info("Daily report generated")
        return {
            "date": report.get("date"),
            "summary": report.get("summary"),
            "trades_table": report.get("trades_table"),
            "performance_comparison": report.get("performance_comparison"),
            "strategy_analysis": report.get("strategy_analysis"),
            "ai_insights": report.get("ai_insights"),
            "mistakes_and_lessons": report.get("mistakes_and_lessons"),
            "tomorrow_watchlist": report.get("tomorrow_watchlist"),
            "recommendations": report.get("recommendations"),
            "graph_data": report.get("graph_data"),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error generating daily report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/advanced/reports/export-html")
async def export_report_as_html() -> Dict:
    """Export latest report as HTML"""
    try:
        from app.services.report_generator import report_generator
        
        report = await report_generator.generate_daily_report()
        html_content = await report_generator.export_report_as_html(report)
        
        logger.info("Report exported as HTML")
        return {
            "format": "HTML",
            "content": html_content,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error exporting report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# TRADE REASONING ROUTES
@router.get("/api/advanced/reasoning/trades/{trade_id}")
async def get_trade_reasoning(trade_id: str) -> Dict:
    """Get detailed reasoning and explanation for a specific trade"""
    try:
        from app.services.explainable_ai import explainable_logger
        
        reasoning = await explainable_logger.get_trade_log(trade_id)
        
        if not reasoning:
            raise HTTPException(status_code=404, detail=f"Trade {trade_id} not found")
        
        logger.info(f"Trade reasoning retrieved: {trade_id}")
        return {
            "trade_id": trade_id,
            "symbol": reasoning.get("symbol"),
            "action": reasoning.get("action"),
            "entry_price": reasoning.get("entry_price"),
            "exit_price": reasoning.get("exit_price"),
            "entry_reasoning": reasoning.get("entry_reasoning"),
            "exit_reasoning": reasoning.get("exit_reasoning"),
            "pnl": reasoning.get("pnl"),
            "confidence": reasoning.get("confidence"),
            "indicator_agreement": reasoning.get("indicator_agreement"),
            "technical_analysis": reasoning.get("technical_analysis"),
            "market_context": reasoning.get("market_context"),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching trade reasoning: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# SCHEDULER ROUTES
@router.get("/api/advanced/scheduler/status")
async def get_scheduler_status() -> Dict:
    """Get current scheduler status and jobs"""
    try:
        from app.services.orchestrator import get_orchestrator
        
        orchestrator = await get_orchestrator()
        status = orchestrator.get_scheduler_status()
        
        logger.info("Scheduler status retrieved")
        return status
    except Exception as e:
        logger.error(f"Error fetching scheduler status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/advanced/scheduler/market-status")
async def get_market_status() -> Dict:
    """Check if Indian market is open"""
    try:
        from app.services.orchestrator import get_orchestrator
        
        orchestrator = await get_orchestrator()
        is_open = orchestrator.is_market_open()
        
        logger.info("Market status checked")
        return {
            "market_open": is_open,
            "market_hours": "9:15 AM - 3:30 PM IST",
            "trading_days": "Monday - Friday",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error checking market status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# STATS & MONITORING ROUTES
@router.get("/api/advanced/stats/execution")
async def get_execution_stats() -> Dict:
    """Get trade execution statistics"""
    try:
        from app.services.orchestrator import get_executor
        from app.services.paper_trading_advanced import paper_trader as pt
        from app.services.ai_analysis_advanced import ai_engine as advanced_ai
        from app.services.explainable_ai import explainable_logger
        
        executor = await get_executor(pt, groww_client, advanced_ai, explainable_logger)
        stats = executor.get_execution_stats()
        
        logger.info("Execution stats retrieved")
        return {
            **stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching execution stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/advanced/health")
async def advanced_health_check() -> Dict:
    """Advanced health check for all AI trading services"""
    try:
        from app.services.orchestrator import get_orchestrator
        
        orchestrator = await get_orchestrator()
        
        return {
            "status": "operational",
            "services": {
                "groww_api": "connected",
                "claude_ai": "connected",
                "database": "connected",
                "paper_trading": "active",
                "ai_analysis": "active",
                "options_engine": "active",
                "mutual_fund_analyzer": "active",
                "report_generator": "active",
                "explainable_ai": "active"
            },
            "scheduler": {
                "running": orchestrator.is_running,
                "market_open": orchestrator.is_market_open()
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        raise HTTPException(status_code=500, detail=str(e))
