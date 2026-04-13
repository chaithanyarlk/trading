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

  // ═══════════════════════════════════════════════════════════════
  //  MULTI-AGENT SYSTEM
  // ═══════════════════════════════════════════════════════════════

  // Paper Trading Config (from UI)
  configurePaperTrading: (config) =>
    api.post('/api/agents/config', config),
  getPaperTradingConfig: () =>
    api.get('/api/agents/config'),

  // Multi-Agent Analysis
  runAgentPipeline: (symbols, config, autoExecute = false) =>
    api.post('/api/agents/analyze', {
      symbols,
      config,
      auto_execute: autoExecute,
    }),
  analyzeSingleSymbol: (symbol, config) =>
    api.post(`/api/agents/analyze/${symbol}`, config),

  // Agent Execution
  executeDecision: (decision) =>
    api.post('/api/agents/execute', decision),

  // Agent Portfolio & Performance
  getAgentPortfolio: () => api.get('/api/agents/portfolio'),
  getAgentPerformance: () => api.get('/api/agents/performance'),
  getAgentTrades: () => api.get('/api/agents/trades'),
  getDecisionHistory: () => api.get('/api/agents/decisions/history'),

  // Agent Market Data
  getAgentQuote: (symbol) => api.get(`/api/agents/market/quote/${symbol}`),
  getAgentLtp: (symbol) => api.get(`/api/agents/market/ltp/${symbol}`),
  getAgentHistorical: (symbol, interval = '1day', days = 365) =>
    api.get(`/api/agents/market/historical/${symbol}`, { params: { interval, days } }),

  // Instruments (stocks / options / futures classification)
  getInstrumentCounts: () => api.get('/api/agents/instruments/all'),
  getStockInstruments: (search = '', limit = 100) =>
    api.get('/api/agents/instruments/stocks', { params: { search, limit } }),
  getOptionInstruments: (underlying = '', limit = 100) =>
    api.get('/api/agents/instruments/options', { params: { underlying, limit } }),
  getFutureInstruments: (limit = 100) =>
    api.get('/api/agents/instruments/futures', { params: { limit } }),

  // Real Groww Portfolio
  getGrowwHoldings: () => api.get('/api/agents/groww-portfolio/holdings'),
  getGrowwPositions: (segment = '') =>
    api.get('/api/agents/groww-portfolio/positions', { params: { segment } }),
  getGrowwMargin: () => api.get('/api/agents/groww-portfolio/margin'),
  getGrowwOrders: (page = 0) =>
    api.get('/api/agents/groww-portfolio/orders', { params: { page } }),

  // Potential Buys (with support, stop loss, exit price)
  getPotentialBuys: (config) =>
    api.post('/api/agents/potential-buys', config),

  // Auto Scheduler
  getSchedulerStatus: () => api.get('/api/agents/scheduler/status'),
  startScheduler: (interval = 15) =>
    api.post('/api/agents/scheduler/start', null, { params: { scan_interval_minutes: interval } }),
  stopScheduler: () => api.post('/api/agents/scheduler/stop'),
  triggerScanNow: () => api.post('/api/agents/scheduler/scan-now'),

  // Today's Activity
  getTodaysDecisions: () => api.get('/api/agents/today/decisions'),
  getTodaysExecutions: () => api.get('/api/agents/today/executions'),

  // EOD Report
  getEodReport: () => api.get('/api/agents/report/eod'),
  generateEodReportNow: () => api.post('/api/agents/report/generate-now'),
};

// WebSocket service (old trade stream)
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

// Agent WebSocket — receives real-time scan results, trade executions, EOD reports
export const createAgentWebSocket = (onScanComplete, onEodReport, onError) => {
  const wsUrl = `${API_BASE_URL.replace('http', 'ws')}/api/agents/ws`;
  const ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    console.log('[AgentWS] Connected');
  };

  ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data);
      if (msg.type === 'scan_complete') {
        onScanComplete(msg.data);
      } else if (msg.type === 'eod_report') {
        onEodReport(msg.data);
      } else if (msg.type === 'scan_error') {
        onError(msg.data);
      }
    } catch (e) {
      console.error('[AgentWS] Parse error:', e);
    }
  };

  ws.onerror = (error) => {
    console.error('[AgentWS] Error:', error);
    if (onError) onError({ error: 'WebSocket connection error' });
  };

  ws.onclose = () => {
    console.log('[AgentWS] Disconnected — will try to reconnect in 5s');
    setTimeout(() => {
      createAgentWebSocket(onScanComplete, onEodReport, onError);
    }, 5000);
  };

  return ws;
};

export default api;
