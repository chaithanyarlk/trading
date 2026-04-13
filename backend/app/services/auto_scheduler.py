"""
AUTO SCHEDULER — Runs the agent pipeline automatically during market hours.

- Runs every `scan_interval_minutes` during market hours (9:15 AM – 3:30 PM IST)
- Auto-executes BUY/SELL decisions as paper trades
- Generates EOD report at 3:30 PM IST
- Broadcasts all events via WebSocket to UI in real-time

Starts automatically when the user saves config from UI.
"""
import asyncio
import logging
from datetime import datetime, time as dtime
from typing import List, Dict, Optional, Callable, Awaitable

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.models.agent_schemas import (
    PaperTradingConfig, AnalyzeRequest, TradeAction, ChiefDecision
)
from app.services.agents.pipeline import agent_pipeline
from app.services.paper_trading_v2 import paper_engine
from app.services.ai_provider import ai_provider

logger = logging.getLogger(__name__)

IST = pytz.timezone("Asia/Kolkata")

# Market hours
MARKET_OPEN = dtime(9, 15)
MARKET_CLOSE = dtime(15, 30)


class AutoScheduler:
    """
    Background scheduler that:
      1. Scans symbols every N minutes during market hours
      2. Auto-executes paper trades
      3. Generates EOD report at 3:30 PM IST
      4. Pushes all results to WebSocket subscribers
    """

    def __init__(self):
        self._scheduler: Optional[AsyncIOScheduler] = None
        self._config: Optional[PaperTradingConfig] = None
        self._running = False
        self._scan_interval_minutes = 15   # default: every 15 min
        self._ws_broadcast: Optional[Callable] = None

        # Collected data for the day
        self._todays_decisions: List[ChiefDecision] = []
        self._todays_executions: List[Dict] = []
        self._eod_report: Optional[Dict] = None
        self._scan_count = 0

    @property
    def is_running(self) -> bool:
        return self._running

    def set_broadcast_fn(self, fn: Callable):
        """Set the WebSocket broadcast function (called from routes)."""
        self._ws_broadcast = fn

    async def _broadcast(self, event_type: str, data: dict):
        """Push event to all connected WebSocket clients."""
        if self._ws_broadcast:
            try:
                await self._ws_broadcast({"type": event_type, "data": data})
            except Exception as e:
                logger.error(f"[Scheduler] Broadcast error: {e}")

    # ──────────────────────────────────────────────────────────────
    # Start / Stop
    # ──────────────────────────────────────────────────────────────

    def start(self, config: PaperTradingConfig, scan_interval_minutes: int = 15):
        """
        Start the auto-scheduler. Called when user saves config from UI.
        """
        self._config = config
        self._scan_interval_minutes = scan_interval_minutes
        self._todays_decisions = []
        self._todays_executions = []
        self._eod_report = None
        self._scan_count = 0

        if self._scheduler:
            self.stop()

        self._scheduler = AsyncIOScheduler(timezone=IST)

        # Job 1: Periodic scan during market hours
        self._scheduler.add_job(
            self._run_scan,
            IntervalTrigger(minutes=scan_interval_minutes, timezone=IST),
            id="agent_scan",
            name=f"Agent Scan (every {scan_interval_minutes}min)",
            replace_existing=True,
        )

        # Job 2: EOD report at 3:35 PM IST (5 min after market close)
        self._scheduler.add_job(
            self._generate_eod_report,
            CronTrigger(hour=15, minute=35, timezone=IST),
            id="eod_report",
            name="EOD Report @ 3:35 PM IST",
            replace_existing=True,
        )

        self._scheduler.start()
        self._running = True

        logger.info(
            f"[Scheduler] Started — scanning {len(config.trading_symbols)} symbols "
            f"every {scan_interval_minutes}min during market hours"
        )

    def stop(self):
        """Stop the scheduler."""
        if self._scheduler:
            self._scheduler.shutdown(wait=False)
            self._scheduler = None
        self._running = False
        logger.info("[Scheduler] Stopped")

    # ──────────────────────────────────────────────────────────────
    # Periodic Scan Job
    # ──────────────────────────────────────────────────────────────

    async def _run_scan(self):
        """Run one full scan cycle. Called by APScheduler."""
        now = datetime.now(IST)

        # Only run during market hours (Mon-Fri, 9:15 AM - 3:30 PM)
        if now.weekday() >= 5:  # Sat/Sun
            logger.debug("[Scheduler] Weekend — skipping scan")
            return
        if now.time() < MARKET_OPEN or now.time() > MARKET_CLOSE:
            logger.debug("[Scheduler] Outside market hours — skipping scan")
            return

        if not self._config:
            logger.warning("[Scheduler] No config — skipping scan")
            return

        self._scan_count += 1
        logger.info(f"[Scheduler] ═══ SCAN #{self._scan_count} @ {now.strftime('%H:%M:%S')} ═══")

        try:
            # Ensure paper engine is configured
            if not paper_engine.is_configured:
                paper_engine.configure(self._config)

            # Update pipeline state
            agent_pipeline.set_portfolio_state(
                open_positions=paper_engine.get_open_position_count(),
                portfolio_value=paper_engine.get_portfolio_value()
            )

            # Run pipeline
            request = AnalyzeRequest(
                symbols=self._config.trading_symbols,
                config=self._config,
                auto_execute=True,
            )
            response = await agent_pipeline.run(request)

            # Auto-execute
            scan_executions = []
            for decision in response.decisions:
                self._todays_decisions.append(decision)

                if decision.action != TradeAction.HOLD:
                    result = paper_engine.execute_decision(decision)
                    scan_executions.append(result)
                    self._todays_executions.append(result)

            # Broadcast scan results to UI
            await self._broadcast("scan_complete", {
                "scan_number": self._scan_count,
                "time": now.strftime("%H:%M:%S"),
                "decisions": [d.model_dump() for d in response.decisions],
                "executions": scan_executions,
                "errors": response.errors,
                "portfolio_value": paper_engine.get_portfolio_value(),
                "summary": {
                    "buys": len([d for d in response.decisions if d.action == TradeAction.BUY]),
                    "sells": len([d for d in response.decisions if d.action == TradeAction.SELL]),
                    "holds": len([d for d in response.decisions if d.action == TradeAction.HOLD]),
                }
            })

            logger.info(
                f"[Scheduler] Scan #{self._scan_count} done — "
                f"{len(scan_executions)} trades executed"
            )

        except Exception as e:
            logger.error(f"[Scheduler] Scan error: {e}")
            await self._broadcast("scan_error", {"error": str(e), "scan_number": self._scan_count})

    # ────────────────────��─────────────────────────────────────────
    # EOD Report
    # ──────────────────────────────────────────────────────────────

    async def _generate_eod_report(self):
        """Generate end-of-day report at 3:35 PM IST."""
        now = datetime.now(IST)
        if now.weekday() >= 5:
            return

        logger.info("[Scheduler] ═══ GENERATING EOD REPORT ═══")

        try:
            overview = paper_engine.get_portfolio_overview() if paper_engine.is_configured else None
            perf = paper_engine.get_performance_metrics() if paper_engine.is_configured else None

            # Use AI to generate summary
            decisions_text = "\n".join([
                f"- {d.symbol}: {d.action.value} x{d.quantity} @ ₹{d.price} "
                f"(conf={d.confidence:.0%}, risk={d.risk_level.value})"
                for d in self._todays_decisions
            ]) or "No decisions today."

            executions_text = "\n".join([
                f"- {e.get('symbol', '?')}: {e.get('action', '?')} "
                f"x{e.get('quantity', 0)} @ ₹{e.get('execution_price', 0):.2f} "
                f"(PnL=₹{e.get('pnl', 'N/A')})"
                for e in self._todays_executions
            ]) or "No trades executed today."

            prompt = f"""Generate a professional end-of-day trading report for {now.strftime('%d %B %Y')}.

PORTFOLIO:
Total Value: ₹{overview.total_value:.2f if overview else 'N/A'}
Cash: ₹{overview.cash_balance:.2f if overview else 'N/A'}
Unrealized PnL: ₹{overview.unrealized_pnl:.2f if overview else 'N/A'}
Holdings: {len(overview.holdings) if overview else 0}

PERFORMANCE:
Total Trades: {perf.total_trades if perf else 0}
Win Rate: {perf.win_rate if perf else 0}%
Net Profit: ₹{perf.net_profit if perf else 0}
ROI: {perf.roi if perf else 0}%

TODAY'S DECISIONS ({len(self._todays_decisions)}):
{decisions_text}

TODAY'S EXECUTIONS ({len(self._todays_executions)}):
{executions_text}

SCANS COMPLETED: {self._scan_count}

Write a 5-8 sentence professional report covering:
1. Market summary for the day
2. Key trades and their reasoning
3. Portfolio performance
4. What went well / what to improve
5. Outlook for tomorrow"""

            ai_summary = ai_provider.analyze(
                prompt,
                system_prompt="You are a professional trading desk report writer.",
                max_tokens=600,
            )

            self._eod_report = {
                "date": now.strftime("%Y-%m-%d"),
                "generated_at": now.strftime("%H:%M:%S IST"),
                "portfolio": overview.model_dump() if overview else None,
                "performance": perf.model_dump() if perf else None,
                "total_scans": self._scan_count,
                "total_decisions": len(self._todays_decisions),
                "total_executions": len(self._todays_executions),
                "decisions_summary": [
                    {
                        "symbol": d.symbol,
                        "action": d.action.value,
                        "quantity": d.quantity,
                        "price": d.price,
                        "confidence": d.confidence,
                        "risk_level": d.risk_level.value,
                        "reasoning": d.chief_reasoning[:200],
                    }
                    for d in self._todays_decisions
                ],
                "executions": self._todays_executions,
                "ai_summary": ai_summary,
            }

            # Broadcast report to UI
            await self._broadcast("eod_report", self._eod_report)

            logger.info("[Scheduler] ✓ EOD Report generated and broadcast")

        except Exception as e:
            logger.error(f"[Scheduler] EOD Report error: {e}")
            self._eod_report = {"error": str(e), "date": now.strftime("%Y-%m-%d")}
            await self._broadcast("eod_report", self._eod_report)

    def get_eod_report(self) -> Optional[Dict]:
        """Return the latest EOD report."""
        return self._eod_report

    def get_status(self) -> Dict:
        """Return scheduler status."""
        now = datetime.now(IST)
        is_market_hours = (
            now.weekday() < 5
            and MARKET_OPEN <= now.time() <= MARKET_CLOSE
        )
        return {
            "running": self._running,
            "market_open": is_market_hours,
            "scan_interval_minutes": self._scan_interval_minutes,
            "scans_completed": self._scan_count,
            "decisions_today": len(self._todays_decisions),
            "executions_today": len(self._todays_executions),
            "has_eod_report": self._eod_report is not None,
            "symbols": self._config.trading_symbols if self._config else [],
            "current_time_ist": now.strftime("%H:%M:%S"),
            "next_market_open": "09:15 IST",
            "market_close": "15:30 IST",
            "eod_report_time": "15:35 IST",
        }

    def get_todays_decisions(self) -> List[Dict]:
        """Return all of today's decisions."""
        return [d.model_dump() for d in self._todays_decisions]

    def get_todays_executions(self) -> List[Dict]:
        """Return all of today's executions."""
        return self._todays_executions


# Module-level singleton
auto_scheduler = AutoScheduler()

