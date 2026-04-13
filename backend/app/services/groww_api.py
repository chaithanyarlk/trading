"""
Groww API Client using the official growwapi SDK.
Reference: https://groww.in/trade-api/docs/python-sdk/

SDK is synchronous — all calls are wrapped in run_in_executor for async usage.
"""
import asyncio
import logging
from typing import Optional, List, Dict, Any, Tuple
from functools import partial

from growwapi import GrowwAPI

logger = logging.getLogger(__name__)


class GrowwAPIClient:
    """
    Async-friendly wrapper around the official growwapi SDK (GrowwAPI).

    Authentication:
        token = GrowwAPI.get_access_token(api_key, totp=totp, secret=secret)["data"]["access_token"]
        client = GrowwAPIClient(token)
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
    def get_access_token(api_key: str, totp: Optional[str] = None,
                         secret: Optional[str] = None) -> Optional[str]:
        """
        Obtain an access token from Groww.

        Args:
            api_key: Your Groww API key
            totp:    TOTP code (if TOTP-based auth)
            secret:  Secret key (if secret-based auth)

        Returns:
            access_token string, or None on failure
        """
        try:
            result = GrowwAPI.get_access_token(api_key, totp=totp, secret=secret)
            return result.get("data", {}).get("access_token")
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
        Look up an instrument by its Groww symbol (e.g. "NSE_EQ|INE009A01021").

        Args:
            groww_symbol: Groww contract identifier
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
        exchange_trading_symbols: Tuple[str, ...],
        segment: str
    ) -> Optional[Dict]:
        """
        Get Last Traded Price for one or more symbols.

        Args:
            exchange_trading_symbols: Tuple of "EXCHANGE:SYMBOL" strings,
                                      e.g. ("NSE:RELIANCE", "NSE:TCS")
            segment: GrowwAPI.SEGMENT_CASH | SEGMENT_FNO | etc.

        Returns:
            dict with LTP data keyed by symbol
        """
        try:
            return await self._run(self._sdk.get_ltp, exchange_trading_symbols, segment)
        except Exception as e:
            logger.error(f"get_ltp error: {e}")
            return None

    async def get_ohlc(
        self,
        exchange_trading_symbols: Tuple[str, ...],
        segment: str
    ) -> Optional[Dict]:
        """
        Get OHLC data for one or more symbols.

        Args:
            exchange_trading_symbols: Tuple of "EXCHANGE:SYMBOL" strings
            segment: GrowwAPI.SEGMENT_CASH | SEGMENT_FNO | etc.
        """
        try:
            return await self._run(self._sdk.get_ohlc, exchange_trading_symbols, segment)
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
    async def get_historical_candles(
        self,
        exchange: str,
        segment: str,
        trading_symbol: str,
        interval: str,
        from_date: str,
        to_date: str
    ) -> Optional[Any]:
        """
        Fetch historical OHLCV candles.

        Args:
            exchange:       GrowwAPI.EXCHANGE_NSE
            segment:        GrowwAPI.SEGMENT_CASH | SEGMENT_FNO
            trading_symbol: e.g. "RELIANCE"
            interval:       GrowwAPI.CANDLE_INTERVAL_DAY | CANDLE_INTERVAL_MIN_1 | etc.
                            Valid values: "1minute","2minute","3minute","5minute",
                                         "10minute","15minute","30minute",
                                         "1hour","4hour","1day","1week","1month"
            from_date:      "YYYY-MM-DD"
            to_date:        "YYYY-MM-DD"

        Returns:
            DataFrame or list of candle dicts returned by SDK
        """
        try:
            return await self._run(
                self._sdk.get_historical_candles,
                exchange, segment, trading_symbol, interval, from_date, to_date
            )
        except Exception as e:
            logger.error(f"get_historical_candles({trading_symbol}) error: {e}")
            return None

    async def get_historical_candle_data_v2(
        self,
        trading_symbol: str,
        exchange: str,
        segment: str,
        start_time: str,
        end_time: str,
        interval_in_minutes: int = 1440,
    ) -> Optional[Any]:
        """
        Fetch historical candle data using the correct SDK signature.

        Per Groww SDK docs the method accepts:
            trading_symbol, exchange, segment, start_time, end_time,
            interval_in_minutes

        Args:
            trading_symbol: e.g. "RELIANCE"
            exchange:       GrowwAPI.EXCHANGE_NSE
            segment:        GrowwAPI.SEGMENT_CASH
            start_time:     "yyyy-MM-dd HH:mm:ss"  e.g. "2025-04-01 09:15:00"
            end_time:       "yyyy-MM-dd HH:mm:ss"  e.g. "2026-04-13 15:30:00"
            interval_in_minutes: Candle width in minutes.
                                 1=1min, 5=5min, 15=15min, 30=30min,
                                 60=1hr, 240=4hr, 1440=1day, 10080=1week

        Returns:
            DataFrame or list of candle dicts from SDK
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
            logger.error(f"get_historical_candle_data_v2({trading_symbol}) error: {e}")
            return None

    # ------------------------------------------------------------------
    # PORTFOLIO – HOLDINGS & POSITIONS
    # ------------------------------------------------------------------
    async def get_holdings(self) -> Optional[Dict]:
        """
        Fetch long-term equity holdings (CNC/delivery positions).

        Returns:
            SDK response dict with holdings list
        """
        try:
            return await self._run(self._sdk.get_holdings_for_user)
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
        exchange: str,
        segment: str,
        transaction_type: str,
        quantity: int,
        order_type: str,
        product: str,
        validity: str,
        price: float = 0.0,
        trigger_price: Optional[float] = None,
        order_reference_id: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Place a new order.

        Args:
            trading_symbol:    e.g. "RELIANCE"
            exchange:          GrowwAPI.EXCHANGE_NSE | EXCHANGE_BSE
            segment:           GrowwAPI.SEGMENT_CASH | SEGMENT_FNO
            transaction_type:  GrowwAPI.TRANSACTION_TYPE_BUY | TRANSACTION_TYPE_SELL
            quantity:          Number of shares/lots
            order_type:        GrowwAPI.ORDER_TYPE_MARKET | LIMIT | SL | SL_M
            product:           GrowwAPI.PRODUCT_CNC (delivery) | MIS (intraday) | NRML (F&O)
            validity:          GrowwAPI.VALIDITY_DAY | IOC | GTC | GTD | EOS
            price:             Required for LIMIT / SL; 0.0 for MARKET
            trigger_price:     Required for SL / SL_M orders
            order_reference_id: Optional client-side reference ID

        Returns:
            SDK response dict containing groww_order_id on success
        """
        try:
            return await self._run(
                self._sdk.place_order,
                validity=validity,
                exchange=exchange,
                order_type=order_type,
                product=product,
                quantity=quantity,
                segment=segment,
                trading_symbol=trading_symbol,
                transaction_type=transaction_type,
                order_reference_id=order_reference_id,
                price=price,
                trigger_price=trigger_price
            )
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
        segment: str,
        groww_order_id: str,
        order_type: str,
        quantity: int,
        price: Optional[float] = None,
        trigger_price: Optional[float] = None
    ) -> Optional[Dict]:
        """
        Modify an existing open order.

        Args:
            segment:        GrowwAPI.SEGMENT_CASH | SEGMENT_FNO
            groww_order_id: Order ID to modify
            order_type:     GrowwAPI.ORDER_TYPE_LIMIT | SL | SL_M
            quantity:       New quantity
            price:          New limit price (for LIMIT / SL)
            trigger_price:  New trigger price (for SL / SL_M)
        """
        try:
            return await self._run(
                self._sdk.modify_order,
                order_type=order_type,
                segment=segment,
                groww_order_id=groww_order_id,
                quantity=quantity,
                price=price,
                trigger_price=trigger_price
            )
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
            expiry_date:  "YYYY-MM-DD"
        """
        try:
            return await self._run(
                self._sdk.get_option_chain, exchange, underlying, expiry_date
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
        Get option Greeks (delta, gamma, theta, vega, IV) for a contract.

        Args:
            exchange:       GrowwAPI.EXCHANGE_NSE
            underlying:     Underlying symbol e.g. "NIFTY"
            trading_symbol: Option contract symbol e.g. "NIFTY24APR22000CE"
            expiry:         "YYYY-MM-DD"
        """
        try:
            return await self._run(
                self._sdk.get_greeks, exchange, underlying, trading_symbol, expiry
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

