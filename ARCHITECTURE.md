# System Architecture - AI Trading Assistant

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     React Dashboard (Frontend)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │Portfolio View│  │Trade Feed    │  │Metrics Panel │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │Charts        │  │Modals        │  │Suggestions   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                            ↕
                   REST API + WebSocket
                            ↕
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend Server                        │
│  ┌────────────────────────────────────────────────────────┐    │
│  │              API Routes Layer                           │    │
│  │  /api/signals  /api/trades  /api/portfolio  /ws/trades │    │
│  └────────────────────────────────────────────────────────┘    │
│  ┌────────────────────────────────────────────────────────┐    │
│  │            Trading Engine Core                          │    │
│  │  ┌─────────────────────────────────────────────┐      │    │
│  │  │ Technical Analysis Engine                   │      │    │
│  │  │ • RSI Calculation                           │      │    │
│  │  │ • MACD Analysis                             │      │    │
│  │  │ • Bollinger Bands                           │      │    │
│  │  │ • Moving Averages                           │      │    │
│  │  │ • Volume Analysis                           │      │    │
│  │  │ • Signal Generation & Aggregation           │      │    │
│  │  └─────────────────────────────────────────────┘      │    │
│  │  ┌─────────────────────────────────────────────┐      │    │
│  │  │ Trading Engine                              │      │    │
│  │  │ • Signal Filtering                          │      │    │
│  │  │ • Risk Assessment                           │      │    │
│  │  │ • Position Sizing                           │      │    │
│  │  │ • Trade Recommendations                     │      │    │
│  │  │ • Options Strategies                        │      │    │
│  │  │ • Mutual Fund Selection                     │      │    │
│  │  └─────────────────────────────────────────────┘      │    │
│  │  ┌─────────────────────────────────────────────┐      │    │
│  │  │ Paper Trading Simulator                     │      │    │
│  │  │ • Portfolio Management                      │      │    │
│  │  │ • Trade Execution (Paper)                   │      │    │
│  │  │ • P&L Calculation                           │      │    │
│  │  │ • Performance Metrics                       │      │    │
│  │  └─────────────────────────────────────────────┘      │    │
│  │  ┌─────────────────────────────────────────────┐      │    │
│  │  │ Groww API Integration                       │      │    │
│  │  │ • Live Quote Fetching                       │      │    │
│  │  │ • Order Execution                           │      │    │
│  │  │ • Portfolio Sync                            │      │    │
│  │  │ • Account Balance                           │      │    │
│  │  └─────────────────────────────────────────────┘      │    │
│  └────────────────────────────────────────────────────────┘    │
│  ┌────────────────────────────────────────────────────────┐    │
│  │         Data Models & Configuration                    │    │
│  │  • Pydantic Schemas                                    │    │
│  │  • Configuration Management                           │    │
│  │  • Environment Variables                              │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                            ↕
    ┌────────────────┬──────────────┬────────────────┐
    ↓                ↓              ↓                ↓
┌─────────┐    ┌─────────┐   ┌──────────┐    ┌─────────────┐
│ Groww   │    │Database │   │ Market   │    │ Logs &      │
│ API     │    │(SQLite/ │   │ Data     │    │ Audit Trail │
│         │    │ Postgres)   │           │    │             │
└─────────┘    └─────────┘   └──────────┘    └─────────────┘
```

---

## 📊 Data Flow Diagram

```
┌──────────────────┐
│  Market Data     │
│  (Stock Prices)  │
└─────────┬────────┘
          │
          ↓
┌──────────────────────────────────┐
│ Technical Analysis Engine        │
│ • Calculate RSI, MACD, Bands     │
│ • Analyze volume                 │
│ • Generate indicator signals     │
└──────────┬───────────────────────┘
           │
           ↓
┌──────────────────────────────────┐
│ Signal Aggregation               │
│ • Combine all indicators         │
│ • Calculate confidence           │
│ • Determine risk level           │
│ • Generate reasoning             │
└──────────┬───────────────────────┘
           │
           ↓
┌──────────────────────────────────┐
│ Trade Signal                     │
│ (BUY/SELL, Price, Confidence)    │
└──────────┬───────────────────────┘
           │
    ┌──────┴──────┐
    │             │
    ↓             ↓
┌──────────┐  ┌────────────────────┐
│ Broadcast│  │ User Review &      │
│ to UI    │  │ Approval           │
│ (WebSocket)  │ (Paper/Live Mode)  │
└────┬─────┘  └────────┬───────────┘
     │                 │
     │                 ↓
     │         ┌──────────────────────┐
     │         │ Trade Execution      │
     │         │ • Update Portfolio   │
     │         │ • Calculate P&L      │
     │         │ • Log Trade          │
     │         └──────────┬───────────┘
     │                    │
     │                    ↓
     │         ┌──────────────────────┐
     │         │ Performance Metrics   │
     │         │ • Win Rate           │
     │         │ • ROI                │
     │         │ • Sharpe Ratio       │
     │         └──────────┬───────────┘
     │                    │
     └────────┬───────────┘
              │
              ↓
     ┌──────────────────┐
     │ UI Update        │
     │ Dashboard        │
     │ Refresh          │
     └──────────────────┘
```

---

## 🔄 Component Interaction

### 1. **Frontend (React)**

```javascript
App.jsx
├── Dashboard Components
│   ├── TradeFeed (real-time trade stream)
│   ├── PortfolioOverview (holdings & P&L)
│   ├── PerformanceDashboard (metrics)
│   ├── TradingModeToggle (paper/live)
│   └── ReasoningPanel (trade explanation)
├── Charts Components
│   ├── EquityCurve (portfolio value over time)
│   ├── TradeDistribution (wins vs losses)
│   └── PortfolioAllocation (asset breakdown)
├── Modal Components
│   ├── OptionsSuggestionsModal
│   ├── MutualFundsModal
│   └── StocksToWatchModal
└── Services
    └── api.js (REST API client + WebSocket)
```

### 2. **Backend (FastAPI)**

```python
main.py (FastAPI App)
├── API Routes (app/api/routes.py)
│   ├── /api/signals/generate
│   ├── /api/trades/execute
│   ├── /api/portfolio
│   ├── /api/performance
│   ├── /api/options/suggestions
│   ├── /api/mutual-funds/recommendations
│   ├── /api/stocks/watch
│   ├── /api/market/quote
│   ├── /api/market/historical
│   ├── /api/trading/mode
│   └── /ws/trades (WebSocket)
│
├── Services (app/services/)
│   ├── TechnicalAnalysisEngine
│   │   ├── calculate_rsi()
│   │   ├── calculate_macd()
│   │   ├── calculate_bollinger_bands()
│   │   ├── calculate_moving_average_signal()
│   │   ├── calculate_volume_trend()
│   │   └── generate_trade_signal()
│   │
│   ├── TradingEngine
│   │   ├── generate_trade_signals()
│   │   ├── generate_options_suggestions()
│   │   ├── generate_mutual_fund_recommendations()
│   │   ├── get_stocks_to_watch()
│   │   └── apply_risk_management()
│   │
│   ├── PaperTradingSimulator
│   │   ├── execute_trade()
│   │   ├── _execute_buy()
│   │   ├── _execute_sell()
│   │   ├── get_portfolio_overview()
│   │   └── get_performance_metrics()
│   │
│   └── GrowwAPIClient
│       ├── get_stock_quote()
│       ├── get_historical_data()
│       ├── buy_stock()
│       ├── sell_stock()
│       └── get_portfolio()
│
├── Models (app/models/schemas.py)
│   ├── TradeSignal
│   ├── Trade
│   ├── PortfolioOverview
│   ├── PerformanceMetrics
│   ├── OptionsStrategy
│   └── MutualFundRecommendation
│
└── Core (app/core/config.py)
    └── Configuration Management
```

### 3. **Database Layer**

```
SQLite Database (trading_system.db)
├── trades (table)
│   ├── id
│   ├── asset_id
│   ├── asset_name
│   ├── action (BUY/SELL)
│   ├── entry_price
│   ├── quantity
│   ├── timestamp
│   ├── status
│   └── reasoning
│
├── portfolio_snapshots (table)
│   ├── timestamp
│   ├── total_value
│   ├── cash_balance
│   └── holdings (JSON)
│
└── performance_history (table)
    ├── date
    ├── cumulative_profit
    ├── win_rate
    └── roi
```

---

## 🔐 Security Architecture

```
┌─────────────────────────────────────────┐
│        Frontend Security                 │
│  • HTTPS only in production              │
│  • CSRF token validation                 │
│  • Input sanitization                    │
│  • Rate limiting                         │
└──────────────┬──────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────┐
│        API Security                      │
│  • CORS configuration                    │
│  • JWT authentication (future)           │
│  • Request validation                    │
│  • Error handling                        │
└──────────────┬──────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────┐
│      Trading Safety Layer                │
│  • Position sizing enforcement           │
│  • Stop-loss protection                  │
│  • Risk warnings                         │
│  • Manual approval for live trades       │
│  • Comprehensive logging                 │
└──────────────┬──────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────┐
│      API Integration Security            │
│  • Encrypted API keys                    │
│  • Timeout protection (10s)              │
│  • Error handling                        │
│  • Retry logic with exponential backoff  │
└─────────────────────────────────────────┘
```

---

## 📈 Trading Workflow

```
Step 1: Data Acquisition
├── Market data from Groww/broker API
├── Historical prices fetched
└── Volume data collected

Step 2: Technical Analysis
├── Calculate RSI (14-period)
├── Calculate MACD (12,26,9)
├── Calculate Bollinger Bands (20,2)
├── Calculate Moving Averages (20,50)
├── Analyze Volume Trends
└── Generate individual signals

Step 3: Signal Aggregation
├── Count bullish indicators
├── Count bearish indicators
├── Calculate consensus confidence
├── Determine risk level (LOW/MEDIUM/HIGH)
└── Generate trade reasoning

Step 4: Risk Management
├── Calculate max position size (10% of portfolio)
├── Determine stop-loss level (2% below entry)
├── Calculate risk-reward ratio
└── Approve/reject based on risk limits

Step 5: Trade Decision
├── IF paper mode → execute immediately
├── IF live mode → wait for user approval
├── Log decision with full reasoning
└── Broadcast via WebSocket to UI

Step 6: Execution
├── Update portfolio (add/reduce positions)
├── Calculate P&L
├── Update average cost tracking
├── Log trade with timestamp

Step 7: Monitoring
├── Track portfolio value
├── Calculate performance metrics
├── Update equity curve
├── Monitor for stop-loss hits
└── Prepare next signal

Step 8: Feedback Loop
├── Store trade outcome
├── Update win/loss tracking
├── Calculate ROI
├── Learn from results (future: ML model)
└── Adjust strategy parameters
```

---

## 🎯 Technical Analysis Strategy

### Multi-Indicator Approach

```
Market Data (Prices + Volumes)
        │
        ├─→ RSI (14)         → Signal: BUY/SELL/NEUTRAL (Confidence: 0.8)
        │
        ├─→ MACD (12,26,9)   → Signal: BUY/SELL/NEUTRAL (Confidence: 0.75)
        │
        ├─→ Bollinger Bands  → Signal: BUY/SELL/NEUTRAL (Confidence: 0.7)
        │
        ├─→ MA Crossover     → Signal: BUY/SELL/NEUTRAL (Confidence: 0.75)
        │
        └─→ Volume Analysis  → Signal: BUY/SELL/NEUTRAL (Confidence: 0.6)
        
        │
        └─→ Aggregate Signals
            • Count BUY signals
            • Count SELL signals
            • Calculate final confidence
            • Determine risk level
            
            Final Signal: BUY/SELL with X% confidence (LOW/MEDIUM/HIGH risk)
```

### Confidence Calculation

```
IF buy_signals > sell_signals:
    confidence = (buy_signals / total_signals) * 100
    action = BUY
ELIF sell_signals > buy_signals:
    confidence = (sell_signals / total_signals) * 100
    action = SELL
ELSE:
    confidence = 50%
    action = NEUTRAL

Risk Level:
    IF confidence >= 80% → LOW RISK
    IF confidence >= 60% → MEDIUM RISK
    IF confidence < 60%  → HIGH RISK
```

---

## 🚀 Deployment Architecture

### Development
```
Local Machine
├── Backend: python main.py (port 8000)
├── Frontend: npm start (port 3000)
└── Database: SQLite (local)
```

### Production (Docker)
```
Docker Host
├── Backend Container
│   ├── FastAPI App
│   ├── Python dependencies
│   └── Database (mounted volume)
├── Frontend Container
│   ├── React build (static)
│   └── Nginx server
└── Reverse Proxy (Nginx)
    ├── HTTPS/TLS
    ├── Load balancing
    └── CORS headers
```

### Scaling
```
Load Balancer
├── Backend Instance 1
├── Backend Instance 2
├── Backend Instance 3
│   └── Shared Database (PostgreSQL)
│       └── Read Replicas
└── Frontend CDN
    └── Static Assets (S3/CloudFront)
```

---

## 📊 Performance Considerations

### Optimization Strategies

1. **Frontend**
   - Lazy loading of components
   - React.memo for chart components
   - Virtual scrolling for trade feed
   - WebSocket for real-time updates

2. **Backend**
   - Technical analysis cached for 1min
   - Portfolio calculations optimized
   - Database indexing on timestamps
   - Async API calls with aiohttp

3. **Database**
   - Composite indexes on (timestamp, asset)
   - Time-series retention policy
   - Aggregated metrics table
   - Archive old trades

---

## 🔄 State Management

### Frontend State (React Context)

```javascript
TradingContext
├── Portfolio state
├── Trades history
├── Performance metrics
├── Current signals
├── UI preferences
└── Settings
```

### Backend State (In-Memory)

```python
Global State
├── Trading engine instance
├── Paper trader simulator
├── Groww API client
├── Configuration
└── Connected WebSocket clients
```

---

## 🧪 Testing Architecture

```
Unit Tests
├── Technical analysis functions
├── Trade execution logic
├── Portfolio calculations
└── Risk management rules

Integration Tests
├── API endpoints
├── Database operations
├── Signal generation flow
└── External API calls (mocked)

E2E Tests
├── User workflows (UI)
├── Trade execution (full flow)
├── Data consistency
└── Performance benchmarks
```

---

## 📚 Data Models

### TradeSignal
```
{
  asset_id, asset_name, asset_type,
  action (BUY/SELL),
  price, confidence,
  indicators (RSI, MACD, etc.),
  reasoning,
  risk_level,
  recommended_quantity,
  timestamp
}
```

### Trade
```
{
  id, asset_id, asset_name,
  action (BUY/SELL),
  entry_price, quantity,
  timestamp, status,
  reasoning, confidence
}
```

### Portfolio
```
{
  total_value,
  total_invested,
  realized_pnl, unrealized_pnl,
  cash_balance,
  holdings [
    {asset_id, quantity, avg_cost, current_price, pnl}
  ],
  last_updated
}
```

---

## 🎓 Learning Resources

- RSI: https://en.wikipedia.org/wiki/Relative_strength_index
- MACD: https://en.wikipedia.org/wiki/MACD
- Bollinger Bands: https://en.wikipedia.org/wiki/Bollinger_Bands
- Technical Analysis: https://en.wikipedia.org/wiki/Technical_analysis

---

**This architecture prioritizes safety, transparency, and maintainability.**
