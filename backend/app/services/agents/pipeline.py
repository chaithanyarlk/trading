"""
AGENT PIPELINE — Orchestrates the multi-agent trading system.

Flow:
  1. DataFetcherAgent → fetches market data + news for each symbol
  2. AlgoAgent → runs technical analysis on market data
  3. SentimentAgent → runs sentiment analysis on news data
  4. ChiefTradingAgent → combines both, applies risk mgmt, makes final decision
  5. (Optional) Auto-execute paper trades

This is the ONLY entry point the API routes call.
"""
import logging
from typing import List, Optional
from datetime import datetime

from app.models.agent_schemas import (
    PaperTradingConfig, ChiefDecision, AnalyzeRequest, AnalyzeResponse, TradeAction
)
from app.services.agents.data_fetcher_agent import DataFetcherAgent
from app.services.agents.algo_agent import AlgoAgent
from app.services.agents.sentiment_agent import SentimentAgent
from app.services.agents.chief_agent import ChiefTradingAgent

logger = logging.getLogger(__name__)


class AgentPipeline:
    """
    Orchestrates the full multi-agent decision pipeline.

    Usage:
        pipeline = AgentPipeline()
        response = await pipeline.run(AnalyzeRequest(
            symbols=["RELIANCE", "TCS"],
            config=PaperTradingConfig(initial_capital=500000, ...),
            auto_execute=False
        ))
    """

    def __init__(self):
        self.data_fetcher = DataFetcherAgent()
        self.algo_agent = AlgoAgent()
        self.sentiment_agent = SentimentAgent()
        self.chief_agent = ChiefTradingAgent()

        # Track state for risk management
        self._open_positions: int = 0
        self._portfolio_value: float = 0
        self._decisions_history: List[ChiefDecision] = []

    def set_portfolio_state(self, open_positions: int, portfolio_value: float):
        """Update the pipeline with current portfolio state (called by paper trader)."""
        self._open_positions = open_positions
        self._portfolio_value = portfolio_value

    async def run(self, request: AnalyzeRequest) -> AnalyzeResponse:
        """
        Run the full multi-agent pipeline for all requested symbols.
        """
        config = request.config
        symbols = request.symbols
        decisions: List[ChiefDecision] = []
        errors: List[str] = []

        if self._portfolio_value <= 0:
            self._portfolio_value = config.initial_capital

        logger.info(
            f"[Pipeline] Starting analysis for {len(symbols)} symbols: {symbols}"
        )

        for symbol in symbols:
            try:
                decision = await self._analyze_single(symbol, config)
                decisions.append(decision)
            except Exception as e:
                error_msg = f"Pipeline error for {symbol}: {str(e)}"
                logger.error(f"[Pipeline] {error_msg}")
                errors.append(error_msg)

        # Store history
        self._decisions_history.extend(decisions)

        # Summary log
        actions = {d.symbol: f"{d.action.value} x{d.quantity}" for d in decisions if d.action != TradeAction.HOLD}
        holds = [d.symbol for d in decisions if d.action == TradeAction.HOLD]
        logger.info(f"[Pipeline] Actions: {actions}")
        if holds:
            logger.info(f"[Pipeline] Holds: {holds}")

        return AnalyzeResponse(
            decisions=decisions,
            errors=errors,
            timestamp=datetime.now()
        )

    async def _analyze_single(
        self, symbol: str, config: PaperTradingConfig
    ) -> ChiefDecision:
        """Run the full agent chain for a single symbol."""

        logger.info(f"[Pipeline] ── {symbol} ──────────────────────────")

        # ── Step 1: DataFetcherAgent ──────────────────────────────
        logger.info(f"[Pipeline] Step 1/4: DataFetcher for {symbol}")
        market_data = await self.data_fetcher.fetch_market_data(symbol)
        news_data = await self.data_fetcher.fetch_news_sentiment(symbol)

        # ── Step 2: AlgoAgent ─────────────────────────────────────
        logger.info(f"[Pipeline] Step 2/4: AlgoAgent for {symbol}")
        algo_verdict = await self.algo_agent.analyze(market_data)

        # ── Step 3: SentimentAgent ────────────────────────────────
        logger.info(f"[Pipeline] Step 3/4: SentimentAgent for {symbol}")
        sentiment_verdict = await self.sentiment_agent.analyze(news_data, market_data)

        # ── Step 4: ChiefAgent ────────────────────────────────────
        logger.info(f"[Pipeline] Step 4/4: ChiefAgent for {symbol}")
        decision = await self.chief_agent.decide(
            symbol=symbol,
            market=market_data,
            algo_verdict=algo_verdict,
            sentiment_verdict=sentiment_verdict,
            config=config,
            current_positions=self._open_positions,
            portfolio_value=self._portfolio_value,
        )

        return decision

    async def analyze_single_symbol(
        self, symbol: str, config: PaperTradingConfig
    ) -> ChiefDecision:
        """Public method to analyze a single symbol."""
        if self._portfolio_value <= 0:
            self._portfolio_value = config.initial_capital
        return await self._analyze_single(symbol, config)

    def get_history(self) -> List[ChiefDecision]:
        """Get all past decisions."""
        return self._decisions_history

    def clear_history(self):
        """Clear decision history."""
        self._decisions_history.clear()


# Module-level singleton
agent_pipeline = AgentPipeline()

