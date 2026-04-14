"""
GrowwService – high-level service layer built on top of GrowwAPIClient.

This module handles:
  - Client initialisation from config (token exchange)
  - Normalising SDK responses for the rest of the app
  - Providing helper utilities (date helpers, candle → list normalisation)

All Groww API interactions in the rest of the app should go through
GrowwService rather than calling GrowwAPIClient directly.
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from growwapi import GrowwAPI

from app.core.config import settings
from app.services.groww_api import GrowwAPIClient, GrowwFeedClient

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
_groww_service: Optional["GrowwService"] = None


async def get_groww_service() -> "GrowwService":
    """Return (and lazily initialise) the module-level GrowwService."""
    global _groww_service
    if _groww_service is None:
        _groww_service = GrowwService()
        await _groww_service.initialise()
    return _groww_service


# ---------------------------------------------------------------------------
# Service class
# ---------------------------------------------------------------------------
class GrowwService:
    """
    High-level async service wrapping GrowwAPIClient.

    Initialisation
    --------------
    The Groww SDK requires a bearer *access token* (not the raw API key).
    Call ``initialise()`` once at startup to exchange the API key for a token
    and build the underlying client.

    If no API key is configured the service runs in *offline mode* – all
    data methods return ``None`` and the rest of the app falls back to
    paper-trading / mock data.
    """

    def __init__(self):
        self.client: Optional[GrowwAPIClient] = None
        self.feed: Optional[GrowwFeedClient] = None
        self._online = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    async def initialise(self):
        """
        Exchange the API key + secret for an access token and build the SDK client.
        Safe to call even when no credentials are configured.
        """
        api_key = settings.GROWW_API_KEY
        api_secret = settings.GROWW_API_SECRET
        if not api_key or not api_secret:
            logger.warning(
                "GROWW_API_KEY or GROWW_API_SECRET not set – Groww service running in offline mode."
            )
            return

        # If a pre-issued auth token is present in config use it directly,
        # otherwise obtain one via the SDK's get_access_token flow.
        token = getattr(settings, "GROWW_AUTH_TOKEN", "") or ""
        if not token:
            logger.info("Fetching Groww access token via API key + secret …")
            token = GrowwAPIClient.get_access_token(api_key, api_secret)

        if not token:
            logger.error(
                "Could not obtain Groww access token – service running in offline mode."
            )
            return

        self.client = GrowwAPIClient(token)
        self.feed = GrowwFeedClient(GrowwAPI(token))
        self._online = True
        logger.info("GrowwService initialised and online.")

    @property
    def is_online(self) -> bool:
        return self._online and self.client is not None

    # ------------------------------------------------------------------
    # User / account
    # ------------------------------------------------------------------
    async def get_user_profile(self) -> Optional[Dict]:
        """Return the authenticated user's profile from Groww."""
        if not self.is_online:
            return None
        return await self.client.get_user_profile()

    async def get_available_margin(self) -> Optional[Dict]:
        """Return available margin details."""
        if not self.is_online:
            return None
        return await self.client.get_available_margin()

    # ------------------------------------------------------------------
    # Instruments
    # ------------------------------------------------------------------
    async def get_all_instruments(self) -> Optional[List[Dict]]:
        """
        Download the full Groww instrument master (equity + F&O).

        The SDK caches the CSV after the first download.
        """
        if not self.is_online:
            return None
        return await self.client.get_all_instruments()

    async def get_instrument(
        self, trading_symbol: str, exchange: str = GrowwAPI.EXCHANGE_NSE
    ) -> Optional[Dict]:
        """
        Look up an instrument by exchange + trading symbol.

        Args:
            trading_symbol: e.g. "RELIANCE"
            exchange:        GrowwAPI.EXCHANGE_NSE (default) | EXCHANGE_BSE
        """
        if not self.is_online:
            return None
        return await self.client.get_instrument_by_exchange_and_trading_symbol(
            exchange, trading_symbol
        )

    async def get_instrument_by_groww_symbol(self, groww_symbol: str) -> Optional[Dict]:
        """Look up an instrument by its Groww symbol string."""
        if not self.is_online:
            return None
        return await self.client.get_instrument_by_groww_symbol(groww_symbol)

    # ------------------------------------------------------------------
    # Market data
    # ------------------------------------------------------------------
    async def get_ltp(
        self,
        trading_symbol: str,
        exchange: str = "NSE",
        segment: str = GrowwAPI.SEGMENT_CASH,
    ) -> Optional[float]:
        """
        Return the last traded price for a single symbol.

        Internally looks up the instrument, then calls the SDK's get_ltp
        with exchange_trading_symbols="NSE_RELIANCE" and segment from instrument.

        Args:
            trading_symbol: e.g. "RELIANCE"
            exchange:        e.g. "NSE" or "BSE"
            segment:         Segment string e.g. "CASH", "FNO"
        """
        if not self.is_online:
            return None
        exchange_trading_symbol = f"{exchange}_{trading_symbol}"
        result = await self.client.get_ltp(
            exchange_trading_symbols=exchange_trading_symbol,
            segment=segment
        )
        if result:
            return result.get("ltp")
        return None

    async def get_quote(
        self,
        trading_symbol: str,
        exchange: str = GrowwAPI.EXCHANGE_NSE,
        segment: str = GrowwAPI.SEGMENT_CASH,
    ) -> Optional[Dict]:
        """
        Return the full market quote for a symbol.

        Args:
            trading_symbol: e.g. "RELIANCE"
            exchange:        GrowwAPI.EXCHANGE_NSE | EXCHANGE_BSE
            segment:         GrowwAPI.SEGMENT_CASH | SEGMENT_FNO
        """
        if not self.is_online:
            return None
        return await self.client.get_quote(trading_symbol, exchange, segment)

    async def get_ohlc(
        self,
        trading_symbol: str,
        exchange: str = "NSE",
        segment: str = GrowwAPI.SEGMENT_CASH,
    ) -> Optional[Dict]:
        """
        Return OHLC data for a symbol.

        Args:
            trading_symbol: e.g. "RELIANCE"
            exchange:        e.g. "NSE" or "BSE"
            segment:         GrowwAPI.SEGMENT_CASH | SEGMENT_FNO
        """
        if not self.is_online:
            return None
        key = f"{exchange}_{trading_symbol}"
        result = await self.client.get_ohlc(
            segment=segment,
            exchange_trading_symbols=key
        )
        if result:
            return result.get(key) or next(iter(result.values()), None)
        return None

    # ------------------------------------------------------------------
    # Historical candles
    # ------------------------------------------------------------------

    # Map human-readable interval names → minutes
    _INTERVAL_MAP = {
        "1minute": 1, "1min": 1,
        "5minute": 5, "5min": 5,
        "15minute": 15, "15min": 15,
        "30minute": 30, "30min": 30,
        "1hour": 60, "1hr": 60,
        "4hour": 240, "4hr": 240,
        "1day": 1440, "day": 1440,
        "1week": 10080, "week": 10080,
    }

    async def get_historical_candles(
        self,
        trading_symbol: str,
        interval: str = "1day",
        days: int = 365,
        exchange: str = GrowwAPI.EXCHANGE_NSE,
        segment: str = GrowwAPI.SEGMENT_CASH,
    ) -> Optional[List[Dict]]:
        """
        Fetch historical OHLCV candles using the Groww SDK.

        The SDK expects ``start_time`` / ``end_time`` as
        ``"yyyy-MM-dd HH:mm:ss"`` strings and ``interval_in_minutes`` as int.

        Args:
            trading_symbol: e.g. "RELIANCE"
            interval:        "1minute","5minute","15minute","30minute",
                             "1hour","4hour","1day" (default),"1week"
            days:            How many calendar days of history (max ~365)
            exchange:        GrowwAPI.EXCHANGE_NSE | EXCHANGE_BSE
            segment:         GrowwAPI.SEGMENT_CASH | SEGMENT_FNO

        Returns:
            List of dicts: [{timestamp, open, high, low, close, volume}, ...]
            Returns None if offline or on error.
        """
        if not self.is_online:
            return None

        # Resolve interval string → minutes
        interval_mins = self._INTERVAL_MAP.get(interval.lower(), 1440)

        # Build start/end in "yyyy-MM-dd HH:mm:ss" format
        end_dt = datetime.today()
        start_dt = end_dt - timedelta(days=min(days, 365))
        end_time = end_dt.strftime("%Y-%m-%d %H:%M:%S")
        start_time = start_dt.strftime("%Y-%m-%d %H:%M:%S")

        raw = await self.client.get_historical_candle_data(
            trading_symbol=trading_symbol,
            exchange=exchange,
            segment=segment,
            start_time=start_time,
            end_time=end_time,
            interval_in_minutes=interval_mins,
        )
        return self._normalise_candles(raw)

    def _normalise_candles(self, raw: Any) -> Optional[List[Dict]]:
        """
        Convert SDK candle response to list of plain dicts.

        SDK returns:
        {"candles": [[epoch_sec, open, high, low, close, volume], ...],
         "start_time": "...", "end_time": "...", "interval_in_minutes": 5}
        """
        if raw is None:
            return None
        # Handle the actual SDK response format
        if isinstance(raw, dict) and "candles" in raw:
            candles = raw["candles"]
            return [
                {
                    "timestamp": c[0],
                    "open": c[1],
                    "high": c[2],
                    "low": c[3],
                    "close": c[4],
                    "volume": c[5],
                }
                for c in candles
                if isinstance(c, (list, tuple)) and len(c) >= 6
            ]
        # pandas DataFrame fallback
        if hasattr(raw, "to_dict"):
            return raw.to_dict(orient="records")
        # Already a list
        if isinstance(raw, list):
            return raw
        logger.warning(f"Unexpected candle data type: {type(raw)}")
        return None

    # ------------------------------------------------------------------
    # Portfolio
    # ------------------------------------------------------------------
    async def get_holdings(self) -> Optional[Dict]:
        """
        Fetch long-term delivery holdings (CNC positions).

        Returns raw SDK response dict (keys depend on SDK version).
        """
        if not self.is_online:
            return None
        return await self.client.get_holdings()

    async def get_positions(
        self, segment: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Fetch intraday / F&O open positions.

        Args:
            segment: Optional – GrowwAPI.SEGMENT_CASH | SEGMENT_FNO | etc.
        """
        if not self.is_online:
            return None
        return await self.client.get_positions(segment)

    async def get_position_for_symbol(
        self,
        trading_symbol: str,
        segment: str = GrowwAPI.SEGMENT_CASH,
    ) -> Optional[Dict]:
        """Return position details for a single trading symbol."""
        if not self.is_online:
            return None
        return await self.client.get_position_for_symbol(trading_symbol, segment)

    # ------------------------------------------------------------------
    # Orders
    # ------------------------------------------------------------------
    async def place_order(
        self,
        trading_symbol: str,
        quantity: int,
        transaction_type: str,
        order_type: str = GrowwAPI.ORDER_TYPE_LIMIT,
        product: str = GrowwAPI.PRODUCT_CNC,
        validity: str = GrowwAPI.VALIDITY_DAY,
        exchange: str = GrowwAPI.EXCHANGE_NSE,
        segment: str = GrowwAPI.SEGMENT_CASH,
        price: Optional[float] = None,
        trigger_price: Optional[float] = None,
        order_reference_id: Optional[str] = None,
    ) -> Optional[Dict]:
        """
        Place a new order via Groww.

        Live trading must be enabled in settings (``LIVE_TRADING_ENABLED=True``).

        Args:
            trading_symbol:    e.g. "WIPRO"
            quantity:          Number of shares / lots
            transaction_type:  GrowwAPI.TRANSACTION_TYPE_BUY | TRANSACTION_TYPE_SELL
            order_type:        GrowwAPI.ORDER_TYPE_LIMIT (default) | MARKET | STOP_LOSS | STOP_LOSS_MARKET
            product:           GrowwAPI.PRODUCT_CNC (default) | MIS | NRML | MTF
            validity:          GrowwAPI.VALIDITY_DAY (default) | IOC | GTC | GTD | EOS
            exchange:          GrowwAPI.EXCHANGE_NSE (default) | EXCHANGE_BSE
            segment:           GrowwAPI.SEGMENT_CASH (default) | SEGMENT_FNO
            price:             Optional: Price for LIMIT / SL orders
            trigger_price:     Optional: Trigger price for SL / SL_M orders
            order_reference_id: Optional: 8-20 char alphanumeric reference ID

        Returns:
            dict e.g. {"groww_order_id": "...", "order_status": "OPEN",
                       "order_reference_id": "...", "remark": "Order placed successfully"}
        """
        if not self.is_online:
            logger.warning("place_order: Groww service is offline.")
            return None
        if not settings.LIVE_TRADING_ENABLED:
            logger.warning("place_order: LIVE_TRADING_ENABLED is False – order blocked.")
            return None

        return await self.client.place_order(
            trading_symbol=trading_symbol,
            quantity=quantity,
            validity=validity,
            exchange=exchange,
            segment=segment,
            product=product,
            order_type=order_type,
            transaction_type=transaction_type,
            price=price,
            trigger_price=trigger_price,
            order_reference_id=order_reference_id,
        )

    async def cancel_order(
        self, groww_order_id: str, segment: str = GrowwAPI.SEGMENT_CASH
    ) -> Optional[Dict]:
        """Cancel an open order by its Groww order ID."""
        if not self.is_online:
            return None
        return await self.client.cancel_order(segment, groww_order_id)

    async def modify_order(
        self,
        groww_order_id: str,
        quantity: int,
        order_type: str,
        segment: str = GrowwAPI.SEGMENT_CASH,
        price: Optional[float] = None,
        trigger_price: Optional[float] = None,
    ) -> Optional[Dict]:
        """
        Modify an existing open order.

        Returns:
            dict e.g. {"groww_order_id": "...", "order_status": "OPEN"}
        """
        if not self.is_online:
            return None
        return await self.client.modify_order(
            quantity=quantity,
            order_type=order_type,
            segment=segment,
            groww_order_id=groww_order_id,
            price=price,
            trigger_price=trigger_price,
        )

    async def get_order_list(
        self,
        segment: Optional[str] = None,
        page: int = 0,
        page_size: int = 25,
    ) -> Optional[Dict]:
        """Return the order book (paginated)."""
        if not self.is_online:
            return None
        return await self.client.get_order_list(
            segment=segment, page=page, page_size=page_size
        )

    async def get_order_status(
        self, groww_order_id: str, segment: str = GrowwAPI.SEGMENT_CASH
    ) -> Optional[Dict]:
        """Return the status of a specific order."""
        if not self.is_online:
            return None
        return await self.client.get_order_status(segment, groww_order_id)

    async def get_order_margin_details(
        self, orders: List[Dict], segment: str = GrowwAPI.SEGMENT_CASH
    ) -> Optional[Dict]:
        """Calculate the margin required for a set of orders before placing."""
        if not self.is_online:
            return None
        return await self.client.get_order_margin_details(segment, orders)

    # ------------------------------------------------------------------
    # Options / F&O
    # ------------------------------------------------------------------
    async def get_option_chain(
        self,
        underlying: str,
        expiry_date: str,
        exchange: str = GrowwAPI.EXCHANGE_NSE,
    ) -> Optional[Dict]:
        """
        Fetch the complete options chain for an underlying.

        Args:
            underlying:   e.g. "NIFTY" or "RELIANCE"
            expiry_date:  "YYYY-MM-DD"
            exchange:     GrowwAPI.EXCHANGE_NSE (default)
        """
        if not self.is_online:
            return None
        return await self.client.get_option_chain(exchange, underlying, expiry_date)

    async def get_expiries(
        self,
        underlying_symbol: str,
        exchange: str = GrowwAPI.EXCHANGE_NSE,
        year: Optional[int] = None,
        month: Optional[int] = None,
    ) -> Optional[Dict]:
        """
        Return available expiry dates for an underlying.

        Args:
            underlying_symbol: e.g. "NIFTY"
            exchange:           GrowwAPI.EXCHANGE_NSE (default)
            year:               Optional year filter
            month:              Optional month filter (1-12)
        """
        if not self.is_online:
            return None
        return await self.client.get_expiries(exchange, underlying_symbol, year, month)

    async def get_contracts(
        self,
        underlying_symbol: str,
        expiry_date: str,
        exchange: str = GrowwAPI.EXCHANGE_NSE,
    ) -> Optional[Dict]:
        """
        Fetch all CE + PE contracts for a given underlying and expiry.

        Args:
            underlying_symbol: e.g. "NIFTY"
            expiry_date:       "YYYY-MM-DD"
            exchange:          GrowwAPI.EXCHANGE_NSE (default)
        """
        if not self.is_online:
            return None
        return await self.client.get_contracts(exchange, underlying_symbol, expiry_date)

    async def get_greeks(
        self,
        underlying: str,
        trading_symbol: str,
        expiry: str,
        exchange: str = GrowwAPI.EXCHANGE_NSE,
    ) -> Optional[Dict]:
        """
        Get option Greeks for a specific FNO contract.

        Args:
            underlying:     e.g. "NIFTY"
            trading_symbol: e.g. "NIFTY25O1425100CE"
            expiry:         "YYYY-MM-DD" e.g. "2025-10-14"
            exchange:       GrowwAPI.EXCHANGE_NSE (default)

        Returns:
            dict e.g. {"greeks": {"delta": ..., "gamma": ..., "theta": ...,
                       "vega": ..., "rho": ..., "iv": ...}}
        """
        if not self.is_online:
            return None
        return await self.client.get_greeks(
            exchange=exchange,
            underlying=underlying,
            trading_symbol=trading_symbol,
            expiry=expiry
        )

    # ------------------------------------------------------------------
    # Smart orders (GTT / OCO)
    # ------------------------------------------------------------------
    async def create_smart_order(self, **kwargs) -> Optional[Dict]:
        """Create a GTT or OCO smart order. Pass keyword arguments per SDK docs."""
        if not self.is_online:
            return None
        return await self.client.create_smart_order(**kwargs)

    async def cancel_smart_order(
        self,
        smart_order_id: str,
        smart_order_type: str = GrowwAPI.SMART_ORDER_TYPE_GTT,
        segment: str = GrowwAPI.SEGMENT_CASH,
    ) -> Optional[Dict]:
        """Cancel a GTT / OCO smart order."""
        if not self.is_online:
            return None
        return await self.client.cancel_smart_order(segment, smart_order_type, smart_order_id)

    async def get_smart_order_list(
        self,
        smart_order_type: Optional[str] = None,
        segment: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Optional[Dict]:
        """Return a list of smart orders with optional filters."""
        if not self.is_online:
            return None
        return await self.client.get_smart_order_list(
            smart_order_type=smart_order_type,
            segment=segment,
            status=status,
        )

    # ------------------------------------------------------------------
    # Live feed (GrowwFeed WebSocket)
    # ------------------------------------------------------------------
    def subscribe_live_ltp(
        self,
        instruments: List[Dict],
        on_data_received=None,
    ):
        """
        Subscribe to live LTP data for instruments.

        Args:
            instruments: List of dicts e.g.
                [{"exchange": "NSE", "segment": "CASH", "exchange_token": "2885"}]
            on_data_received: Optional callback triggered when data arrives
        """
        if not self.is_online or not self.feed:
            logger.warning("subscribe_live_ltp: service is offline or feed not available")
            return
        self.feed.subscribe_ltp(instruments, on_data_received=on_data_received)

    def unsubscribe_live_ltp(self, instruments: List[Dict]):
        """Unsubscribe from live LTP for instruments."""
        if not self.feed:
            return
        self.feed.unsubscribe_ltp(instruments)

    def get_live_ltp(self) -> Optional[Dict]:
        """
        Poll the latest live LTP data.

        Returns:
            dict e.g.
            {"ltp": {"NSE": {"CASH": {"2885": {"tsInMillis": ..., "ltp": 1419.1}}}}}
        """
        if not self.feed:
            return None
        return self.feed.get_ltp()

    async def start_live_feed(self):
        """Start the live feed consumer in a background thread."""
        if not self.is_online or not self.feed:
            logger.warning("start_live_feed: service is offline or feed not available")
            return
        await self.feed.start()

    def stop_live_feed(self):
        """Stop the live feed and unsubscribe all."""
        if self.feed:
            self.feed.stop()

    # ------------------------------------------------------------------
    # Live feed — Index values
    # ------------------------------------------------------------------
    def subscribe_live_index_value(
        self,
        instruments: List[Dict],
        on_data_received=None,
    ):
        """
        Subscribe to live index values.

        Args:
            instruments: List of dicts e.g.
                [{"exchange": "NSE", "segment": "CASH", "exchange_token": "NIFTY"},
                 {"exchange": "BSE", "segment": "CASH", "exchange_token": "1"}]
            on_data_received: Optional callback triggered when data arrives
        """
        if not self.is_online or not self.feed:
            logger.warning("subscribe_live_index_value: service is offline or feed not available")
            return
        self.feed.subscribe_index_value(instruments, on_data_received=on_data_received)

    def unsubscribe_live_index_value(self, instruments: List[Dict]):
        """Unsubscribe from live index values."""
        if not self.feed:
            return
        self.feed.unsubscribe_index_value(instruments)

    def get_live_index_value(self) -> Optional[Dict]:
        """
        Poll the latest live index values.

        Returns:
            dict e.g.
            {"NSE": {"CASH": {"NIFTY": {"tsInMillis": ..., "value": 24386.7}}},
             "BSE": {"CASH": {"1": {"tsInMillis": ..., "value": 73386.7}}}}
        """
        if not self.feed:
            return None
        return self.feed.get_index_value()

    # ------------------------------------------------------------------
    # Live feed — FNO order updates
    # ------------------------------------------------------------------
    def subscribe_fno_order_updates(self, on_data_received=None):
        """
        Subscribe to derivative (FNO) order updates.

        Args:
            on_data_received: Optional callback. Receives meta dict with
                              "feed_type" and "segment" keys.
        """
        if not self.is_online or not self.feed:
            logger.warning("subscribe_fno_order_updates: service is offline or feed not available")
            return
        self.feed.subscribe_fno_order_updates(on_data_received=on_data_received)

    def unsubscribe_fno_order_updates(self):
        """Unsubscribe from FNO order updates."""
        if not self.feed:
            return
        self.feed.unsubscribe_fno_order_updates()

    def get_fno_order_update(self) -> Optional[Dict]:
        """
        Poll the latest FNO order update.

        Returns:
            dict e.g.
            {"qty": 75, "price": "130", "filledQty": 75, "avgFillPrice": "110",
             "growwOrderId": "...", "exchangeOrderId": "...",
             "orderStatus": "EXECUTED", "duration": "DAY",
             "exchange": "NSE", "segment": "FNO", "product": "NRML",
             "contractId": "NIFTY2522025400CE"}
        """
        if not self.feed:
            return None
        return self.feed.get_fno_order_update()

    # ------------------------------------------------------------------
    # Live feed — Equity order updates
    # ------------------------------------------------------------------
    def subscribe_equity_order_updates(self, on_data_received=None):
        """
        Subscribe to equity (CASH segment) order updates.

        Args:
            on_data_received: Optional callback. Receives meta dict with
                              "feed_type" and "segment" keys.
        """
        if not self.is_online or not self.feed:
            logger.warning("subscribe_equity_order_updates: service is offline or feed not available")
            return
        self.feed.subscribe_equity_order_updates(on_data_received=on_data_received)

    def unsubscribe_equity_order_updates(self):
        """Unsubscribe from equity order updates."""
        if not self.feed:
            return
        self.feed.unsubscribe_equity_order_updates()

    def get_equity_order_update(self) -> Optional[Dict]:
        """
        Poll the latest equity order update.

        Returns:
            dict e.g.
            {"qty": 3, "filledQty": 3, "avgFillPrice": "145",
             "growwOrderId": "...", "exchangeOrderId": "...",
             "orderStatus": "EXECUTED", "duration": "DAY",
             "exchange": "NSE", "contractId": "INE221H01019"}
        """
        if not self.feed:
            return None
        return self.feed.get_equity_order_update()

