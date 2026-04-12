import aiohttp
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class GrowwAPIClient:
    """Client for Groww API integration"""
    
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def connect(self):
        """Initialize HTTP session"""
        self.session = aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
    
    async def disconnect(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
    
    async def get_stock_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch current stock quote"""
        try:
            if not self.session:
                await self.connect()
            
            url = f"{self.base_url}/quotes/{symbol}"
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    return await resp.json()
                logger.error(f"Failed to fetch quote for {symbol}: {resp.status}")
                return None
        except Exception as e:
            logger.error(f"Error fetching stock quote: {e}")
            return None
    
    async def get_historical_data(
        self, symbol: str, period: str = "1y", interval: str = "1d"
    ) -> Optional[List[Dict[str, Any]]]:
        """Fetch historical data for technical analysis"""
        try:
            if not self.session:
                await self.connect()
            
            url = f"{self.base_url}/historical/{symbol}"
            params = {"period": period, "interval": interval}
            async with self.session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    return await resp.json()
                logger.error(f"Failed to fetch historical data for {symbol}: {resp.status}")
                return None
        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")
            return None
    
    async def buy_stock(
        self, symbol: str, quantity: int, price: float
    ) -> Optional[Dict[str, Any]]:
        """Place a buy order"""
        try:
            if not self.session:
                await self.connect()
            
            url = f"{self.base_url}/orders"
            payload = {
                "symbol": symbol,
                "quantity": quantity,
                "price": price,
                "order_type": "LIMIT",
                "side": "BUY",
                "timestamp": datetime.now().isoformat()
            }
            
            async with self.session.post(
                url, json=payload, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 201:
                    return await resp.json()
                logger.error(f"Failed to place buy order: {resp.status}")
                return None
        except Exception as e:
            logger.error(f"Error placing buy order: {e}")
            return None
    
    async def sell_stock(
        self, symbol: str, quantity: int, price: float
    ) -> Optional[Dict[str, Any]]:
        """Place a sell order"""
        try:
            if not self.session:
                await self.connect()
            
            url = f"{self.base_url}/orders"
            payload = {
                "symbol": symbol,
                "quantity": quantity,
                "price": price,
                "order_type": "LIMIT",
                "side": "SELL",
                "timestamp": datetime.now().isoformat()
            }
            
            async with self.session.post(
                url, json=payload, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 201:
                    return await resp.json()
                logger.error(f"Failed to place sell order: {resp.status}")
                return None
        except Exception as e:
            logger.error(f"Error placing sell order: {e}")
            return None
    
    async def get_portfolio(self) -> Optional[Dict[str, Any]]:
        """Fetch current portfolio"""
        try:
            if not self.session:
                await self.connect()
            
            url = f"{self.base_url}/portfolio"
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    return await resp.json()
                logger.error(f"Failed to fetch portfolio: {resp.status}")
                return None
        except Exception as e:
            logger.error(f"Error fetching portfolio: {e}")
            return None
    
    async def get_account_balance(self) -> Optional[float]:
        """Get current account balance"""
        try:
            if not self.session:
                await self.connect()
            
            url = f"{self.base_url}/account/balance"
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("balance")
                logger.error(f"Failed to fetch account balance: {resp.status}")
                return None
        except Exception as e:
            logger.error(f"Error fetching account balance: {e}")
            return None
