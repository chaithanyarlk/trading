"""
Groww Data Interface — single source of truth for all Groww API calls.

Every function here calls GrowwService.
No other file should call Groww directly.

Usage:
    from app.services.groww_data_interface import groww_data
    quote = await groww_data.get_stock_quote("RELIANCE")
"""
import logging
import re
import time
from typing import Dict, List, Optional
from datetime import datetime

from app.services.groww_api_enhanced import GrowwService, get_groww_service

logger = logging.getLogger(__name__)


class GrowwDataInterface:
    """
    Single source of truth for all Groww API calls.
    """

    def __init__(self):
        self._service: Optional[GrowwService] = None
        # Cached instrument data
        self._instruments_cache: Optional[List[Dict]] = None
        self._stocks_cache: Optional[List[Dict]] = None
        self._options_cache: Optional[List[Dict]] = None
        self._futures_cache: Optional[List[Dict]] = None

    async def _get_service(self) -> GrowwService:
        if self._service is None:
            self._service = await get_groww_service()
        return self._service

    # ──────────────────────────────────────────────────────────────────
    # 1. STOCK QUOTE
    # ──────────────────────────────────────────────────────────────────
    async def get_stock_quote(
        self,
        symbol: str,
        exchange: str = "NSE",
    ) -> Optional[Dict]:
        """Get full market quote for a stock."""
        svc = await self._get_service()
        return await svc.get_quote(symbol, exchange)

    # ──────────────────────────────────────────────────────────────────
    # 2. LAST TRADED PRICE
    # ──────────────────────────────────────────────────────────────────
    async def get_ltp(
        self,
        symbol: str,
        exchange: str = "NSE",
    ) -> Optional[float]:
        """Get last traded price for a symbol."""
        svc = await self._get_service()
        return await svc.get_ltp(symbol, exchange)

    # ──────────────────────────────────────────────────────────────────
    # 3. HISTORICAL CANDLES  (uses start_time/end_time as SDK requires)
    # ──────────────────────────────────────────────────────────────────
    async def get_historical_candles(
        self,
        symbol: str,
        interval: str = "1day",
        days: int = 365,
        exchange: str = "NSE",
    ) -> Optional[List[Dict]]:
        """
        Get historical OHLCV candles.

        Internally uses get_historical_candle_data with
        start_time/end_time in "yyyy-MM-dd HH:mm:ss" format
        and interval_in_minutes (not string intervals).

        Valid intervals: "1minute","5minute","15minute","30minute",
                         "1hour","4hour","1day","1week"
        """
        svc = await self._get_service()
        return await svc.get_historical_candles(symbol, interval, days, exchange)

    # ──────────────────────────────────────────────────────────────────
    # 4. ALL INSTRUMENTS — fetch, classify into stocks/options/futures
    # ──────────────────────────────────────────────────────────────────
    async def get_all_instruments(self, force_refresh: bool = False) -> Optional[List[Dict]]:
        """
        Download the full Groww instrument master.
        Returns a DataFrame-turned-list-of-dicts with fields:
          exchange, exchange_token, trading_symbol, groww_symbol,
          is_reserved, buy_allowed, sell_allowed, internal_trading_symbol, ...

        Cached after first call. Pass force_refresh=True to re-download.
        """
        if self._instruments_cache and not force_refresh:
            return self._instruments_cache
        svc = await self._get_service()
        instruments = await svc.get_all_instruments()
        if instruments:
            self._instruments_cache = instruments
            self._classify_instruments(instruments)
            logger.info(f"[GrowwData] Loaded {len(instruments)} instruments")
        return self._instruments_cache

    def _classify_instruments(self, instruments: List[Dict]):
        """
        Classify instruments into stocks, options, futures.

        Logic (from Groww instrument master):
          - Stocks (equity): exchange == "NSE" and segment == "CASH"
          - Options: trading_symbol ends with CE or PE
          - Futures: trading_symbol ends with FUT
        """
        self._stocks_cache = []
        self._options_cache = []
        self._futures_cache = []

        option_re = re.compile(r"(CE|PE)$")
        future_re = re.compile(r"FUT$")

        for inst in instruments:
            sym = inst.get("trading_symbol", "") or ""
            exchange = inst.get("exchange", "") or ""
            segment = inst.get("segment", "") or ""

            if option_re.search(sym):
                self._options_cache.append(inst)
            elif future_re.search(sym):
                self._futures_cache.append(inst)
            elif exchange == "NSE" and segment == "CASH":
                self._stocks_cache.append(inst)

        logger.info(
            f"[GrowwData] Classified: {len(self._stocks_cache)} stocks, "
            f"{len(self._options_cache)} options, {len(self._futures_cache)} futures"
        )

    async def get_equity_stocks(self, force_refresh: bool = False) -> List[Dict]:
        """Return only equity stock instruments (no options, no futures)."""
        if not self._stocks_cache or force_refresh:
            await self.get_all_instruments(force_refresh)
        return self._stocks_cache or []

    async def get_option_instruments(self, force_refresh: bool = False) -> List[Dict]:
        """Return only option instruments (CE/PE)."""
        if not self._options_cache or force_refresh:
            await self.get_all_instruments(force_refresh)
        return self._options_cache or []

    async def get_future_instruments(self, force_refresh: bool = False) -> List[Dict]:
        """Return only futures instruments."""
        if not self._futures_cache or force_refresh:
            await self.get_all_instruments(force_refresh)
        return self._futures_cache or []

    async def get_instrument_counts(self) -> Dict:
        """Return counts of each instrument type."""
        await self.get_all_instruments()
        return {
            "total": len(self._instruments_cache or []),
            "stocks": len(self._stocks_cache or []),
            "options": len(self._options_cache or []),
            "futures": len(self._futures_cache or []),
        }

    # ──────────────────────────────────────────────────────────────────
    # 5. OPTION CHAIN
    # ──────────────────────────────────────────────────────────────────
    async def get_option_chain(
        self,
        underlying: str,
        expiry_date: str,
        exchange: str = "NSE",
    ) -> Optional[Dict]:
        """Get options chain for an underlying + expiry."""
        svc = await self._get_service()
        return await svc.get_option_chain(underlying, expiry_date, exchange)

    # ──────────────────────────────────────────────────────────────────
    # 6. OPTION EXPIRIES
    # ──────────────────────────────────────────────────────────────────
    async def get_option_expiries(
        self,
        underlying: str,
        exchange: str = "NSE",
    ) -> Optional[List[str]]:
        """Get available expiry dates for an underlying."""
        svc = await self._get_service()
        result = await svc.get_expiries(underlying, exchange)
        if result:
            return (result or {}).get("data") or (result or {}).get("expiries") or []
        return None

    # ──────────────────────────────────────────────────────────────────
    # 7. OPTION GREEKS
    # ──────────────────────────────────────────────────────────────────
    async def get_option_greeks(
        self,
        underlying: str,
        trading_symbol: str,
        expiry: str,
        exchange: str = "NSE",
    ) -> Optional[Dict]:
        """Get Greeks for a specific option contract."""
        svc = await self._get_service()
        return await svc.get_greeks(underlying, trading_symbol, expiry, exchange)

    # ──────────────────────────────────────────────────────────────────
    # 8. PLACE ORDER (LIVE)
    # ──────────────────────────────────────────────────────────────────
    async def place_order(
        self,
        symbol: str,
        transaction_type: str,
        quantity: int,
        order_type: str = "LIMIT",
        product: str = "CNC",
        price: Optional[float] = None,
        trigger_price: Optional[float] = None,
        exchange: str = "NSE",
    ) -> Optional[Dict]:
        """Place a real order on Groww (LIVE_TRADING_ENABLED must be True)."""
        svc = await self._get_service()
        return await svc.place_order(
            trading_symbol=symbol,
            transaction_type=transaction_type,
            quantity=quantity,
            order_type=order_type,
            product=product,
            price=price,
            trigger_price=trigger_price,
            exchange=exchange,
        )

    # ──────────────────────────────────────────────────────────────────
    # 9. ORDER STATUS
    # ──────────────────────────────────────────────────────────────────
    async def get_order_status(
        self,
        groww_order_id: str,
    ) -> Optional[Dict]:
        """Check status of a placed order."""
        svc = await self._get_service()
        return await svc.get_order_status(groww_order_id)

    # ──────────────────────────────────────────────────────────────────
    # 10. CANCEL ORDER
    # ──────────────────────────────────────────────────────────────────
    async def cancel_order(
        self,
        groww_order_id: str,
    ) -> Optional[Dict]:
        """Cancel an open order."""
        svc = await self._get_service()
        return await svc.cancel_order(groww_order_id)

    # ──────────────────────────────────────────────────────────────────
    # 11. PORTFOLIO HOLDINGS (real Groww account)
    # ──────────────────────────────────────────────────────────────────
    async def get_holdings(self) -> Optional[Dict]:
        """
        Get delivery holdings from Groww account.
        Returns raw SDK response — typically:
        {
          "holdings": [
            {
              "isin": "INE545U01014",
              "trading_symbol": "RELIANCE",
              "quantity": 10,
              "average_price": 100,
              "pledge_quantity": 2,
              "demat_locked_quantity": 1,
              "groww_locked_quantity": 1.5,
              "repledge_quantity": 0.5,
              "t1_quantity": 3,
              "demat_free_quantity": 5,
              "corporate_action_additional_quantity": 1,
              "active_demat_transfer_quantity": 1
            }
          ]
        }
        """
        svc = await self._get_service()
        return await svc.get_holdings()

    # ──────────────────────────────────────────────────────────────────
    # 12. LIVE POSITIONS (intraday / F&O)
    # ──────────────────────────────────────────────────────────────────
    async def get_positions(self, segment: Optional[str] = None) -> Optional[Dict]:
        """Get open intraday/F&O positions."""
        svc = await self._get_service()
        return await svc.get_positions(segment)

    # ──────────────────────────────────────────────────────────────────
    # 13. AVAILABLE MARGIN
    # ──────────────────────────────────────────────────────────────────
    async def get_available_margin(self) -> Optional[Dict]:
        """Get available margin/buying power."""
        svc = await self._get_service()
        return await svc.get_available_margin()

    # ──────────────────────────────────────────────────────────────────
    # 14. ORDER BOOK
    # ──────────────────────────────────────────────────────────────────
    async def get_order_list(self, page: int = 0, page_size: int = 25) -> Optional[Dict]:
        """Get the order book (paginated)."""
        svc = await self._get_service()
        return await svc.get_order_list(page=page, page_size=page_size)

    # ──────────────────────────────────────────────────────────────────
    # 15. LIVE FEED (GrowwFeed WebSocket)
    # ──────────────────────────────────────────────────────────────────
    async def subscribe_live_ltp(
        self,
        instruments: List[Dict],
        on_data_received=None,
    ):
        """
        Subscribe to live LTP for instruments.

        Args:
            instruments: e.g. [{"exchange": "NSE", "segment": "CASH", "exchange_token": "2885"}]
            on_data_received: Optional callback when data arrives
        """
        svc = await self._get_service()
        svc.subscribe_live_ltp(instruments, on_data_received=on_data_received)

    async def unsubscribe_live_ltp(self, instruments: List[Dict]):
        """Unsubscribe from live LTP for instruments."""
        svc = await self._get_service()
        svc.unsubscribe_live_ltp(instruments)

    async def get_live_ltp(self) -> Optional[Dict]:
        """
        Poll latest live LTP data.

        Returns:
            dict e.g.
            {"ltp": {"NSE": {"CASH": {"2885": {"tsInMillis": ..., "ltp": 1419.1}}}}}
        """
        svc = await self._get_service()
        return svc.get_live_ltp()

    async def start_live_feed(self):
        """Start the live feed consumer in a background thread."""
        svc = await self._get_service()
        await svc.start_live_feed()

    async def stop_live_feed(self):
        """Stop the live feed."""
        svc = await self._get_service()
        svc.stop_live_feed()

    # ──────────────────────────────────────────────────────────────────
    # 16. LIVE INDEX VALUES (GrowwFeed WebSocket)
    # ──────────────────────────────────────────────────────────────────
    async def subscribe_live_index_value(
        self,
        instruments: List[Dict],
        on_data_received=None,
    ):
        """
        Subscribe to live index values.

        Args:
            instruments: e.g. [{"exchange": "NSE", "segment": "CASH", "exchange_token": "NIFTY"}]
            on_data_received: Optional callback when data arrives
        """
        svc = await self._get_service()
        svc.subscribe_live_index_value(instruments, on_data_received=on_data_received)

    async def unsubscribe_live_index_value(self, instruments: List[Dict]):
        """Unsubscribe from live index values."""
        svc = await self._get_service()
        svc.unsubscribe_live_index_value(instruments)

    async def get_live_index_value(self) -> Optional[Dict]:
        """
        Poll latest live index values.

        Returns:
            dict e.g.
            {"NSE": {"CASH": {"NIFTY": {"tsInMillis": ..., "value": 24386.7}}}}
        """
        svc = await self._get_service()
        return svc.get_live_index_value()

    # ──────────────────────────────────────────────────────────────────
    # 17. FNO ORDER UPDATES (GrowwFeed WebSocket)
    # ──────────────────────────────────────────────────────────────────
    async def subscribe_fno_order_updates(self, on_data_received=None):
        """
        Subscribe to derivative (FNO) order updates.

        Args:
            on_data_received: Optional callback when an order update arrives
        """
        svc = await self._get_service()
        svc.subscribe_fno_order_updates(on_data_received=on_data_received)

    async def unsubscribe_fno_order_updates(self):
        """Unsubscribe from FNO order updates."""
        svc = await self._get_service()
        svc.unsubscribe_fno_order_updates()

    async def get_fno_order_update(self) -> Optional[Dict]:
        """
        Poll latest FNO order update.

        Returns:
            dict e.g.
            {"qty": 75, "price": "130", "filledQty": 75, "avgFillPrice": "110",
             "growwOrderId": "...", "orderStatus": "EXECUTED", ...}
        """
        svc = await self._get_service()
        return svc.get_fno_order_update()

    # ──────────────────────────────────────────────────────────────────
    # 18. EQUITY ORDER UPDATES (GrowwFeed WebSocket)
    # ──────────────────────────────────────────────────────────────────
    async def subscribe_equity_order_updates(self, on_data_received=None):
        """
        Subscribe to equity (CASH segment) order updates.

        Args:
            on_data_received: Optional callback when an order update arrives
        """
        svc = await self._get_service()
        svc.subscribe_equity_order_updates(on_data_received=on_data_received)

    async def unsubscribe_equity_order_updates(self):
        """Unsubscribe from equity order updates."""
        svc = await self._get_service()
        svc.unsubscribe_equity_order_updates()

    async def get_equity_order_update(self) -> Optional[Dict]:
        """
        Poll latest equity order update.

        Returns:
            dict e.g.
            {"qty": 3, "filledQty": 3, "avgFillPrice": "145",
             "growwOrderId": "...", "orderStatus": "EXECUTED", ...}
        """
        svc = await self._get_service()
        return svc.get_equity_order_update()


# Module-level singleton
groww_data = GrowwDataInterface()

