"""
Agent 1: DATA FETCHER AGENT
─────────────────────────────
Low-level grunt. Fetches raw data from Groww API and returns clean snapshots.
No opinions, no decisions — just data.

Responsibilities:
  - Stock quotes & LTP
  - Historical OHLCV candles
  - News headlines (via AI generation since Groww doesn't have news API)
"""
import logging
from typing import List, Optional
from datetime import datetime

from app.models.agent_schemas import MarketDataSnapshot, NewsDataSnapshot
from app.services.groww_data_interface import groww_data
from app.services.ai_provider import ai_provider

logger = logging.getLogger(__name__)


class DataFetcherAgent:
    """
    Level 1 Agent — fetches raw market data and news.
    Feeds data upward to AlgoAgent and SentimentAgent.
    """

    ROLE = "DATA_FETCHER"

    async def fetch_market_data(self, symbol: str) -> MarketDataSnapshot:
        """
        Fetch full market snapshot for a symbol.
        Calls Groww API for quote + historical candles.
        """
        logger.info(f"[DataFetcher] Fetching market data for {symbol}")

        snapshot = MarketDataSnapshot(symbol=symbol)

        # 1. Get live quote
        quote = await groww_data.get_stock_quote(symbol)
        if quote:
            snapshot.ltp = quote.get("ltp") or quote.get("last_price") or quote.get("price")
            snapshot.open = quote.get("open")
            snapshot.high = quote.get("high")
            snapshot.low = quote.get("low")
            snapshot.prev_close = quote.get("close") or quote.get("prev_close")
            snapshot.volume = quote.get("volume")
            if snapshot.ltp and snapshot.prev_close and snapshot.prev_close > 0:
                snapshot.change_percent = (
                    (snapshot.ltp - snapshot.prev_close) / snapshot.prev_close * 100
                )
            snapshot.raw_quote = quote
            logger.info(f"[DataFetcher] {symbol} LTP=₹{snapshot.ltp}")
        else:
            logger.warning(f"[DataFetcher] No quote for {symbol} — Groww offline?")

        # 2. Get historical candles (1 year daily)
        candles = await groww_data.get_historical_candles(symbol, interval="1day", days=365)
        if candles:
            snapshot.historical_prices = [c.get("close", 0) for c in candles if c.get("close")]
            snapshot.historical_volumes = [c.get("volume", 0) for c in candles if c.get("volume")]
            logger.info(f"[DataFetcher] {symbol}: {len(snapshot.historical_prices)} days of history")
        else:
            logger.warning(f"[DataFetcher] No historical data for {symbol}")

        snapshot.timestamp = datetime.now()
        return snapshot

    async def fetch_news_sentiment(self, symbol: str) -> NewsDataSnapshot:
        """
        Fetch news/sentiment for a symbol.
        Uses AI to generate a sentiment assessment since Groww doesn't have a news API.
        """
        logger.info(f"[DataFetcher] Fetching news sentiment for {symbol}")

        news = NewsDataSnapshot(symbol=symbol)

        try:
            prompt = f"""You are a financial news analyst. For the Indian stock "{symbol}" on NSE:

1. List 3-5 recent key headlines or events that could affect this stock (make them realistic based on what you know about this company).
2. Rate overall sentiment from -1.0 (very bearish) to +1.0 (very bullish).
3. List any risk events.
4. Rate the sector sentiment.

Respond in this EXACT format:
HEADLINES:
- headline 1
- headline 2
- headline 3
SENTIMENT_SCORE: 0.3
KEY_EVENTS:
- event 1
RISK_EVENTS:
- risk 1
SECTOR_SENTIMENT: NEUTRAL"""

            response = ai_provider.analyze(
                prompt,
                system_prompt="You are a financial news analyst for Indian markets.",
                max_tokens=500
            )

            news = self._parse_news_response(symbol, response)
        except Exception as e:
            logger.error(f"[DataFetcher] News sentiment error for {symbol}: {e}")
            news.sentiment_score = 0.0
            news.headlines = ["Unable to fetch news data"]

        news.timestamp = datetime.now()
        return news

    async def fetch_all(self, symbols: List[str]) -> dict:
        """
        Fetch market data + news for all symbols.
        Returns {"market": {symbol: snapshot}, "news": {symbol: snapshot}}
        """
        market_data = {}
        news_data = {}

        for symbol in symbols:
            market_data[symbol] = await self.fetch_market_data(symbol)
            news_data[symbol] = await self.fetch_news_sentiment(symbol)

        return {"market": market_data, "news": news_data}

    # ──────────────────────────────────────────────────────────────────
    # Parsing helpers
    # ──────────────────────────────────────────────────────────────────
    def _parse_news_response(self, symbol: str, response: str) -> NewsDataSnapshot:
        """Parse AI-generated news response."""
        news = NewsDataSnapshot(symbol=symbol)
        lines = response.strip().split("\n")
        current_section = None

        for line in lines:
            line = line.strip()
            if line.startswith("HEADLINES:"):
                current_section = "headlines"
            elif line.startswith("SENTIMENT_SCORE:"):
                try:
                    news.sentiment_score = float(line.split(":", 1)[1].strip())
                except ValueError:
                    pass
                current_section = None
            elif line.startswith("KEY_EVENTS:"):
                current_section = "key_events"
            elif line.startswith("RISK_EVENTS:"):
                current_section = "risk_events"
            elif line.startswith("SECTOR_SENTIMENT:"):
                news.sector_sentiment = line.split(":", 1)[1].strip()
                current_section = None
            elif line.startswith("- ") and current_section:
                item = line[2:].strip()
                if current_section == "headlines":
                    news.headlines.append(item)
                elif current_section == "key_events":
                    news.key_events.append(item)
                elif current_section == "risk_events":
                    news.risk_events.append(item)

        return news

