"""
Agent 4: CHIEF TRADING AGENT (THE BOSS)
─────────────────────────────────────────
The final decision maker. Takes verdicts from AlgoAgent and SentimentAgent,
applies risk management rules from the UI config, and makes the final
BUY / SELL / HOLD decision with full reasoning.

This is the ONLY agent that can trigger a trade.

Responsibilities:
  - Weigh algo verdict vs sentiment verdict
  - Apply position sizing from UI config
  - Apply stop-loss / take-profit from UI config
  - Risk management (max position size, max open positions)
  - Final reasoning with dissenting opinions noted
  - Execute paper trade or live trade
"""
import logging
import uuid
from typing import Optional, List
from datetime import datetime

from app.models.agent_schemas import (
    AlgoAgentVerdict, SentimentAgentVerdict, ChiefDecision,
    TradeAction, RiskLevel, PaperTradingConfig, MarketDataSnapshot
)
from app.services.ai_provider import ai_provider

logger = logging.getLogger(__name__)


class ChiefTradingAgent:
    """
    Level 3 Agent — THE BOSS. Makes final trading decisions.
    Receives verdicts from AlgoAgent + SentimentAgent + UI config.
    Returns ChiefDecision.
    """

    ROLE = "CHIEF_TRADER"

    # Weight allocation for combining agent signals
    ALGO_WEIGHT = 0.6
    SENTIMENT_WEIGHT = 0.4

    async def decide(
        self,
        symbol: str,
        market: MarketDataSnapshot,
        algo_verdict: AlgoAgentVerdict,
        sentiment_verdict: SentimentAgentVerdict,
        config: PaperTradingConfig,
        current_positions: int = 0,
        portfolio_value: float = 0,
    ) -> ChiefDecision:
        """
        Make the final trading decision.

        Inputs:
            - market: raw market data
            - algo_verdict: technical analysis agent's decision
            - sentiment_verdict: news/sentiment agent's decision
            - config: paper trading config from UI
            - current_positions: how many positions already open
            - portfolio_value: current total portfolio value
        """
        current_price = market.ltp or 0
        logger.info(
            f"[ChiefAgent] Deciding on {symbol} | "
            f"Algo={algo_verdict.action.value}({algo_verdict.confidence:.0%}) "
            f"Sentiment={sentiment_verdict.action.value}({sentiment_verdict.confidence:.0%})"
        )

        # ── Step 1: Combine agent signals ─────────────────────────
        combined_action, combined_confidence, dissenting = self._combine_signals(
            algo_verdict, sentiment_verdict
        )

        # ── Step 2: Risk management checks ────────────────────────
        risk_level, risk_approved, risk_reason = self._check_risk(
            action=combined_action,
            confidence=combined_confidence,
            current_price=current_price,
            config=config,
            current_positions=current_positions,
            portfolio_value=portfolio_value,
        )

        if not risk_approved:
            logger.info(f"[ChiefAgent] {symbol}: Risk check BLOCKED — {risk_reason}")
            combined_action = TradeAction.HOLD
            dissenting.append(f"Risk Manager Override: {risk_reason}")

        # ── Step 3: Position sizing ───────────────────────────────
        quantity = 0
        position_size_pct = 0.0
        if combined_action in (TradeAction.BUY, TradeAction.SELL) and current_price > 0:
            capital = portfolio_value or config.initial_capital
            max_position = capital * (config.max_position_size_percent / 100)
            risk_capital = capital * (config.risk_per_trade_percent / 100)
            # Use the smaller of max position or risk-based position
            position_value = min(max_position, risk_capital / (config.stop_loss_percent / 100))
            position_value = min(position_value, capital * 0.25)  # hard cap 25%
            quantity = max(1, int(position_value / current_price))
            position_size_pct = (quantity * current_price / capital) * 100

        # ── Step 4: Stop-loss and take-profit ─────────────────────
        stop_loss = None
        take_profit = None
        if combined_action == TradeAction.BUY and current_price > 0:
            stop_loss = round(current_price * (1 - config.stop_loss_percent / 100), 2)
            take_profit = round(current_price * (1 + config.take_profit_percent / 100), 2)
        elif combined_action == TradeAction.SELL and current_price > 0:
            stop_loss = round(current_price * (1 + config.stop_loss_percent / 100), 2)
            take_profit = round(current_price * (1 - config.take_profit_percent / 100), 2)

        # ── Step 5: AI-powered final reasoning ────────────────────
        chief_reasoning = await self._generate_reasoning(
            symbol=symbol,
            action=combined_action,
            confidence=combined_confidence,
            current_price=current_price,
            algo_verdict=algo_verdict,
            sentiment_verdict=sentiment_verdict,
            risk_level=risk_level,
            quantity=quantity,
            stop_loss=stop_loss,
            take_profit=take_profit,
            dissenting=dissenting,
        )

        decision = ChiefDecision(
            symbol=symbol,
            action=combined_action,
            confidence=round(combined_confidence, 3),
            price=current_price,
            quantity=quantity,
            stop_loss=stop_loss,
            take_profit=take_profit,
            risk_level=risk_level,
            position_size_percent=round(position_size_pct, 2),
            algo_verdict=algo_verdict,
            sentiment_verdict=sentiment_verdict,
            chief_reasoning=chief_reasoning,
            dissenting_opinions=dissenting,
            trade_id=str(uuid.uuid4())[:8],
            timestamp=datetime.now(),
        )

        logger.info(
            f"[ChiefAgent] DECISION: {symbol} → {combined_action.value} "
            f"x{quantity} @ ₹{current_price} "
            f"(confidence={combined_confidence:.0%}, risk={risk_level.value})"
        )
        return decision

    # ──────────────────────────────────────────────────────────────
    # Internal methods
    # ──────────────────────────────────────────────────────────────

    def _combine_signals(
        self,
        algo: AlgoAgentVerdict,
        sentiment: SentimentAgentVerdict,
    ) -> tuple:
        """
        Combine algo and sentiment verdicts with weighted scoring.
        Returns (action, confidence, dissenting_opinions).
        """
        dissenting = []

        # Convert actions to numeric scores: BUY=+1, HOLD=0, SELL=-1
        action_to_score = {TradeAction.BUY: 1, TradeAction.HOLD: 0, TradeAction.SELL: -1}
        algo_score = action_to_score[algo.action] * algo.confidence * self.ALGO_WEIGHT
        sent_score = action_to_score[sentiment.action] * sentiment.confidence * self.SENTIMENT_WEIGHT

        combined_score = algo_score + sent_score

        # Track disagreements
        if algo.action != sentiment.action:
            dissenting.append(
                f"AlgoAgent says {algo.action.value} ({algo.confidence:.0%}) "
                f"but SentimentAgent says {sentiment.action.value} ({sentiment.confidence:.0%})"
            )

        # Determine final action
        if combined_score > 0.15:
            action = TradeAction.BUY
        elif combined_score < -0.15:
            action = TradeAction.SELL
        else:
            action = TradeAction.HOLD

        # Confidence = absolute combined score, capped at 1.0
        confidence = min(abs(combined_score) / (self.ALGO_WEIGHT + self.SENTIMENT_WEIGHT), 1.0)

        # Require minimum confidence to act
        if confidence < 0.3 and action != TradeAction.HOLD:
            dissenting.append(
                f"Combined confidence too low ({confidence:.0%}), downgrading to HOLD"
            )
            action = TradeAction.HOLD

        return action, confidence, dissenting

    def _check_risk(
        self,
        action: TradeAction,
        confidence: float,
        current_price: float,
        config: PaperTradingConfig,
        current_positions: int,
        portfolio_value: float,
    ) -> tuple:
        """
        Run risk management checks.
        Returns (risk_level, approved: bool, reason: str).
        """
        # Determine risk level
        if confidence >= 0.7:
            risk_level = RiskLevel.LOW
        elif confidence >= 0.5:
            risk_level = RiskLevel.MEDIUM
        elif confidence >= 0.3:
            risk_level = RiskLevel.HIGH
        else:
            risk_level = RiskLevel.VERY_HIGH

        # Check: max open positions
        if action == TradeAction.BUY and current_positions >= config.max_open_positions:
            return risk_level, False, f"Max open positions reached ({config.max_open_positions})"

        # Check: minimum confidence
        if action != TradeAction.HOLD and confidence < 0.25:
            return risk_level, False, f"Confidence too low ({confidence:.0%})"

        # Check: VERY_HIGH risk not allowed for BUY
        if action == TradeAction.BUY and risk_level == RiskLevel.VERY_HIGH:
            return risk_level, False, "Risk too high for new position"

        return risk_level, True, "Approved"

    async def _generate_reasoning(
        self,
        symbol: str,
        action: TradeAction,
        confidence: float,
        current_price: float,
        algo_verdict: AlgoAgentVerdict,
        sentiment_verdict: SentimentAgentVerdict,
        risk_level: RiskLevel,
        quantity: int,
        stop_loss: Optional[float],
        take_profit: Optional[float],
        dissenting: List[str],
    ) -> str:
        """Use AI to generate a human-readable final reasoning."""
        try:
            prompt = f"""You are the Chief Trading Officer making the final call. Summarize your decision in 3-4 concise sentences.

Stock: {symbol}
Decision: {action.value}
Confidence: {confidence:.0%}
Current Price: ₹{current_price}
Quantity: {quantity}
Stop Loss: ₹{stop_loss or 'N/A'}
Take Profit: ₹{take_profit or 'N/A'}
Risk Level: {risk_level.value}

Technical Analysis (AlgoAgent):
  Action: {algo_verdict.action.value} ({algo_verdict.confidence:.0%})
  Trend: {algo_verdict.trend}
  Key: {algo_verdict.reasoning[:200]}

Sentiment Analysis:
  Action: {sentiment_verdict.action.value} ({sentiment_verdict.confidence:.0%})
  Score: {sentiment_verdict.sentiment_score:+.2f}
  Key: {sentiment_verdict.reasoning[:200]}

Dissenting Opinions:
{chr(10).join('- ' + d for d in dissenting) if dissenting else '- None, all agents agree'}

Write 3-4 sentences: What you decided, why, what the risks are, and key levels to watch."""

            response = ai_provider.analyze(
                prompt,
                system_prompt="You are a chief trading officer. Be concise, decisive, and specific.",
                max_tokens=300
            )
            return response.strip()

        except Exception as e:
            logger.error(f"[ChiefAgent] Reasoning generation failed: {e}")
            return (
                f"Decision: {action.value} {symbol} x{quantity} @ ₹{current_price}. "
                f"Algo says {algo_verdict.action.value} ({algo_verdict.confidence:.0%}), "
                f"Sentiment says {sentiment_verdict.action.value} ({sentiment_verdict.confidence:.0%}). "
                f"Risk: {risk_level.value}."
            )

