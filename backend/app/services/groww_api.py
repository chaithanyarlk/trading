"""
Groww API Client using the official growwapi SDK.
Reference: https://groww.in/trade-api/docs/python-sdk/

SDK is synchronous — all calls are wrapped in run_in_executor for async usage.
"""
import asyncio
import logging
from typing import Optional, List, Dict, Any, Tuple
from functools import partial

from growwapi import GrowwAPI, GrowwFeed

logger = logging.getLogger(__name__)


class GrowwAPIClient:
    """
    Async-friendly wrapper around the official growwapi SDK (GrowwAPI).

    Authentication:
        access_token = GrowwAPI.get_access_token(api_key=api_key, secret=secret)
        client = GrowwAPIClient(access_token)
    """

    def __init__(self, token: str):
        """
        Args:
            token: Bearer access token obtained via GrowwAPI.get_access_token()
        """
        self._sdk = GrowwAPI(token)

    # ------------------------------------------------------------------
    # Internal helper – run blocking SDK calls off the event loop
    # ------------------------------------------------------------------
    async def _run(self, func, *args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, partial(func, *args, **kwargs))

    # ------------------------------------------------------------------
    # AUTH (static – call before creating the client)
    # ------------------------------------------------------------------
    @staticmethod
    def get_access_token(api_key: str, secret: str) -> Optional[str]:
        """
        Obtain an access token from Groww.

        Args:
            api_key: Your Groww API key
            secret:  Your Groww API secret

        Returns:
            access_token string, or None on failure
        """
        try:
            access_token = GrowwAPI.get_access_token(api_key=api_key, secret=secret)
            return access_token
        except Exception as e:
            logger.error(f"Failed to get access token: {e}")
            return None

    # ------------------------------------------------------------------
    # USER PROFILE & MARGINS
    # ------------------------------------------------------------------
    async def get_user_profile(self) -> Optional[Dict]:
        """Fetch the logged-in user's profile."""
        try:
            return await self._run(self._sdk.get_user_profile)
        except Exception as e:
            logger.error(f"get_user_profile error: {e}")
            return None

    async def get_available_margin(self) -> Optional[Dict]:
        """Fetch available margin details for the user."""
        try:
            return await self._run(self._sdk.get_available_margin_details)
        except Exception as e:
            logger.error(f"get_available_margin error: {e}")
            return None

    # ------------------------------------------------------------------
    # INSTRUMENTS
    # ------------------------------------------------------------------
    async def get_all_instruments(self) -> Optional[List[Dict]]:
        """
        Download and return the full instrument list (CSV → list of dicts).
        Result is cached inside the SDK after first call.
        """
        try:
            result = await self._run(self._sdk.get_all_instruments)
            # SDK may return a DataFrame; normalise to list of dicts
            if hasattr(result, "to_dict"):
                return result.to_dict(orient="records")
            return result
        except Exception as e:
            logger.error(f"get_all_instruments error: {e}")
            return None

    async def get_instrument_by_groww_symbol(self, groww_symbol: str) -> Optional[Dict]:
        """
        Look up an instrument by its Groww symbol (e.g. "NSE-RELIANCE").

        Args:
            groww_symbol: Groww contract identifier e.g. "NSE-RELIANCE"
        """
        try:
            return await self._run(self._sdk.get_instrument_by_groww_symbol, groww_symbol)
        except Exception as e:
            logger.error(f"get_instrument_by_groww_symbol error: {e}")
            return None

    async def get_instrument_by_exchange_and_trading_symbol(
        self, exchange: str, trading_symbol: str
    ) -> Optional[Dict]:
        """
        Look up an instrument by exchange + trading symbol.

        Args:
            exchange:       e.g. GrowwAPI.EXCHANGE_NSE
            trading_symbol: e.g. "RELIANCE"
        """
        try:
            return await self._run(
                self._sdk.get_instrument_by_exchange_and_trading_symbol,
                exchange, trading_symbol
            )
        except Exception as e:
            logger.error(f"get_instrument_by_exchange_and_trading_symbol error: {e}")
            return None

    async def get_instrument_by_exchange_token(self, exchange_token: str) -> Optional[Dict]:
        """
        Look up an instrument by its exchange token.

        Args:
            exchange_token: The numeric exchange token string
        """
        try:
            return await self._run(
                self._sdk.get_instrument_by_exchange_token, exchange_token
            )
        except Exception as e:
            logger.error(f"get_instrument_by_exchange_token error: {e}")
            return None

    # ------------------------------------------------------------------
    # MARKET DATA (LTP / OHLC / FULL QUOTE)
    # ------------------------------------------------------------------
    async def get_ltp(
        self,
        exchange_trading_symbols: str,
        segment: str
    ) -> Optional[Dict]:
        """
        Get Last Traded Price for a symbol.

        Args:
            exchange_trading_symbols: e.g. "NSE_RELIANCE"
                                      Format: "{EXCHANGE}_{trading_symbol}"
            segment: Segment from instrument e.g. "CASH", "FNO"

        Returns:
            dict e.g. {"ltp": 149.5}
        """
        try:
            return await self._run(
                self._sdk.get_ltp,
                exchange_trading_symbols=exchange_trading_symbols,
                segment=segment
            )
        except Exception as e:
            logger.error(f"get_ltp error: {e}")
            return None

    async def get_ohlc(
        self,
        segment: str,
        exchange_trading_symbols: Any
    ) -> Optional[Dict]:
        """
        Get OHLC data for one or more symbols.

        Args:
            segment: GrowwAPI.SEGMENT_CASH | SEGMENT_FNO | etc.
            exchange_trading_symbols: Single string e.g. "NSE_NIFTY"
                                      or tuple e.g. ("NSE_NIFTY", "NSE_RELIANCE")

        Returns:
            dict keyed by symbol e.g.
            {"NSE_RELIANCE": {"open": ..., "high": ..., "low": ..., "close": ...}}
        """
        try:
            return await self._run(
                self._sdk.get_ohlc,
                segment=segment,
                exchange_trading_symbols=exchange_trading_symbols
            )
        except Exception as e:
            logger.error(f"get_ohlc error: {e}")
            return None

    async def get_quote(
        self,
        trading_symbol: str,
        exchange: str,
        segment: str
    ) -> Optional[Dict]:
        """
        Get full market quote for a single symbol.

        Args:
            trading_symbol: e.g. "RELIANCE"
            exchange:        GrowwAPI.EXCHANGE_NSE or EXCHANGE_BSE
            segment:         GrowwAPI.SEGMENT_CASH | SEGMENT_FNO | etc.
        """
        try:
            return await self._run(self._sdk.get_quote, trading_symbol, exchange, segment)
        except Exception as e:
            logger.error(f"get_quote({trading_symbol}) error: {e}")
            return None

    # ------------------------------------------------------------------
    # HISTORICAL DATA
    # ------------------------------------------------------------------
    async def get_historical_candle_data(
        self,
        trading_symbol: str,
        exchange: str,
        segment: str,
        start_time: str,
        end_time: str,
        interval_in_minutes: int = 5,
    ) -> Optional[Dict]:
        """
        Fetch historical OHLCV candle data.

        Args:
            trading_symbol:      e.g. "RELIANCE"
            exchange:            GrowwAPI.EXCHANGE_NSE
            segment:             GrowwAPI.SEGMENT_CASH
            start_time:          "yyyy-MM-dd HH:mm:ss" e.g. "2025-02-27 10:00:00"
            end_time:            "yyyy-MM-dd HH:mm:ss" e.g. "2025-02-27 14:00:00"
            interval_in_minutes: Candle width in minutes (default 5).
                                 1, 5, 15, 30, 60, 240, 1440, 10080

        Returns:
            dict e.g. {"candles": [[epoch_sec, open, high, low, close, volume], ...],
                       "start_time": "...", "end_time": "...", "interval_in_minutes": 5}
        """
        try:
            return await self._run(
                self._sdk.get_historical_candle_data,
                trading_symbol=trading_symbol,
                exchange=exchange,
                segment=segment,
                start_time=start_time,
                end_time=end_time,
                interval_in_minutes=interval_in_minutes,
            )
        except Exception as e:
            logger.error(f"get_historical_candle_data({trading_symbol}) error: {e}")
            return None

    # ------------------------------------------------------------------
    # PORTFOLIO – HOLDINGS & POSITIONS
    # ------------------------------------------------------------------
    async def get_holdings(self) -> Optional[Dict]:
        """
        Fetch long-term equity holdings (CNC/delivery positions).

        Returns:
            SDK response dict with "holdings" list containing:
              isin, trading_symbol, quantity, average_price,
              pledge_quantity, demat_locked_quantity, groww_locked_quantity,
              repledge_quantity, t1_quantity, demat_free_quantity,
              corporate_action_additional_quantity, active_demat_transfer_quantity
        """
        try:
            return await self._run(self._sdk.get_holdings_for_user, timeout=5)
        except Exception as e:
            logger.error(f"get_holdings error: {e}")
            return None

    async def get_positions(self, segment: Optional[str] = None) -> Optional[Dict]:
        """
        Fetch intraday / F&O positions.

        Args:
            segment: Optional filter – GrowwAPI.SEGMENT_CASH | SEGMENT_FNO | etc.
        """
        try:
            return await self._run(self._sdk.get_positions_for_user, segment)
        except Exception as e:
            logger.error(f"get_positions error: {e}")
            return None

    async def get_position_for_symbol(
        self, trading_symbol: str, segment: str
    ) -> Optional[Dict]:
        """
        Fetch position details for a specific trading symbol.

        Args:
            trading_symbol: e.g. "RELIANCE"
            segment:        GrowwAPI.SEGMENT_CASH | SEGMENT_FNO
        """
        try:
            return await self._run(
                self._sdk.get_position_for_trading_symbol, trading_symbol, segment
            )
        except Exception as e:
            logger.error(f"get_position_for_symbol({trading_symbol}) error: {e}")
            return None

    # ------------------------------------------------------------------
    # ORDERS
    # ------------------------------------------------------------------
    async def place_order(
        self,
        trading_symbol: str,
        quantity: int,
        validity: str,
        exchange: str,
        segment: str,
        product: str,
        order_type: str,
        transaction_type: str,
        price: Optional[float] = None,
        trigger_price: Optional[float] = None,
        order_reference_id: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Place a new order.

        Args:
            trading_symbol:    e.g. "WIPRO"
            quantity:          Number of shares/lots
            validity:          GrowwAPI.VALIDITY_DAY | IOC | GTC | GTD | EOS
            exchange:          GrowwAPI.EXCHANGE_NSE | EXCHANGE_BSE
            segment:           GrowwAPI.SEGMENT_CASH | SEGMENT_FNO
            product:           GrowwAPI.PRODUCT_CNC (delivery) | MIS (intraday) | NRML (F&O)
            order_type:        GrowwAPI.ORDER_TYPE_LIMIT | MARKET | STOP_LOSS | STOP_LOSS_MARKET
            transaction_type:  GrowwAPI.TRANSACTION_TYPE_BUY | TRANSACTION_TYPE_SELL
            price:             Optional: Price for LIMIT / SL orders
            trigger_price:     Optional: Trigger price for SL / SL_M orders
            order_reference_id: Optional: 8-20 char alphanumeric reference ID

        Returns:
            dict e.g. {"groww_order_id": "...", "order_status": "OPEN",
                       "order_reference_id": "...", "remark": "Order placed successfully"}
        """
        try:
            kwargs = dict(
                trading_symbol=trading_symbol,
                quantity=quantity,
                validity=validity,
                exchange=exchange,
                segment=segment,
                product=product,
                order_type=order_type,
                transaction_type=transaction_type,
            )
            if price is not None:
                kwargs["price"] = price
            if trigger_price is not None:
                kwargs["trigger_price"] = trigger_price
            if order_reference_id is not None:
                kwargs["order_reference_id"] = order_reference_id

            return await self._run(self._sdk.place_order, **kwargs)
        except Exception as e:
            logger.error(f"place_order({trading_symbol} {transaction_type}) error: {e}")
            return None

    async def cancel_order(
        self, segment: str, groww_order_id: str
    ) -> Optional[Dict]:
        """
        Cancel an open order.

        Args:
            segment:        GrowwAPI.SEGMENT_CASH | SEGMENT_FNO
            groww_order_id: Order ID returned by place_order
        """
        try:
            return await self._run(self._sdk.cancel_order, segment, groww_order_id)
        except Exception as e:
            logger.error(f"cancel_order({groww_order_id}) error: {e}")
            return None

    async def modify_order(
        self,
        quantity: int,
        order_type: str,
        segment: str,
        groww_order_id: str,
        price: Optional[float] = None,
        trigger_price: Optional[float] = None
    ) -> Optional[Dict]:
        """
        Modify an existing open order.

        Args:
            quantity:       New quantity
            order_type:     GrowwAPI.ORDER_TYPE_MARKET | LIMIT | STOP_LOSS | STOP_LOSS_MARKET
            segment:        GrowwAPI.SEGMENT_CASH | SEGMENT_FNO
            groww_order_id: Order ID to modify
            price:          Optional: New limit price (for LIMIT / SL)
            trigger_price:  Optional: New trigger price (for SL / SL_M)

        Returns:
            dict e.g. {"groww_order_id": "...", "order_status": "OPEN"}
        """
        try:
            kwargs = dict(
                quantity=quantity,
                order_type=order_type,
                segment=segment,
                groww_order_id=groww_order_id,
            )
            if price is not None:
                kwargs["price"] = price
            if trigger_price is not None:
                kwargs["trigger_price"] = trigger_price

            return await self._run(self._sdk.modify_order, **kwargs)
        except Exception as e:
            logger.error(f"modify_order({groww_order_id}) error: {e}")
            return None

    async def get_order_list(
        self,
        segment: Optional[str] = None,
        page: int = 0,
        page_size: int = 25
    ) -> Optional[Dict]:
        """
        Fetch the order book.

        Args:
            segment:   Optional filter by segment
            page:      Page number (0-indexed)
            page_size: Number of records per page
        """
        try:
            return await self._run(
                self._sdk.get_order_list, page=page, page_size=page_size, segment=segment
            )
        except Exception as e:
            logger.error(f"get_order_list error: {e}")
            return None

    async def get_order_detail(
        self, segment: str, groww_order_id: str
    ) -> Optional[Dict]:
        """Fetch details of a specific order by its Groww order ID."""
        try:
            return await self._run(self._sdk.get_order_detail, segment, groww_order_id)
        except Exception as e:
            logger.error(f"get_order_detail({groww_order_id}) error: {e}")
            return None

    async def get_order_status(
        self, segment: str, groww_order_id: str
    ) -> Optional[Dict]:
        """Fetch the current status of an order."""
        try:
            return await self._run(self._sdk.get_order_status, segment, groww_order_id)
        except Exception as e:
            logger.error(f"get_order_status({groww_order_id}) error: {e}")
            return None

    async def get_order_status_by_reference(
        self, segment: str, order_reference_id: str
    ) -> Optional[Dict]:
        """Fetch order status by client-side reference ID."""
        try:
            return await self._run(
                self._sdk.get_order_status_by_reference, segment, order_reference_id
            )
        except Exception as e:
            logger.error(f"get_order_status_by_reference({order_reference_id}) error: {e}")
            return None

    async def get_trade_list_for_order(
        self,
        groww_order_id: str,
        segment: str,
        page: int = 0,
        page_size: int = 25
    ) -> Optional[Dict]:
        """Get individual trade fills (partial fills, etc.) for a given order."""
        try:
            return await self._run(
                self._sdk.get_trade_list_for_order,
                groww_order_id, segment, page, page_size
            )
        except Exception as e:
            logger.error(f"get_trade_list_for_order({groww_order_id}) error: {e}")
            return None

    async def get_order_margin_details(
        self, segment: str, orders: List[Dict]
    ) -> Optional[Dict]:
        """
        Calculate margin required for a list of orders before placing.

        Args:
            segment: GrowwAPI.SEGMENT_CASH | SEGMENT_FNO
            orders:  List of order dicts
        """
        try:
            return await self._run(self._sdk.get_order_margin_details, segment, orders)
        except Exception as e:
            logger.error(f"get_order_margin_details error: {e}")
            return None

    # ------------------------------------------------------------------
    # OPTIONS / F&O
    # ------------------------------------------------------------------
    async def get_option_chain(
        self, exchange: str, underlying: str, expiry_date: str
    ) -> Optional[Dict]:
        """
        Fetch the full options chain for an underlying.

        Args:
            exchange:     GrowwAPI.EXCHANGE_NSE
            underlying:   Underlying symbol e.g. "NIFTY" or "RELIANCE"
            expiry_date:  "YYYY-MM-DD" e.g. "2025-11-28"

        Returns:
            dict with "underlying_ltp" and "strikes" keyed by strike price,
            each containing CE/PE with greeks, trading_symbol, ltp, open_interest, volume
        """
        try:
            return await self._run(
                self._sdk.get_option_chain,
                exchange=exchange,
                underlying=underlying,
                expiry_date=expiry_date
            )
        except Exception as e:
            logger.error(f"get_option_chain({underlying}) error: {e}")
            return None

    async def get_expiries(
        self,
        exchange: str,
        underlying_symbol: str,
        year: Optional[int] = None,
        month: Optional[int] = None
    ) -> Optional[Dict]:
        """
        Get available expiry dates for an underlying.

        Args:
            exchange:           GrowwAPI.EXCHANGE_NSE
            underlying_symbol:  e.g. "NIFTY" or "RELIANCE"
            year:               Optional filter by year (e.g. 2026)
            month:              Optional filter by month (1-12)
        """
        try:
            return await self._run(
                self._sdk.get_expiries, exchange, underlying_symbol, year, month
            )
        except Exception as e:
            logger.error(f"get_expiries({underlying_symbol}) error: {e}")
            return None

    async def get_contracts(
        self, exchange: str, underlying_symbol: str, expiry_date: str
    ) -> Optional[Dict]:
        """
        Get all CE + PE contracts for a given underlying and expiry date.

        Args:
            exchange:           GrowwAPI.EXCHANGE_NSE
            underlying_symbol:  e.g. "NIFTY"
            expiry_date:        "YYYY-MM-DD"
        """
        try:
            return await self._run(
                self._sdk.get_contracts, exchange, underlying_symbol, expiry_date
            )
        except Exception as e:
            logger.error(f"get_contracts({underlying_symbol}) error: {e}")
            return None

    async def get_greeks(
        self,
        exchange: str,
        underlying: str,
        trading_symbol: str,
        expiry: str
    ) -> Optional[Dict]:
        """
        Get option Greeks (delta, gamma, theta, vega, rho, IV) for an FNO contract.

        Args:
            exchange:       GrowwAPI.EXCHANGE_NSE
            underlying:     Underlying symbol e.g. "NIFTY"
            trading_symbol: Option contract symbol e.g. "NIFTY25O1425100CE"
            expiry:         "YYYY-MM-DD" e.g. "2025-10-14"

        Returns:
            dict e.g. {"greeks": {"delta": 0.6, "gamma": 0.0014,
                       "theta": -8.1, "vega": 13.1, "rho": 2.7, "iv": 8.2}}
        """
        try:
            return await self._run(
                self._sdk.get_greeks,
                exchange=exchange,
                underlying=underlying,
                trading_symbol=trading_symbol,
                expiry=expiry
            )
        except Exception as e:
            logger.error(f"get_greeks({trading_symbol}) error: {e}")
            return None

    # ------------------------------------------------------------------
    # SMART ORDERS (GTT / OCO)
    # ------------------------------------------------------------------
    async def create_smart_order(self, **kwargs) -> Optional[Dict]:
        """Create a GTT or OCO smart order. Pass SDK keyword arguments."""
        try:
            return await self._run(self._sdk.create_smart_order, **kwargs)
        except Exception as e:
            logger.error(f"create_smart_order error: {e}")
            return None

    async def cancel_smart_order(
        self, segment: str, smart_order_type: str, smart_order_id: str
    ) -> Optional[Dict]:
        """Cancel a smart order (GTT/OCO) by its ID."""
        try:
            return await self._run(
                self._sdk.cancel_smart_order, segment, smart_order_type, smart_order_id
            )
        except Exception as e:
            logger.error(f"cancel_smart_order({smart_order_id}) error: {e}")
            return None

    async def get_smart_order(
        self, segment: str, smart_order_type: str, smart_order_id: str
    ) -> Optional[Dict]:
        """Fetch details of a single smart order."""
        try:
            return await self._run(
                self._sdk.get_smart_order, segment, smart_order_type, smart_order_id
            )
        except Exception as e:
            logger.error(f"get_smart_order({smart_order_id}) error: {e}")
            return None

    async def get_smart_order_list(
        self,
        smart_order_type: Optional[str] = None,
        segment: Optional[str] = None,
        status: Optional[str] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        start_date_time: Optional[str] = None,
        end_date_time: Optional[str] = None
    ) -> Optional[Dict]:
        """Fetch smart orders with optional filters."""
        try:
            return await self._run(
                self._sdk.get_smart_order_list,
                smart_order_type=smart_order_type,
                segment=segment,
                status=status,
                page=page,
                page_size=page_size,
                start_date_time=start_date_time,
                end_date_time=end_date_time
            )
        except Exception as e:
            logger.error(f"get_smart_order_list error: {e}")
            return None

    # ------------------------------------------------------------------
    # SDK CONSTANTS re-exported for convenience
    # ------------------------------------------------------------------
    EXCHANGE_NSE = GrowwAPI.EXCHANGE_NSE
    EXCHANGE_BSE = GrowwAPI.EXCHANGE_BSE
    EXCHANGE_MCX = GrowwAPI.EXCHANGE_MCX

    SEGMENT_CASH      = GrowwAPI.SEGMENT_CASH
    SEGMENT_FNO       = GrowwAPI.SEGMENT_FNO
    SEGMENT_CURRENCY  = GrowwAPI.SEGMENT_CURRENCY
    SEGMENT_COMMODITY = GrowwAPI.SEGMENT_COMMODITY

    TRANSACTION_TYPE_BUY  = GrowwAPI.TRANSACTION_TYPE_BUY
    TRANSACTION_TYPE_SELL = GrowwAPI.TRANSACTION_TYPE_SELL

    ORDER_TYPE_MARKET      = GrowwAPI.ORDER_TYPE_MARKET
    ORDER_TYPE_LIMIT       = GrowwAPI.ORDER_TYPE_LIMIT
    ORDER_TYPE_STOP_LOSS   = GrowwAPI.ORDER_TYPE_STOP_LOSS
    ORDER_TYPE_STOP_LOSS_M = GrowwAPI.ORDER_TYPE_STOP_LOSS_MARKET

    PRODUCT_CNC  = GrowwAPI.PRODUCT_CNC   # Delivery / Cash & Carry
    PRODUCT_MIS  = GrowwAPI.PRODUCT_MIS   # Intraday
    PRODUCT_NRML = GrowwAPI.PRODUCT_NRML  # Normal (F&O overnight)
    PRODUCT_MTF  = GrowwAPI.PRODUCT_MTF   # Margin Trading Facility

    VALIDITY_DAY = GrowwAPI.VALIDITY_DAY
    VALIDITY_IOC = GrowwAPI.VALIDITY_IOC
    VALIDITY_GTC = GrowwAPI.VALIDITY_GTC
    VALIDITY_GTD = GrowwAPI.VALIDITY_GTD
    VALIDITY_EOS = GrowwAPI.VALIDITY_EOS

    CANDLE_INTERVAL_1MIN  = GrowwAPI.CANDLE_INTERVAL_MIN_1
    CANDLE_INTERVAL_5MIN  = GrowwAPI.CANDLE_INTERVAL_MIN_5
    CANDLE_INTERVAL_15MIN = GrowwAPI.CANDLE_INTERVAL_MIN_15
    CANDLE_INTERVAL_30MIN = GrowwAPI.CANDLE_INTERVAL_MIN_30
    CANDLE_INTERVAL_1HR   = GrowwAPI.CANDLE_INTERVAL_HOUR_1
    CANDLE_INTERVAL_4HR   = GrowwAPI.CANDLE_INTERVAL_HOUR_4
    CANDLE_INTERVAL_DAY   = GrowwAPI.CANDLE_INTERVAL_DAY
    CANDLE_INTERVAL_WEEK  = GrowwAPI.CANDLE_INTERVAL_WEEK
    CANDLE_INTERVAL_MONTH = GrowwAPI.CANDLE_INTERVAL_MONTH

    SMART_ORDER_TYPE_GTT = GrowwAPI.SMART_ORDER_TYPE_GTT
    SMART_ORDER_TYPE_OCO = GrowwAPI.SMART_ORDER_TYPE_OCO


class GrowwFeedClient:
    """
    Wrapper around GrowwFeed for live market data streaming.

    GrowwFeed provides real-time LTP data via WebSocket.
    feed.consume() is blocking, so it runs in a background thread.
    Polling via feed.get_ltp() is used for synchronous access.

    Usage:
        groww = GrowwAPI(access_token)
        feed_client = GrowwFeedClient(groww)
        feed_client.subscribe_ltp([
            {"exchange": "NSE", "segment": "CASH", "exchange_token": "2885"},
        ])
        feed_client.start()          # starts consume() in background thread
        ltp_data = feed_client.get_ltp()
        feed_client.unsubscribe_ltp([...])
        feed_client.stop()
    """

    def __init__(self, groww_api: GrowwAPI):
        """
        Args:
            groww_api: An initialised GrowwAPI instance
        """
        self._feed = GrowwFeed(groww_api)
        self._consume_thread: Optional[asyncio.Task] = None
        self._running = False
        self._subscribed_instruments: List[Dict] = []
        self._subscribed_indices: List[Dict] = []
        self._fno_order_updates_subscribed = False
        self._equity_order_updates_subscribed = False

    # ------------------------------------------------------------------
    # LTP subscriptions
    # ------------------------------------------------------------------
    def subscribe_ltp(
        self,
        instruments: List[Dict],
        on_data_received=None
    ):
        """
        Subscribe to live LTP for a list of instruments.

        Args:
            instruments: List of dicts e.g.
                [{"exchange": "NSE", "segment": "CASH", "exchange_token": "2885"}]
            on_data_received: Optional callback triggered when data arrives
        """
        if on_data_received:
            self._feed.subscribe_ltp(instruments, on_data_received=on_data_received)
        else:
            self._feed.subscribe_ltp(instruments)
        self._subscribed_instruments.extend(instruments)
        logger.info(f"Subscribed to LTP for {len(instruments)} instruments")

    def unsubscribe_ltp(self, instruments: List[Dict]):
        """
        Unsubscribe from live LTP for a list of instruments.

        Args:
            instruments: Same format as subscribe_ltp
        """
        self._feed.unsubscribe_ltp(instruments)
        for inst in instruments:
            if inst in self._subscribed_instruments:
                self._subscribed_instruments.remove(inst)
        logger.info(f"Unsubscribed from LTP for {len(instruments)} instruments")

    def get_ltp(self) -> Optional[Dict]:
        """
        Get the latest LTP data (synchronous poll).

        Returns:
            dict e.g.
            {"ltp": {"NSE": {"CASH": {"2885": {"tsInMillis": ..., "ltp": 1419.1}}}}}
        """
        try:
            return self._feed.get_ltp()
        except Exception as e:
            logger.error(f"get_ltp error: {e}")
            return None

    # ------------------------------------------------------------------
    # Index value subscriptions
    # ------------------------------------------------------------------
    def subscribe_index_value(
        self,
        instruments: List[Dict],
        on_data_received=None
    ):
        """
        Subscribe to live index values.

        Args:
            instruments: List of dicts e.g.
                [{"exchange": "NSE", "segment": "CASH", "exchange_token": "NIFTY"},
                 {"exchange": "BSE", "segment": "CASH", "exchange_token": "1"}]
            on_data_received: Optional callback triggered when data arrives
        """
        if on_data_received:
            self._feed.subscribe_index_value(instruments, on_data_received=on_data_received)
        else:
            self._feed.subscribe_index_value(instruments)
        self._subscribed_indices.extend(instruments)
        logger.info(f"Subscribed to index values for {len(instruments)} indices")

    def unsubscribe_index_value(self, instruments: List[Dict]):
        """
        Unsubscribe from live index values.

        Args:
            instruments: Same format as subscribe_index_value
        """
        self._feed.unsubscribe_index_value(instruments)
        for inst in instruments:
            if inst in self._subscribed_indices:
                self._subscribed_indices.remove(inst)
        logger.info(f"Unsubscribed from index values for {len(instruments)} indices")

    def get_index_value(self) -> Optional[Dict]:
        """
        Get the latest index values (synchronous poll).

        Returns:
            dict e.g.
            {"NSE": {"CASH": {"NIFTY": {"tsInMillis": ..., "value": 24386.7}}},
             "BSE": {"CASH": {"1": {"tsInMillis": ..., "value": 73386.7}}}}
        """
        try:
            return self._feed.get_index_value()
        except Exception as e:
            logger.error(f"get_index_value error: {e}")
            return None

    # ------------------------------------------------------------------
    # FNO order updates
    # ------------------------------------------------------------------
    def subscribe_fno_order_updates(self, on_data_received=None):
        """
        Subscribe to derivative (FNO) order updates.

        Args:
            on_data_received: Optional callback triggered when an order update arrives.
                              Receives a meta dict with "feed_type" and "segment" keys.
        """
        if on_data_received:
            self._feed.subscribe_fno_order_updates(on_data_received=on_data_received)
        else:
            self._feed.subscribe_fno_order_updates()
        self._fno_order_updates_subscribed = True
        logger.info("Subscribed to FNO order updates")

    def unsubscribe_fno_order_updates(self):
        """Unsubscribe from FNO order updates."""
        self._feed.unsubscribe_fno_order_updates()
        self._fno_order_updates_subscribed = False
        logger.info("Unsubscribed from FNO order updates")

    def get_fno_order_update(self) -> Optional[Dict]:
        """
        Get the latest FNO order update (synchronous poll).

        Returns:
            dict e.g.
            {"qty": 75, "price": "130", "filledQty": 75, "avgFillPrice": "110",
             "growwOrderId": "...", "exchangeOrderId": "...",
             "orderStatus": "EXECUTED", "duration": "DAY",
             "exchange": "NSE", "segment": "FNO", "product": "NRML",
             "contractId": "NIFTY2522025400CE"}
        """
        try:
            return self._feed.get_fno_order_update()
        except Exception as e:
            logger.error(f"get_fno_order_update error: {e}")
            return None

    # ------------------------------------------------------------------
    # Equity order updates
    # ------------------------------------------------------------------
    def subscribe_equity_order_updates(self, on_data_received=None):
        """
        Subscribe to equity (CASH segment) order updates.

        Args:
            on_data_received: Optional callback triggered when an order update arrives.
                              Receives a meta dict with "feed_type" and "segment" keys.
        """
        if on_data_received:
            self._feed.subscribe_equity_order_updates(on_data_received=on_data_received)
        else:
            self._feed.subscribe_equity_order_updates()
        self._equity_order_updates_subscribed = True
        logger.info("Subscribed to equity order updates")

    def unsubscribe_equity_order_updates(self):
        """Unsubscribe from equity order updates."""
        self._feed.unsubscribe_equity_order_updates()
        self._equity_order_updates_subscribed = False
        logger.info("Unsubscribed from equity order updates")

    def get_equity_order_update(self) -> Optional[Dict]:
        """
        Get the latest equity order update (synchronous poll).

        Returns:
            dict e.g.
            {"qty": 3, "filledQty": 3, "avgFillPrice": "145",
             "growwOrderId": "...", "exchangeOrderId": "...",
             "orderStatus": "EXECUTED", "duration": "DAY",
             "exchange": "NSE", "contractId": "INE221H01019"}
        """
        try:
            return self._feed.get_equity_order_update()
        except Exception as e:
            logger.error(f"get_equity_order_update error: {e}")
            return None

    async def start(self):
        """
        Start consuming the feed in a background thread.
        feed.consume() is blocking, so it runs via run_in_executor.
        """
        if self._running:
            logger.warning("Feed is already running")
            return
        self._running = True
        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, self._consume_blocking)
        logger.info("GrowwFeed consumer started in background thread")

    def _consume_blocking(self):
        """Blocking call — runs in a separate thread."""
        try:
            self._feed.consume()
        except Exception as e:
            logger.error(f"GrowwFeed consume error: {e}")
        finally:
            self._running = False

    def stop(self):
        """Unsubscribe all and stop the feed."""
        if self._subscribed_instruments:
            try:
                self._feed.unsubscribe_ltp(self._subscribed_instruments)
            except Exception as e:
                logger.error(f"Error unsubscribing LTP: {e}")
        if self._subscribed_indices:
            try:
                self._feed.unsubscribe_index_value(self._subscribed_indices)
            except Exception as e:
                logger.error(f"Error unsubscribing index values: {e}")
        if self._fno_order_updates_subscribed:
            try:
                self._feed.unsubscribe_fno_order_updates()
            except Exception as e:
                logger.error(f"Error unsubscribing FNO order updates: {e}")
        if self._equity_order_updates_subscribed:
            try:
                self._feed.unsubscribe_equity_order_updates()
            except Exception as e:
                logger.error(f"Error unsubscribing equity order updates: {e}")
        self._subscribed_instruments = []
        self._subscribed_indices = []
        self._fno_order_updates_subscribed = False
        self._equity_order_updates_subscribed = False
        self._running = False
        logger.info("GrowwFeed stopped")

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def subscribed_instruments(self) -> List[Dict]:
        return self._subscribed_instruments.copy()


