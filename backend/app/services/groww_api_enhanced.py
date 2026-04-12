"""
Enhanced Groww API Client for real market data integration
"""
import aiohttp
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import json
from app.core.config import settings

logger = logging.getLogger(__name__)

class GrowwAPIClient:
    """Real-time Groww API integration"""
    
    def __init__(self):
        self.base_url = settings.GROWW_API_BASE_URL
        self.api_key = settings.GROWW_API_KEY
        self.api_secret = settings.GROWW_API_SECRET
        self.auth_token = settings.GROWW_AUTH_TOKEN
        self.session = None
        
    async def initialize(self):
        """Initialize HTTP session"""
        self.session = aiohttp.ClientSession()
    
    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
    
    def _get_headers(self) -> Dict:
        """Get authorization headers"""
        return {
            "Authorization": f"Bearer {self.auth_token}",
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
    
    # ============ MARKET DATA ============
    
    async def get_stock_quote(self, symbol: str) -> Optional[Dict]:
        """
        Fetch real-time quote for a stock
        
        Returns: {
            "symbol": "NSE.RELIANCE",
            "name": "RELIANCE INDUSTRIES LIMITED",
            "price": 2850.50,
            "change": 25.50,
            "change_percent": 0.90,
            "bid": 2850.00,
            "ask": 2851.00,
            "volume": 5000000,
            "market_cap": 2500000000000,
            "52_week_high": 3500.00,
            "52_week_low": 2200.00,
            "pe_ratio": 25.5,
            "dividend_yield": 2.1,
            "timestamp": "2026-04-12T14:30:00Z"
        }
        """
        try:
            if not self.session:
                await self.initialize()
            
            url = f"{self.base_url}/quote/{symbol}"
            async with self.session.get(url, headers=self._get_headers()) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Fetched quote for {symbol}: ₹{data.get('price')}")
                    return data
                else:
                    logger.warning(f"Failed to fetch quote for {symbol}: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching quote for {symbol}: {e}")
            return None
    
    async def get_historical_data(
        self, 
        symbol: str, 
        days: int = 365,
        interval: str = "1d"
    ) -> Optional[List[Dict]]:
        """
        Fetch historical OHLCV data
        
        Args:
            symbol: Stock symbol (e.g., "NSE.RELIANCE")
            days: Number of days of historical data (1-365)
            interval: "1m", "5m", "15m", "1h", "1d"
        
        Returns: List of {
            "timestamp": "2026-04-12T00:00:00Z",
            "open": 2825.00,
            "high": 2850.50,
            "low": 2820.00,
            "close": 2850.00,
            "volume": 5000000,
            "vwap": 2836.25
        }
        """
        try:
            if not self.session:
                await self.initialize()
            
            params = {
                "interval": interval,
                "days": min(days, 365)  # Max 365 days
            }
            
            url = f"{self.base_url}/historical/{symbol}"
            async with self.session.get(url, params=params, headers=self._get_headers()) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Fetched {len(data)} candles for {symbol}")
                    return data
                else:
                    logger.warning(f"Failed to fetch historical data: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return None
    
    async def get_intraday_data(
        self, 
        symbol: str, 
        minutes: int = 1
    ) -> Optional[List[Dict]]:
        """
        Fetch intraday minute data
        
        Args:
            symbol: Stock symbol
            minutes: Minutes interval (1, 5, 15, 30, 60)
        """
        return await self.get_historical_data(symbol, days=1, interval=f"{minutes}m")
    
    # ============ OPTIONS DATA ============
    
    async def get_options_chain(self, symbol: str) -> Optional[List[Dict]]:
        """
        Fetch options chain for a stock
        
        Returns: List of {
            "symbol": "RELIANCE",
            "strike": 2850,
            "expiry": "2026-04-16",
            "call": {
                "symbol": "RELIANCE_CE_2850",
                "bid": 45.50,
                "ask": 46.00,
                "last_price": 45.75,
                "volume": 1000000,
                "open_interest": 500000,
                "iv": 25.5,
                "delta": 0.65,
                "gamma": 0.002,
                "theta": -0.15,
                "vega": 0.45
            },
            "put": {
                "symbol": "RELIANCE_PE_2850",
                ...
            }
        }
        """
        try:
            if not self.session:
                await self.initialize()
            
            url = f"{self.base_url}/options/chain/{symbol}"
            async with self.session.get(url, headers=self._get_headers()) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Fetched options chain for {symbol}: {len(data)} strikes")
                    return data
                else:
                    logger.warning(f"Failed to fetch options chain: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching options chain for {symbol}: {e}")
            return None
    
    async def get_options_greeks(self, symbol: str, strike: float, expiry: str) -> Optional[Dict]:
        """
        Get Greeks (delta, gamma, theta, vega) for an option
        """
        try:
            if not self.session:
                await self.initialize()
            
            url = f"{self.base_url}/options/greeks"
            params = {
                "symbol": symbol,
                "strike": strike,
                "expiry": expiry
            }
            
            async with self.session.get(url, params=params, headers=self._get_headers()) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.warning("Failed to fetch Greeks")
                    return None
        except Exception as e:
            logger.error(f"Error fetching Greeks: {e}")
            return None
    
    # ============ MUTUAL FUNDS ============
    
    async def get_mutual_funds(self) -> Optional[List[Dict]]:
        """
        Fetch all available mutual funds with ratings and returns
        
        Returns: List of {
            "fund_code": "AXISBLUEQ",
            "fund_name": "Axis Bluechip Fund",
            "category": "Large Cap",
            "nav": 145.50,
            "aum": 50000000000,
            "expense_ratio": 0.58,
            "risk_rating": 3,  # 1-5 stars
            "returns_1y": 12.5,
            "returns_3y": 14.2,
            "returns_5y": 15.8,
            "rating": 5,  # Fund rating
            "last_updated": "2026-04-12T15:30:00Z"
        }
        """
        try:
            if not self.session:
                await self.initialize()
            
            url = f"{self.base_url}/mutual-funds"
            async with self.session.get(url, headers=self._get_headers()) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Fetched {len(data)} mutual funds")
                    return data
                else:
                    logger.warning(f"Failed to fetch mutual funds: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching mutual funds: {e}")
            return None
    
    async def search_mutual_funds(self, query: str) -> Optional[List[Dict]]:
        """Search for mutual funds by name or category"""
        try:
            if not self.session:
                await self.initialize()
            
            url = f"{self.base_url}/mutual-funds/search"
            params = {"q": query}
            
            async with self.session.get(url, params=params, headers=self._get_headers()) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return None
        except Exception as e:
            logger.error(f"Error searching mutual funds: {e}")
            return None
    
    # ============ MARKET ANALYSIS ============
    
    async def get_trending_stocks(self, limit: int = 10) -> Optional[List[Dict]]:
        """
        Get trending stocks by volume and momentum
        
        Returns: List of {
            "symbol": "NSE.RELIANCE",
            "name": "RELIANCE INDUSTRIES",
            "price": 2850.50,
            "change_percent": 2.5,
            "volume": 5000000,
            "trend_strength": 0.85,
            "reason": "Volume breakout, bullish setup"
        }
        """
        try:
            if not self.session:
                await self.initialize()
            
            url = f"{self.base_url}/trends/stocks"
            params = {"limit": limit}
            
            async with self.session.get(url, params=params, headers=self._get_headers()) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return None
        except Exception as e:
            logger.error(f"Error fetching trending stocks: {e}")
            return None
    
    async def get_market_breadth(self) -> Optional[Dict]:
        """
        Get market breadth data (advances, declines, etc.)
        
        Returns: {
            "advances": 1500,
            "declines": 800,
            "unchanged": 200,
            "advance_decline_ratio": 1.875,
            "market_sentiment": "BULLISH",
            "vix": 15.5
        }
        """
        try:
            if not self.session:
                await self.initialize()
            
            url = f"{self.base_url}/market/breadth"
            async with self.session.get(url, headers=self._get_headers()) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return None
        except Exception as e:
            logger.error(f"Error fetching market breadth: {e}")
            return None
    
    # ============ PORTFOLIO & EXECUTION ============
    
    async def get_portfolio(self) -> Optional[Dict]:
        """Get current portfolio holdings and cash"""
        try:
            if not self.session:
                await self.initialize()
            
            url = f"{self.base_url}/portfolio"
            async with self.session.get(url, headers=self._get_headers()) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return None
        except Exception as e:
            logger.error(f"Error fetching portfolio: {e}")
            return None
    
    async def place_order(
        self,
        symbol: str,
        action: str,  # BUY/SELL
        quantity: int,
        order_type: str = "MARKET",  # MARKET/LIMIT
        price: Optional[float] = None
    ) -> Optional[Dict]:
        """
        Place a stock trading order
        
        Returns: {
            "order_id": "12345",
            "status": "EXECUTED",
            "symbol": "NSE.RELIANCE",
            "action": "BUY",
            "quantity": 10,
            "execution_price": 2850.50,
            "timestamp": "2026-04-12T14:30:00Z"
        }
        """
        try:
            if not self.session:
                await self.initialize()
            
            # LIVE TRADING ONLY - This requires real Groww integration
            if not settings.LIVE_TRADING_ENABLED:
                logger.warning("Live trading is disabled")
                return None
            
            url = f"{self.base_url}/orders/place"
            payload = {
                "symbol": symbol,
                "action": action,
                "quantity": quantity,
                "order_type": order_type,
                "price": price
            }
            
            async with self.session.post(url, json=payload, headers=self._get_headers()) as response:
                if response.status in (200, 201):
                    return await response.json()
                else:
                    logger.error(f"Order placement failed: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return None
    
    async def place_options_order(
        self,
        contract_symbol: str,
        action: str,  # BUY/SELL
        quantity: int,
        order_type: str = "MARKET",
        price: Optional[float] = None
    ) -> Optional[Dict]:
        """
        Place an options trading order
        
        Args:
            contract_symbol: e.g., "RELIANCE_CE_2850" (Call) or "RELIANCE_PE_2850" (Put)
        """
        try:
            if not self.session:
                await self.initialize()
            
            if not settings.LIVE_TRADING_ENABLED:
                logger.warning("Live trading is disabled")
                return None
            
            url = f"{self.base_url}/options/place"
            payload = {
                "contract_symbol": contract_symbol,
                "action": action,
                "quantity": quantity,
                "order_type": order_type,
                "price": price
            }
            
            async with self.session.post(url, json=payload, headers=self._get_headers()) as response:
                if response.status in (200, 201):
                    return await response.json()
                else:
                    logger.error(f"Options order placement failed: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error placing options order: {e}")
            return None
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an open order"""
        try:
            if not self.session:
                await self.initialize()
            
            url = f"{self.base_url}/orders/{order_id}/cancel"
            async with self.session.post(url, headers=self._get_headers()) as response:
                return response.status in (200, 204)
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            return False

# Global client instance
groww_client: Optional[GrowwAPIClient] = None

async def get_groww_client() -> GrowwAPIClient:
    """Get or create Groww API client"""
    global groww_client
    if not groww_client:
        groww_client = GrowwAPIClient()
        await groww_client.initialize()
    return groww_client

async def close_groww_client():
    """Close Groww client"""
    global groww_client
    if groww_client:
        await groww_client.close()
