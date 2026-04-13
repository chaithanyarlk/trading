"""
Agent 3: SENTIMENT / NEWS AGENT
─────────────────────────────────
The news reader. Takes news data from DataFetcherAgent,
uses AI to assess sentiment and macro risks.

Responsibilities:
  - Interpret news headlines for bullish/bearish signals
  - Assess macro risks (rate hikes, regulatory changes, etc.)
  - Sector-level sentiment
  - Outputs: SentimentAgentVerdict with action + confidence + reasoning
"""
import logging
from datetime import datetime

from app.models.agent_schemas import (
    NewsDataSnapshot, SentimentAgentVerdict, TradeAction, MarketDataSnapshot
)
from app.services.ai_provider import ai_provider

logger = logging.getLogger(__name__)


class SentimentAgent:
    """
    Level 2 Agent — news/sentiment analysis using AI.
    Receives NewsDataSnapshot + MarketDataSnapshot, returns SentimentAgentVerdict.
    """

    ROLE = "SENTIMENT_ANALYST"

    async def analyze(
        self,
        news: NewsDataSnapshot,
        market: MarketDataSnapshot
    ) -> SentimentAgentVerdict:
        """
        Analyze news sentiment and produce a trading verdict.
        Uses AI to interpret headlines + market context.
        """
        symbol = news.symbol
        logger.info(f"[SentimentAgent] Analyzing sentiment for {symbol}")

        try:
            prompt = f"""You are a senior sentiment analyst for Indian stock markets.

Stock: {symbol}
Current Price: ₹{market.ltp or 'N/A'}
Day Change: {market.change_percent or 'N/A'}%

Headlines:
{chr(10).join('- ' + h for h in news.headlines) if news.headlines else '- No headlines available'}

Key Events:
{chr(10).join('- ' + e for e in news.key_events) if news.key_events else '- None'}

Risk Events:
{chr(10).join('- ' + r for r in news.risk_events) if news.risk_events else '- None'}

Sector Sentiment: {news.sector_sentiment or 'Unknown'}
Raw Sentiment Score: {news.sentiment_score}

Based on all this, provide your sentiment-based trading verdict:

ACTION: [BUY/SELL/HOLD]
CONFIDENCE: [0.0 to 1.0]
SENTIMENT_SCORE: [-1.0 to 1.0]
KEY_FACTORS:
- factor 1
- factor 2
RISK_FACTORS:
- risk 1
REASONING: [2-3 sentences on why you chose this action based on sentiment/news]"""

            response = ai_provider.analyze(
                prompt,
                system_prompt="You are a financial sentiment analyst. Be concise and data-driven.",
                max_tokens=500
            )

            verdict = self._parse_response(symbol, response, news)

        except Exception as e:
            logger.error(f"[SentimentAgent] Error analyzing {symbol}: {e}")
            verdict = SentimentAgentVerdict(
                symbol=symbol,
                action=TradeAction.HOLD,
                confidence=0.0,
                sentiment_score=news.sentiment_score,
                reasoning=f"Sentiment analysis failed: {str(e)}"
            )

        logger.info(
            f"[SentimentAgent] {symbol}: {verdict.action.value} "
            f"(confidence={verdict.confidence:.0%}, sentiment={verdict.sentiment_score:+.2f})"
        )
        return verdict

    def _parse_response(
        self, symbol: str, response: str, news: NewsDataSnapshot
    ) -> SentimentAgentVerdict:
        """Parse AI response into SentimentAgentVerdict."""
        verdict = SentimentAgentVerdict(
            symbol=symbol,
            action=TradeAction.HOLD,
            confidence=0.3,
            sentiment_score=news.sentiment_score,
            reasoning=response
        )

        lines = response.strip().split("\n")
        current_section = None

        for line in lines:
            line = line.strip()
            if line.startswith("ACTION:"):
                action_str = line.split(":", 1)[1].strip().upper()
                if "BUY" in action_str:
                    verdict.action = TradeAction.BUY
                elif "SELL" in action_str:
                    verdict.action = TradeAction.SELL
                else:
                    verdict.action = TradeAction.HOLD
            elif line.startswith("CONFIDENCE:"):
                try:
                    conf = float(line.split(":", 1)[1].strip())
                    verdict.confidence = min(max(conf, 0.0), 1.0)
                except ValueError:
                    pass
            elif line.startswith("SENTIMENT_SCORE:"):
                try:
                    score = float(line.split(":", 1)[1].strip())
                    verdict.sentiment_score = min(max(score, -1.0), 1.0)
                except ValueError:
                    pass
            elif line.startswith("KEY_FACTORS:"):
                current_section = "key_factors"
            elif line.startswith("RISK_FACTORS:"):
                current_section = "risk_factors"
            elif line.startswith("REASONING:"):
                verdict.reasoning = line.split(":", 1)[1].strip()
                current_section = None
            elif line.startswith("- ") and current_section:
                item = line[2:].strip()
                if current_section == "key_factors":
                    verdict.key_factors.append(item)
                elif current_section == "risk_factors":
                    verdict.risk_events.append(item)

        return verdict

