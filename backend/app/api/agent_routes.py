"""
Agent Routes — New API endpoints for the multi-agent trading system.

These routes replace the old hardcoded ones.
Paper trading config comes from UI. Multi-agent pipeline makes decisions.
"""
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from typing import Dict, List
from datetime import datetime
import logging
import json
import asyncio

from app.models.agent_schemas import (
    PaperTradingConfig, AnalyzeRequest, AnalyzeResponse,
    ChiefDecision, TradeAction
)
from app.services.agents.pipeline import agent_pipeline
from app.services.paper_trading_v2 import paper_engine
from app.services.groww_data_interface import groww_data
from app.services.auto_scheduler import auto_scheduler

logger = logging.getLogger(__name__)

agent_router = APIRouter(prefix="/api/agents", tags=["Multi-Agent System"])

# ── WebSocket client management ──────────────────────────────────
_ws_clients: List[WebSocket] = []


async def _broadcast_to_clients(message: dict):
    """Send a message to all connected WebSocket clients."""
    dead = []
    for ws in _ws_clients:
        try:
            await ws.send_json(message)
        except Exception:
            dead.append(ws)
    for ws in dead:
        _ws_clients.remove(ws)


# Wire broadcast into the auto-scheduler so it can push events
auto_scheduler.set_broadcast_fn(_broadcast_to_clients)


@agent_router.websocket("/ws")
async def agent_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time updates.
    Clients receive:
      - scan_complete: after each auto-scan
      - scan_error: if a scan fails
      - eod_report: end-of-day report at 3:35 PM IST
    """
    await websocket.accept()
    _ws_clients.append(websocket)
    logger.info(f"[WS] Client connected ({len(_ws_clients)} total)")
    try:
        while True:
            # Keep connection alive; optionally handle incoming messages
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.debug(f"[WS] Connection closed: {e}")
    finally:
        if websocket in _ws_clients:
            _ws_clients.remove(websocket)
        logger.info(f"[WS] Client disconnected ({len(_ws_clients)} total)")


# ═══════════════════════════════════════════════════════════════════════
#  PAPER TRADING CONFIG — FROM UI
# ═══════════════════════════════════════════════════════════════════════

@agent_router.post("/config")
async def configure_paper_trading(config: PaperTradingConfig) -> Dict:
    """
    Configure paper trading from the UI.
    This also starts the auto-scheduler that scans every 15 min during market hours.
    """
    try:
        result = paper_engine.configure(config)
        # Update pipeline with portfolio state
        agent_pipeline.set_portfolio_state(
            open_positions=paper_engine.get_open_position_count(),
            portfolio_value=paper_engine.get_portfolio_value()
        )
        # Auto-start scheduler
        auto_scheduler.start(config, scan_interval_minutes=15)
        logger.info(f"Paper trading configured + scheduler started: ₹{config.initial_capital}")
        return {**result, "scheduler_started": True, "scan_interval_minutes": 15}
    except Exception as e:
        logger.error(f"Error configuring paper trading: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@agent_router.get("/config")
async def get_paper_trading_config() -> Dict:
    """Get current paper trading configuration."""
    config = paper_engine.get_config()
    if not config:
        return {"configured": False, "message": "Send config from UI first via POST /api/agents/config"}
    return {"configured": True, "config": config.model_dump()}


# ═══════════════════════════════════════════════════════════════════════
#  MULTI-AGENT ANALYSIS PIPELINE
# ═══════════════════════════════════════════════════════════════════════

@agent_router.post("/analyze")
async def run_agent_pipeline(request: AnalyzeRequest) -> Dict:
    """
    Run the full multi-agent pipeline:
      1. DataFetcherAgent → fetches market data + news
      2. AlgoAgent → technical analysis
      3. SentimentAgent → news/sentiment analysis
      4. ChiefAgent → final decision with reasoning

    If auto_execute=True, paper trades are executed automatically.
    """
    try:
        # Ensure paper trading is configured
        if not paper_engine.is_configured:
            paper_engine.configure(request.config)

        # Update pipeline state
        agent_pipeline.set_portfolio_state(
            open_positions=paper_engine.get_open_position_count(),
            portfolio_value=paper_engine.get_portfolio_value()
        )

        # Run the pipeline
        response: AnalyzeResponse = await agent_pipeline.run(request)

        # Auto-execute if requested
        execution_results = []
        if request.auto_execute:
            for decision in response.decisions:
                if decision.action != TradeAction.HOLD:
                    result = paper_engine.execute_decision(decision)
                    execution_results.append(result)

        return {
            "decisions": [d.model_dump() for d in response.decisions],
            "execution_results": execution_results if request.auto_execute else [],
            "errors": response.errors,
            "timestamp": response.timestamp.isoformat(),
            "summary": {
                "total_symbols": len(request.symbols),
                "buy_signals": len([d for d in response.decisions if d.action == TradeAction.BUY]),
                "sell_signals": len([d for d in response.decisions if d.action == TradeAction.SELL]),
                "hold_signals": len([d for d in response.decisions if d.action == TradeAction.HOLD]),
            }
        }
    except Exception as e:
        logger.error(f"Error in agent pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@agent_router.post("/analyze/{symbol}")
async def analyze_single_symbol(symbol: str, config: PaperTradingConfig) -> Dict:
    """
    Run multi-agent analysis on a single symbol.
    Returns the full ChiefDecision with reasoning chain from all agents.
    """
    try:
        if not paper_engine.is_configured:
            paper_engine.configure(config)

        agent_pipeline.set_portfolio_state(
            open_positions=paper_engine.get_open_position_count(),
            portfolio_value=paper_engine.get_portfolio_value()
        )

        decision = await agent_pipeline.analyze_single_symbol(symbol, config)
        return decision.model_dump()
    except Exception as e:
        logger.error(f"Error analyzing {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════
#  TRADE EXECUTION
# ═══════════════════════════════════════════════════════════════════════

@agent_router.post("/execute")
async def execute_decision(decision: ChiefDecision) -> Dict:
    """
    Execute a ChiefDecision as a paper trade.
    Usually called after /analyze returns decisions.
    """
    try:
        if not paper_engine.is_configured:
            raise HTTPException(
                status_code=400,
                detail="Paper trading not configured. POST to /api/agents/config first."
            )
        result = paper_engine.execute_decision(decision)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing decision: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═════��═════════════════════════════════════════════════════════════════
#  PORTFOLIO & PERFORMANCE
# ═══════════════════════════════════════════════════════════════════════

@agent_router.get("/portfolio")
async def get_portfolio() -> Dict:
    """Get current paper trading portfolio."""
    if not paper_engine.is_configured:
        return {"configured": False, "message": "Paper trading not configured"}
    overview = paper_engine.get_portfolio_overview()
    return overview.model_dump()


@agent_router.get("/performance")
async def get_performance() -> Dict:
    """Get paper trading performance metrics."""
    if not paper_engine.is_configured:
        return {"configured": False, "message": "Paper trading not configured"}
    metrics = paper_engine.get_performance_metrics()
    return metrics.model_dump()


@agent_router.get("/trades")
async def get_trades() -> List[Dict]:
    """Get all paper trades with full agent reasoning."""
    return [t.model_dump() for t in paper_engine.trades]


@agent_router.get("/decisions/history")
async def get_decision_history() -> List[Dict]:
    """Get all agent decisions (including HOLDs)."""
    return [d.model_dump() for d in agent_pipeline.get_history()]


# ═══════════════════════════════════════════════════════════════════════
#  MARKET DATA (pass-through to Groww)
# ═══════════════════════════════════════════════════════════════════════

@agent_router.get("/market/quote/{symbol}")
async def get_quote(symbol: str, exchange: str = "NSE") -> Dict:
    """Get market quote for a symbol (via Groww API)."""
    quote = await groww_data.get_stock_quote(symbol, exchange)
    if not quote:
        raise HTTPException(status_code=404, detail=f"Quote for {symbol} not available (Groww offline?)")
    return quote


@agent_router.get("/market/ltp/{symbol}")
async def get_ltp(symbol: str, exchange: str = "NSE") -> Dict:
    """Get LTP for a symbol."""
    ltp = await groww_data.get_ltp(symbol, exchange)
    if ltp is None:
        raise HTTPException(status_code=404, detail=f"LTP for {symbol} not available")
    return {"symbol": symbol, "ltp": ltp}


@agent_router.get("/market/historical/{symbol}")
async def get_historical(
    symbol: str, interval: str = "1day", days: int = 365, exchange: str = "NSE"
) -> List[Dict]:
    """Get historical candles for a symbol."""
    data = await groww_data.get_historical_candles(symbol, interval, days, exchange)
    if not data:
        raise HTTPException(status_code=404, detail=f"Historical data for {symbol} not available")
    return data


# ═══════════════════════════════════════════════════════════════════════
#  INSTRUMENTS — fetch all, classify stocks / options / futures
# ═══════════════════════════════════════════════════════════════════════

@agent_router.get("/instruments/all")
async def get_all_instruments() -> Dict:
    """
    Fetch the full Groww instrument master and classify into
    stocks, options, futures with counts.
    """
    try:
        counts = await groww_data.get_instrument_counts()
        return {
            "counts": counts,
            "message": "Use /instruments/stocks, /instruments/options, /instruments/futures for filtered lists",
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error fetching instruments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@agent_router.get("/instruments/stocks")
async def get_stock_instruments(
    search: str = "",
    exchange: str = "",
    limit: int = 100,
) -> List[Dict]:
    """
    Get equity stock instruments (no options, no futures).
    Optional: filter by search term or exchange.
    """
    try:
        stocks = await groww_data.get_equity_stocks()
        if exchange:
            stocks = [s for s in stocks if s.get("exchange", "").upper() == exchange.upper()]
        if search:
            search_upper = search.upper()
            stocks = [
                s for s in stocks
                if search_upper in (s.get("trading_symbol", "") or "").upper()
            ]
        return stocks[:limit]
    except Exception as e:
        logger.error(f"Error fetching stock instruments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@agent_router.get("/instruments/options")
async def get_option_instruments(
    underlying: str = "",
    limit: int = 100,
) -> List[Dict]:
    """Get option instruments (CE/PE). Optional: filter by underlying."""
    try:
        options = await groww_data.get_option_instruments()
        if underlying:
            underlying_upper = underlying.upper()
            options = [
                o for o in options
                if underlying_upper in (o.get("trading_symbol", "") or "").upper()
            ]
        return options[:limit]
    except Exception as e:
        logger.error(f"Error fetching option instruments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@agent_router.get("/instruments/futures")
async def get_future_instruments(limit: int = 100) -> List[Dict]:
    """Get futures instruments."""
    try:
        futures = await groww_data.get_future_instruments()
        return futures[:limit]
    except Exception as e:
        logger.error(f"Error fetching futures instruments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════
#  REAL GROWW PORTFOLIO — holdings + positions from your account
# ═══════════════════════════════════════════════════════════════════════

@agent_router.get("/groww-portfolio/holdings")
async def get_groww_holdings() -> Dict:
    """
    Get your real Groww delivery holdings (CNC positions).
    Shows what you actually own in your Groww demat account.
    """
    try:
        holdings = await groww_data.get_holdings()
        if holdings is None:
            return {"online": False, "message": "Groww API offline — no real portfolio data"}
        return {"online": True, "holdings": holdings}
    except Exception as e:
        logger.error(f"Error fetching Groww holdings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@agent_router.get("/groww-portfolio/positions")
async def get_groww_positions(segment: str = "") -> Dict:
    """
    Get your real Groww intraday/F&O open positions.
    """
    try:
        positions = await groww_data.get_positions(segment if segment else None)
        if positions is None:
            return {"online": False, "message": "Groww API offline — no position data"}
        return {"online": True, "positions": positions}
    except Exception as e:
        logger.error(f"Error fetching Groww positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@agent_router.get("/groww-portfolio/margin")
async def get_groww_margin() -> Dict:
    """Get available margin/buying power from your Groww account."""
    try:
        margin = await groww_data.get_available_margin()
        if margin is None:
            return {"online": False, "message": "Groww API offline"}
        return {"online": True, "margin": margin}
    except Exception as e:
        logger.error(f"Error fetching margin: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@agent_router.get("/groww-portfolio/orders")
async def get_groww_orders(page: int = 0, page_size: int = 25) -> Dict:
    """Get your Groww order book."""
    try:
        orders = await groww_data.get_order_list(page=page, page_size=page_size)
        if orders is None:
            return {"online": False, "message": "Groww API offline"}
        return {"online": True, "orders": orders}
    except Exception as e:
        logger.error(f"Error fetching orders: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════
#  POTENTIAL BUY STOCKS — with support, stop loss, exit price
# ═══════════════════════════════════════════════════════════════════════

@agent_router.post("/potential-buys")
async def get_potential_buys(config: PaperTradingConfig) -> Dict:
    """
    Run the full agent pipeline on configured symbols and return
    only BUY signals with support, stop loss, take profit, exit price.

    Each stock includes:
      - Current price, support, resistance
      - Stop loss, take profit / exit price
      - Agent reasoning chain
      - Confidence, risk level
    """
    try:
        from app.services.agents.pipeline import agent_pipeline
        from app.models.agent_schemas import AnalyzeRequest, TradeAction

        if not paper_engine.is_configured:
            paper_engine.configure(config)

        agent_pipeline.set_portfolio_state(
            open_positions=paper_engine.get_open_position_count(),
            portfolio_value=paper_engine.get_portfolio_value()
        )

        request = AnalyzeRequest(
            symbols=config.trading_symbols,
            config=config,
            auto_execute=False,
        )
        response = await agent_pipeline.run(request)

        potential_buys = []
        for d in response.decisions:
            if d.action == TradeAction.BUY:
                # Get support/resistance from algo verdict
                support = None
                resistance = None
                trend = "NEUTRAL"
                indicators_summary = []

                if d.algo_verdict:
                    support = d.algo_verdict.support_price
                    resistance = d.algo_verdict.resistance_price
                    trend = d.algo_verdict.trend
                    indicators_summary = [
                        {"name": ind.name, "signal": ind.signal, "value": round(ind.value, 2), "explanation": ind.explanation}
                        for ind in d.algo_verdict.indicators
                    ]

                potential_buys.append({
                    "symbol": d.symbol,
                    "current_price": d.price,
                    "action": d.action.value,
                    "confidence": round(d.confidence * 100, 1),
                    "risk_level": d.risk_level.value,
                    "quantity": d.quantity,
                    "position_size_percent": d.position_size_percent,
                    # Key levels
                    "support_price": round(support, 2) if support else None,
                    "resistance_price": round(resistance, 2) if resistance else None,
                    "stop_loss": round(d.stop_loss, 2) if d.stop_loss else None,
                    "take_profit": round(d.take_profit, 2) if d.take_profit else None,
                    "exit_price": round(d.take_profit, 2) if d.take_profit else None,  # exit = take profit
                    "trend": trend,
                    # Reasoning
                    "chief_reasoning": d.chief_reasoning,
                    "indicators": indicators_summary,
                    "sentiment_score": d.sentiment_verdict.sentiment_score if d.sentiment_verdict else None,
                    "dissenting_opinions": d.dissenting_opinions,
                    "trade_id": d.trade_id,
                })

        return {
            "total_analyzed": len(response.decisions),
            "potential_buys": potential_buys,
            "holds": [
                {"symbol": d.symbol, "reason": d.chief_reasoning}
                for d in response.decisions if d.action == TradeAction.HOLD
            ],
            "sells": [
                {"symbol": d.symbol, "reason": d.chief_reasoning, "price": d.price}
                for d in response.decisions if d.action == TradeAction.SELL
            ],
            "errors": response.errors,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error getting potential buys: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════
#  AUTO SCHEDULER
# ═══════════════════════════════════════════════════════════════════════

@agent_router.get("/scheduler/status")
async def get_scheduler_status() -> Dict:
    """Get auto-scheduler status (running, scans done, next scan, etc.)."""
    return auto_scheduler.get_status()


@agent_router.post("/scheduler/start")
async def start_scheduler(scan_interval_minutes: int = 15) -> Dict:
    """Manually start the scheduler (normally auto-starts on config save)."""
    config = paper_engine.get_config()
    if not config:
        raise HTTPException(status_code=400, detail="Configure paper trading first")
    auto_scheduler.start(config, scan_interval_minutes)
    return {"started": True, "interval": scan_interval_minutes}


@agent_router.post("/scheduler/stop")
async def stop_scheduler() -> Dict:
    """Stop the auto-scheduler."""
    auto_scheduler.stop()
    return {"stopped": True}


@agent_router.post("/scheduler/scan-now")
async def trigger_scan_now() -> Dict:
    """Trigger an immediate scan (ignores market hours check)."""
    if not paper_engine.is_configured:
        raise HTTPException(status_code=400, detail="Configure paper trading first")
    config = paper_engine.get_config()
    agent_pipeline.set_portfolio_state(
        open_positions=paper_engine.get_open_position_count(),
        portfolio_value=paper_engine.get_portfolio_value()
    )
    request = AnalyzeRequest(
        symbols=config.trading_symbols,
        config=config,
        auto_execute=True,
    )
    response = await agent_pipeline.run(request)
    executions = []
    for d in response.decisions:
        if d.action != TradeAction.HOLD:
            result = paper_engine.execute_decision(d)
            executions.append(result)
    # Broadcast
    await _broadcast_to_clients({
        "type": "scan_complete",
        "data": {
            "scan_number": "manual",
            "time": datetime.now().strftime("%H:%M:%S"),
            "decisions": [d.model_dump() for d in response.decisions],
            "executions": executions,
            "errors": response.errors,
            "portfolio_value": paper_engine.get_portfolio_value(),
        }
    })
    return {
        "decisions": [d.model_dump() for d in response.decisions],
        "executions": executions,
        "errors": response.errors,
    }


# ═══════════════════════════════════════════════════════════════════════
#  TODAY'S ACTIVITY + EOD REPORT
# ═══════════════════════════════════════════════════════════════════════

@agent_router.get("/today/decisions")
async def get_todays_decisions() -> List[Dict]:
    """Get all decisions made today by the auto-scheduler."""
    return auto_scheduler.get_todays_decisions()


@agent_router.get("/today/executions")
async def get_todays_executions() -> List[Dict]:
    """Get all trades executed today by the auto-scheduler."""
    return auto_scheduler.get_todays_executions()


@agent_router.get("/report/eod")
async def get_eod_report() -> Dict:
    """
    Get the end-of-day report.
    Auto-generated at 3:35 PM IST. Can also be triggered manually.
    """
    report = auto_scheduler.get_eod_report()
    if not report:
        return {
            "available": False,
            "message": "EOD report not yet generated. Auto-generates at 3:35 PM IST.",
        }
    return {"available": True, "report": report}


@agent_router.post("/report/generate-now")
async def generate_eod_report_now() -> Dict:
    """Manually generate the EOD report (don't wait until 3:35 PM)."""
    if not paper_engine.is_configured:
        raise HTTPException(status_code=400, detail="Configure paper trading first")
    await auto_scheduler._generate_eod_report()
    report = auto_scheduler.get_eod_report()
    return {"available": True, "report": report}


# ═══════════════════════════════════════════════════════════════════════
#  LIVE FEED — subscribe / poll / unsubscribe real-time LTP
# ═══════════════════════════════════════════════════════════════════════

@agent_router.post("/live-feed/subscribe")
async def subscribe_live_feed(instruments: List[Dict]) -> Dict:
    """
    Subscribe to live LTP for instruments.

    Body: list of dicts e.g.
    [{"exchange": "NSE", "segment": "CASH", "exchange_token": "2885"}]
    """
    try:
        await groww_data.subscribe_live_ltp(instruments)
        await groww_data.start_live_feed()
        return {"subscribed": True, "instruments": len(instruments)}
    except Exception as e:
        logger.error(f"Error subscribing to live feed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@agent_router.get("/live-feed/ltp")
async def get_live_ltp() -> Dict:
    """Poll the latest live LTP data."""
    try:
        data = await groww_data.get_live_ltp()
        if data is None:
            return {"online": False, "message": "Live feed not active"}
        return {"online": True, "data": data}
    except Exception as e:
        logger.error(f"Error fetching live LTP: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@agent_router.post("/live-feed/unsubscribe")
async def unsubscribe_live_feed(instruments: List[Dict]) -> Dict:
    """Unsubscribe from live LTP for instruments."""
    try:
        await groww_data.unsubscribe_live_ltp(instruments)
        return {"unsubscribed": True, "instruments": len(instruments)}
    except Exception as e:
        logger.error(f"Error unsubscribing from live feed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@agent_router.post("/live-feed/stop")
async def stop_live_feed() -> Dict:
    """Stop the live feed entirely."""
    try:
        await groww_data.stop_live_feed()
        return {"stopped": True}
    except Exception as e:
        logger.error(f"Error stopping live feed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════
#  LIVE INDEX VALUES — subscribe / poll / unsubscribe real-time indices
# ═══════════════════════════════════════════════════════════════════════

@agent_router.post("/live-feed/index/subscribe")
async def subscribe_index_feed(instruments: List[Dict]) -> Dict:
    """
    Subscribe to live index values.

    Body: list of dicts e.g.
    [{"exchange": "NSE", "segment": "CASH", "exchange_token": "NIFTY"},
     {"exchange": "BSE", "segment": "CASH", "exchange_token": "1"}]
    """
    try:
        await groww_data.subscribe_live_index_value(instruments)
        await groww_data.start_live_feed()
        return {"subscribed": True, "indices": len(instruments)}
    except Exception as e:
        logger.error(f"Error subscribing to index feed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@agent_router.get("/live-feed/index/value")
async def get_live_index_value() -> Dict:
    """
    Poll the latest live index values.

    Returns e.g.
    {"NSE": {"CASH": {"NIFTY": {"tsInMillis": ..., "value": 24386.7}}}}
    """
    try:
        data = await groww_data.get_live_index_value()
        if data is None:
            return {"online": False, "message": "Index feed not active"}
        return {"online": True, "data": data}
    except Exception as e:
        logger.error(f"Error fetching live index value: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@agent_router.post("/live-feed/index/unsubscribe")
async def unsubscribe_index_feed(instruments: List[Dict]) -> Dict:
    """Unsubscribe from live index values."""
    try:
        await groww_data.unsubscribe_live_index_value(instruments)
        return {"unsubscribed": True, "indices": len(instruments)}
    except Exception as e:
        logger.error(f"Error unsubscribing from index feed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════
#  FNO ORDER UPDATES — subscribe / poll / unsubscribe derivative orders
# ═══════════════════════════════════════════════════════════════════════

@agent_router.post("/live-feed/fno-orders/subscribe")
async def subscribe_fno_order_updates() -> Dict:
    """
    Subscribe to derivative (FNO) order updates.
    Receive real-time updates when FNO orders are placed/executed/cancelled.
    """
    try:
        await groww_data.subscribe_fno_order_updates()
        await groww_data.start_live_feed()
        return {"subscribed": True}
    except Exception as e:
        logger.error(f"Error subscribing to FNO order updates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@agent_router.get("/live-feed/fno-orders/update")
async def get_fno_order_update() -> Dict:
    """
    Poll the latest FNO order update.

    Returns e.g.
    {"qty": 75, "price": "130", "filledQty": 75, "avgFillPrice": "110",
     "growwOrderId": "...", "orderStatus": "EXECUTED", "segment": "FNO", ...}
    """
    try:
        data = await groww_data.get_fno_order_update()
        if data is None:
            return {"online": False, "message": "FNO order updates not active"}
        return {"online": True, "data": data}
    except Exception as e:
        logger.error(f"Error fetching FNO order update: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@agent_router.post("/live-feed/fno-orders/unsubscribe")
async def unsubscribe_fno_order_updates() -> Dict:
    """Unsubscribe from FNO order updates."""
    try:
        await groww_data.unsubscribe_fno_order_updates()
        return {"unsubscribed": True}
    except Exception as e:
        logger.error(f"Error unsubscribing from FNO order updates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════
#  EQUITY ORDER UPDATES — subscribe / poll / unsubscribe equity orders
# ═══════════════════════════════════════════════════════════════════════

@agent_router.post("/live-feed/equity-orders/subscribe")
async def subscribe_equity_order_updates() -> Dict:
    """
    Subscribe to equity (CASH segment) order updates.
    Receive real-time updates when equity orders are placed/executed/cancelled.
    """
    try:
        await groww_data.subscribe_equity_order_updates()
        await groww_data.start_live_feed()
        return {"subscribed": True}
    except Exception as e:
        logger.error(f"Error subscribing to equity order updates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@agent_router.get("/live-feed/equity-orders/update")
async def get_equity_order_update() -> Dict:
    """
    Poll the latest equity order update.

    Returns e.g.
    {"qty": 3, "filledQty": 3, "avgFillPrice": "145",
     "growwOrderId": "...", "orderStatus": "EXECUTED", "exchange": "NSE", ...}
    """
    try:
        data = await groww_data.get_equity_order_update()
        if data is None:
            return {"online": False, "message": "Equity order updates not active"}
        return {"online": True, "data": data}
    except Exception as e:
        logger.error(f"Error fetching equity order update: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@agent_router.post("/live-feed/equity-orders/unsubscribe")
async def unsubscribe_equity_order_updates() -> Dict:
    """Unsubscribe from equity order updates."""
    try:
        await groww_data.unsubscribe_equity_order_updates()
        return {"unsubscribed": True}
    except Exception as e:
        logger.error(f"Error unsubscribing from equity order updates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


