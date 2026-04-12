# 📚 Documentation Index - AI Trading Assistant

Complete guide to all documentation, files, and how to use them.

---

## 🚀 Getting Started

Start here if you're new to the system:

1. **[QUICKSTART.md](QUICKSTART.md)** - Get running in 5 minutes
   - Docker setup (recommended)
   - Manual setup
   - First trade example

2. **[SETUP.md](SETUP.md)** - Detailed installation guide
   - Prerequisites
   - Backend setup
   - Frontend setup
   - Testing the system
   - Troubleshooting

3. **[README.md](README.md)** - Complete system documentation
   - Core features
   - Project structure
   - Configuration options
   - Workflow overview
   - Safety features

---

## 📖 Technical Documentation

Understand how the system works:

1. **[ARCHITECTURE.md](ARCHITECTURE.md)** - System design deep dive
   - High-level architecture overview
   - Data flow diagrams
   - Component interactions
   - Trading workflow
   - Technical analysis strategy
   - Deployment options

2. **[API_REFERENCE.md](API_REFERENCE.md)** - Complete API documentation
   - All endpoints explained
   - Request/response formats
   - Query parameters
   - Error codes
   - Example curl commands
   - WebSocket connection

---

## 💻 Backend Structure

```
backend/
├── main.py                 # FastAPI entry point
├── requirements.txt        # Python dependencies
├── .env                    # Configuration file
├── .env.example           # Example config (COPY THIS)
│
└── app/
    ├── __init__.py
    ├── api/
    │   └── routes.py      # All API endpoints (100+ lines)
    │
    ├── core/
    │   └── config.py      # Configuration management
    │
    ├── models/
    │   └── schemas.py     # Data models & validation
    │
    ├── services/
    │   ├── technical_analysis.py    # Analysis engine (~300 lines)
    │   ├── trading_engine.py        # Trade logic (~200 lines)
    │   ├── paper_trading.py         # Simulator (~200 lines)
    │   └── groww_api.py            # API integration (~150 lines)
    │
    └── utils/
        └── (utilities)
```

### Key Services

**technical_analysis.py** - Calculates all indicators
- RSI, MACD, Bollinger Bands, Moving Averages, Volume
- Generates unified trade signals
- Returns confidence scores

**trading_engine.py** - Main decision engine
- Generates options strategies
- Mutual fund recommendations
- Risk management
- Stocks to watch

**paper_trading.py** - Simulation engine
- Portfolio management
- Trade execution (paper)
- P&L calculation
- Performance metrics

**groww_api.py** - Broker integration
- Real quote fetching
- Historical data
- Live order placement
- Portfolio sync

---

## 🎨 Frontend Structure

```
frontend/
├── package.json
├── tailwind.config.js
├── postcss.config.js
│
└── src/
    ├── App.jsx            # Main app component (~200 lines)
    ├── App.css            # App styles
    ├── index.js           # Entry point
    ├── index.css          # Global styles
    │
    ├── components/
    │   ├── Dashboard.jsx  # Core dashboard components (~250 lines)
    │   │   ├── TradeFeed
    │   │   ├── PortfolioOverview
    │   │   ├── PerformanceDashboard
    │   │   ├── TradingModeToggle
    │   │   └── ReasoningPanel
    │   │
    │   ├── Charts.jsx     # Chart components (~150 lines)
    │   │   ├── EquityCurve
    │   │   ├── TradeDistribution
    │   │   └── PortfolioAllocation
    │   │
    │   └── Modals.jsx     # Modal dialogs (~200 lines)
    │       ├── OptionsSuggestionsModal
    │       ├── MutualFundsModal
    │       └── StocksToWatchModal
    │
    ├── services/
    │   └── api.js         # REST & WebSocket client (~80 lines)
    │
    └── pages/
        (future pages)
```

### Component Hierarchy

```
App
├── Header (with buttons)
├── TradingModeToggle
├── TradeFeed & PortfolioOverview (grid)
├── PerformanceDashboard & ReasoningPanel (grid)
├── SuggestionsPanel
├── EquityCurve & TradeDistribution (grid)
├── PortfolioAllocation
├── Modals (OptionsSuggestions, MutualFunds, StocksToWatch)
└── Footer
```

---

## 📝 Testing & Demos

### Mock Data Generator

```bash
# Run mock trading simulation
python mock_data_generator.py --cycles 5

# Or test once
python mock_data_generator.py --test

# Against different server
python mock_data_generator.py --url http://other-server:8000
```

### Manual API Testing

```bash
# Health check
curl http://localhost:8000/health

# Generate signals
curl -X POST http://localhost:8000/api/signals/generate \
  -H "Content-Type: application/json" \
  -d '{...}'

# Execute trade
curl -X POST http://localhost:8000/api/trades/execute \
  -H "Content-Type: application/json" \
  -d '{...}'
```

See [API_REFERENCE.md](API_REFERENCE.md) for complete examples.

---

## 🐳 Docker & Deployment

### Docker Files

- **Dockerfile.backend** - Container for FastAPI server
- **Dockerfile.frontend** - Container for React app
- **docker-compose.yml** - Orchestration file

```bash
# Start with Docker
docker-compose up

# Or manual deployment
# See SETUP.md for instructions
```

---

## 📊 Configuration

### Environment Variables (.env)

Located in `backend/.env`:

```env
# Server
DEBUG=True                      # Enable debug mode
LOG_LEVEL=INFO                 # Logging level

# Groww API
GROWW_API_KEY=your_key_here    # Your API key
GROWW_API_BASE_URL=...         # API endpoint

# Trading
LIVE_TRADING_ENABLED=False     # Safety: disabled by default
PAPER_TRADING_INITIAL_CAPITAL=1000000  # Starting capital
MAX_POSITION_SIZE_PERCENT=10   # Max position size
STOP_LOSS_PERCENT=2            # Stop loss level

# Technical Analysis
RSI_PERIOD=14                  # RSI period
MACD_FAST=12                   # MACD fast
MACD_SLOW=26                   # MACD slow
MACD_SIGNAL=9                  # MACD signal

# Database
DATABASE_URL=sqlite:///./trading_system.db
```

### Frontend .env.local

```env
REACT_APP_API_URL=http://localhost:8000
```

---

## 🎯 Feature Matrix

| Feature | Status | docs |
|---------|--------|------|
| Technical Analysis | ✅ Complete | ARCHITECTURE.md |
| Paper Trading | ✅ Complete | README.md |
| Live Trading | ✅ Ready | README.md |
| Options Strategies | ✅ Complete | API_REFERENCE.md |
| Mutual Funds | ✅ Complete | API_REFERENCE.md |
| Risk Management | ✅ Complete | README.md |
| Portfolio Tracking | ✅ Complete | API_REFERENCE.md |
| Performance Metrics | ✅ Complete | API_REFERENCE.md |
| Real-time Signals | ✅ Complete | ARCHITECTURE.md |
| Dashboard UI | ✅ Complete | README.md |
| WebSocket Stream | ✅ Complete | API_REFERENCE.md |
| Groww Integration | ✅ Ready | API_REFERENCE.md |

---

## 🔧 Customization Guide

### Change Technical Analysis Parameters

Edit `backend/app/core/config.py`:

```python
RSI_PERIOD = 14              # Change from 14 to 21
MACD_FAST = 12              # Change from 12 to 10
STOP_LOSS_PERCENT = 2       # Change from 2% to 3%
```

### Change Dashboard Layout

Edit `frontend/src/App.jsx`:

```javascript
// Change grid layout
<div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
  {/* Add more columns */}
</div>
```

### Add New Indicator

Edit `backend/app/services/technical_analysis.py`:

```python
@staticmethod
def calculate_stochastic(prices):
    # Implement your indicator
    return values, signal
```

Then add to `generate_trade_signal()`:

```python
indicators.append(IndicatorSignal(...))
```

### Add New API Endpoint

Edit `backend/app/api/routes.py`:

```python
@router.get("/api/my-endpoint")
async def my_endpoint():
    return {"result": "data"}
```

---

## 📊 Database Schema

### SQLite (default)

```sql
-- Trades table
CREATE TABLE trades (
    id TEXT PRIMARY KEY,
    asset_id TEXT,
    asset_name TEXT,
    action TEXT,
    entry_price FLOAT,
    quantity INT,
    timestamp DATETIME,
    status TEXT,
    reasoning TEXT,
    confidence FLOAT
);

-- Portfolio snapshots
CREATE TABLE portfolio_snapshots (
    timestamp DATETIME PRIMARY KEY,
    total_value FLOAT,
    cash_balance FLOAT,
    holdings JSON
);

-- Performance history
CREATE TABLE performance_history (
    date DATE PRIMARY KEY,
    cumulative_profit FLOAT,
    win_rate FLOAT,
    roi FLOAT
);
```

### To PostgreSQL

Change `.env`:

```env
DATABASE_URL=postgresql://user:pass@localhost/trading_db
```

Then run migration (future feature).

---

## 🚨 Safety Checklist

Before going live:

- [ ] Review risk settings in `.env`
- [ ] Limit position size to 5-10% max
- [ ] Set stop-loss at 2-3%
- [ ] Keep LIVE_TRADING_ENABLED=False until tested
- [ ] Run 100+ paper trades first
- [ ] Have Groww account funded and tested
- [ ] Review all trade reasoning before execution
- [ ] Monitor first few live trades closely
- [ ] Have emergency stop button ready
- [ ] Keep logs for audit trail

---

## 📈 Performance Optimization

### Backend Optimization

1. **Cache technical analysis** (1-min window)
2. **Use database connection pooling**
3. **Add Redis for rate limiting**
4. **Implement async processing for slow calculations**

### Frontend Optimization

1. **Lazy-load chart components**
2. **Virtualize trade feed (1000+ trades)**
3. **Cache API responses**
4. **Use production build for deployment**

### Database Optimization

1. **Index on timestamps**
2. **Archive old trades**
3. **Use read replicas for queries**
4. **Partition by date**

---

## 📚 Learning Path

### Week 1: Foundations
- [ ] Read README.md
- [ ] Read QUICKSTART.md
- [ ] Get system running
- [ ] Explore dashboard

### Week 2: Understanding
- [ ] Read ARCHITECTURE.md
- [ ] Study API_REFERENCE.md
- [ ] Review backend code
- [ ] Understand technical analysis

### Week 3: Practice
- [ ] Run 50+ paper trades
- [ ] Test different indicators
- [ ] Review performance metrics
- [ ] Analyze win/loss patterns

### Week 4: Mastery
- [ ] Customize indicators
- [ ] Add new features
- [ ] Optimize strategies
- [ ] Consider live trading

---

## 🆘 Common Issues & Solutions

### Backend Issues

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: talib` | Install: `brew install ta-lib` |
| `Address already in use` | `lsof -ti:8000 \| xargs kill -9` |
| Database locked | Delete `.db` file and restart |
| API connection fails | Check Groww credentials in `.env` |

### Frontend Issues

| Issue | Solution |
|-------|----------|
| `npm ERR!` | `rm -rf node_modules && npm install` |
| Can't reach backend | Verify `http://localhost:8000/health` |
| Port 3000 in use | `PORT=3001 npm start` |
| Blank dashboard | Check browser console (F12) |

### General Issues

| Issue | Solution |
|-------|----------|
| No trades | Check signal confidence threshold |
| Wrong P&L | Verify average cost calculation |
| Frozen UI | Check browser performance tab |

---

## 🎓 Educational Resources

- **Technical Analysis**: Investopedia, TradingView
- **Python FastAPI**: https://fastapi.tiangolo.com
- **React**: https://react.dev
- **Financial Analysis**: CFA Institute, Khan Academy

---

## 📞 Support Paths

1. **Check documentation** → README.md
2. **Review API docs** → API_REFERENCE.md
3. **Study architecture** → ARCHITECTURE.md
4. **Troubleshoot** → SETUP.md
5. **Review code** → Source files

---

## 🚀 Future Enhancements

- [ ] Machine learning signals
- [ ] Portfolio optimization (Markowitz)
- [ ] Options Greeks calculation
- [ ] Real-time news sentiment
- [ ] Market regime detection
- [ ] Strategy backtesting
- [ ] Mobile app
- [ ] Advanced charting
- [ ] More broker integrations
- [ ] Paper trading leaderboard

---

## 📄 File Reference

### Documentation Files
- `README.md` - Main documentation (comprehensive)
- `SETUP.md` - Installation & setup guide
- `QUICKSTART.md` - 5-minute quick start
- `ARCHITECTURE.md` - System design details
- `API_REFERENCE.md` - API documentation
- `INDEX.md` - This file (navigation guide)

### Configuration Files
- `backend/.env` - Backend configuration
- `backend/.env.example` - Example config
- `backend/requirements.txt` - Python dependencies
- `frontend/package.json` - Node dependencies
- `frontend/tailwind.config.js` - CSS config
- `docker-compose.yml` - Docker setup

### Source Code
- `backend/main.py` - FastAPI entry point
- `backend/app/api/routes.py` - All API routes
- `backend/app/services/*.py` - Core services
- `backend/app/models/schemas.py` - Data models
- `frontend/src/App.jsx` - Main React component
- `frontend/src/components/*.jsx` - React components

### Utilities
- `mock_data_generator.py` - Test data generator
- `Dockerfile.backend` - Backend container
- `Dockerfile.frontend` - Frontend container

---

## ✅ Verification Checklist

System is ready when:

- [ ] Backend runs: `python main.py` ✓
- [ ] Frontend runs: `npm start` ✓
- [ ] Health check passes: `curl http://localhost:8000/health` ✓
- [ ] Dashboard loads: http://localhost:3000 ✓
- [ ] Can generate signals: API responds ✓
- [ ] Can execute trades: Portfolio updates ✓
- [ ] Metrics display: No errors in console ✓
- [ ] Charts render: Equity curve visible ✓

---

## 📞 Get Help

1. **Installation help** → See SETUP.md
2. **API questions** → See API_REFERENCE.md
3. **Architecture** → See ARCHITECTURE.md
4. **Features** → See README.md
5. **Quick start** → See QUICKSTART.md

---

**Welcome to the AI Trading Assistant! 🚀📈**

Start with QUICKSTART.md for fastest setup.
