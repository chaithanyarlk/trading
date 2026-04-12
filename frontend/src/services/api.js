import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const tradingAPI = {
  // Signals
  generateSignals: (marketData) =>
    api.post('/api/signals/generate', marketData),
  
  // Portfolio
  getPortfolio: () => api.get('/api/portfolio'),
  getPerformance: () => api.get('/api/performance'),
  
  // Trades
  executeTrade: (signal, quantity) =>
    api.post('/api/trades/execute', { signal, quantity }),
  getTrades: () => api.get('/api/trades'),
  
  // Options
  getOptionsSuggestions: (underlying, currentPrice) =>
    api.get('/api/options/suggestions', {
      params: { underlying, current_price: currentPrice },
    }),
  
  // Mutual Funds
  getMutualFundRecommendations: () =>
    api.get('/api/mutual-funds/recommendations'),
  
  // Market
  getStocksToWatch: () => api.get('/api/stocks/watch'),
  getMarketQuote: (symbol) =>
    api.get('/api/market/quote', { params: { symbol } }),
  getHistoricalData: (symbol, period = '1y', interval = '1d') =>
    api.get('/api/market/historical', {
      params: { symbol, period, interval },
    }),
  
  // Trading Mode
  setTradingMode: (liveMode) =>
    api.post('/api/trading/mode', { live_mode: liveMode }),
  
  // Health
  healthCheck: () => api.get('/health'),
};

// WebSocket service
export const createTradeStreamConnection = (onMessage, onError) => {
  const wsUrl = `${API_BASE_URL.replace('http', 'ws')}/ws/trades`;
  const ws = new WebSocket(wsUrl);
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    onMessage(data);
  };
  
  ws.onerror = (error) => {
    onError(error);
  };
  
  return ws;
};

export default api;
