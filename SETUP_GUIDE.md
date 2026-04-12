# AI Trading Platform - Complete Setup & Usage Guide

## 🚀 System Overview

This is a **fully autonomous AI-powered trading and investment platform** powered by **local Claude AI** (running on your PC) for all analysis, reasoning, and decision-making.

### Key Features:
✅ **Local Claude AI Analysis** - Sophisticated multi-factor stock analysis  
✅ **Real-time Groww API Integration** - Market data, options, mutual funds  
✅ **Automated Trade Execution** - Intraday & swing trading with AI signals  
✅ **Options Trading Engine** - 7+ strategy types with AI selection  
✅ **Explainable AI** - Complete reasoning for every trade  
✅ **Paper Trading Simulator** - Realistic simulation with slippage/commission  
✅ **Mutual Fund Intelligence** - AI-powered fund recommendations & SIP planning  
✅ **End-of-Day Reports** - Automated 3:30 PM IST reports with AI insights  
✅ **Trade Logging & Analytics** - Complete trade history with graphs  

---

## 📋 Prerequisites

### System Requirements:
- **Python**: 3.9 or higher
- **Claude API Key**: [Get from Anthropic](https://console.anthropic.com)
- **RAM**: 4GB minimum (8GB recommended)
- **Disk**: 2GB free space

### API Credentials Required:
1. **Anthropic Claude API Key** (for local AI analysis)
2. **Groww API Credentials** (market data integration)
   - API_KEY
   - API_SECRET
   - AUTH_TOKEN

---

## 🔧 Installation Steps

### Step 1: Clone/Setup Project
```bash
cd /Users/hari/Desktop/copilot_trade
```

### Step 2: Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# or: venv\Scripts\activate  # Windows
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

**Required packages** (should be in requirements.txt):
```
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
sqlalchemy==2.0.23
pandas==2.1.1
numpy==1.26.2
talib==0.10.2
aiohttp==3.9.1
anthropic==0.21.0
python-dotenv==1.0.0
apscheduler==3.10.4
```

### Step 4: Configure Environment Variables

Create `.env` file in project root:

```env
# API Keys
CLAUDE_API_KEY=your_claude_api_key_here
GROWW_API_KEY=your_groww_api_key
GROWW_API_SECRET=your_groww_api_secret
GROWW_AUTH_TOKEN=your_groww_auth_token

# Trading Configuration
PAPER_TRADING_INITIAL_CAPITAL=100000
LIVE_TRADING_ENABLED=false
TRADING_SLIPPAGE_PERCENT=0.05
TRADING_COMMISSION_PERCENT=0.02

# Claude Model
CLAUDE_MODEL=claude-3-5-sonnet-20241022

# Database
DATABASE_URL=sqlite:///./trading.db

# Logging
LOG_LEVEL=INFO

# App Config
APP_NAME=AI Trading Platform
APP_VERSION=1.0.0
DEBUG=false
```

---

## 🎯 Understanding the Architecture

### Service Layers:

1. **Database Layer** (`/backend/app/models/database.py`)
   - SQLAlchemy ORM with 12 tables
   - Market data storage, trade signals, execution logs, reports

2. **API Integration Layer** (`/backend/app/services/groww_api_enhanced.py`)
   - Real-time quotes, historical data, options chains
   - Mutual fund database, market sentiment
   - Order execution framework

3. **AI Analysis Layer** (`/backend/app/services/ai_analysis_advanced.py`)
   - Multi-factor technical analysis using Local Claude
   - Confidence scoring, target price calculation
   - Portfolio risk assessment

4. **Options Trading** (`/backend/app/services/options_trading_engine.py`)
   - 7 strategy types: Straddle, Strangle, Iron Condor, Bull/Bear Spreads, Directional
   - AI-driven strategy selection based on market conditions
   - Greeks calculation (Delta, Gamma, Theta, Vega)

5. **Trade Execution** (`/backend/app/services/paper_trading_advanced.py`)
   - Realistic simulator with slippage & commission modeling
   - Position averaging, stop-loss/profit-target execution
   - Performance metrics (Win rate, Sharpe ratio, max drawdown)

6. **Explainable AI** (`/backend/app/services/explainable_ai.py`)
   - Complete reasoning log for every trade entry/exit
   - Indicator agreement tracking
   - Confidence factor extraction

7. **Mutual Fund Analysis** (`/backend/app/services/mutual_fund_analyzer.py`)
   - Fund analysis with Claude recommendations
   - SIP planning with maturity projections
   - Portfolio diversification analysis

8. **Report Generation** (`/backend/app/services/report_generator.py`)
   - Daily reports with trade summaries
   - AI-generated insights and recommendations
   - Strategy performance breakdown
   - Next-day watchlist generation

9. **Orchestration & Scheduling** (`/backend/app/services/orchestrator.py`)
   - Trade execution orchestration
   - 3:30 PM IST end-of-day report generation
   - Market data update scheduling (every 5 minutes during market hours)

---

## ▶️ Running the Platform

### Start the Server:
```bash
cd /Users/hari/Desktop/copilot_trade/backend
python main.py
```

**Expected Output:**
```
============================================================
AI TRADING PLATFORM - STARTUP SEQUENCE
============================================================
Initializing database...
✓ Database initialized
Starting Trade Execution Orchestrator...
Initializing Trade Executor...
Starting Scheduler (EOD reports @ 3:30 PM IST)...
✓ Scheduler started
✓ EOD Report callback registered
============================================================
✓ AI TRADING PLATFORM READY
============================================================
Paper Trading Capital: ₹100,000.00
Live Trading Enabled: false
Claude Model: claude-3-5-sonnet-20241022
Market Timezone: Asia/Kolkata (IST)
API Documentation: http://localhost:8000/docs
============================================================
```

### Access the Platform:
- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Root Endpoint**: http://localhost:8000/

---

## 📡 API Endpoints

### Stock Analysis
```
POST /api/advanced/analysis/comprehensive
  - Input: symbol, risk_profile
  - Returns: BUY/SELL/HOLD signal, confidence, target price, stop loss, reasoning
```

### Trade Execution
```
POST /api/advanced/trades/execute
  - Input: symbol, action (BUY/SELL), quantity, mode (PAPER/LIVE)
  - Returns: Execution result with trade details

POST /api/advanced/trades/set-stop-loss
  - Input: symbol, stop_loss_price, mode
  - Returns: Confirmation

POST /api/advanced/trades/set-target
  - Input: symbol, target_price, mode
  - Returns: Confirmation
```

### Portfolio
```
GET /api/advanced/portfolio/performance
  - Returns: Portfolio value, metrics, positions

GET /api/advanced/stats/execution
  - Returns: Trade execution statistics
```

### Options Trading
```
POST /api/advanced/options/select-strategy
  - Input: symbol, market_sentiment, volatility_level
  - Returns: Recommended strategy with Greeks, probability, risk/reward
```

### Mutual Funds
```
POST /api/advanced/mutual-funds/recommend
  - Input: amount, investment_horizon, risk_profile, objective
  - Returns: Top fund recommendations with allocation %

POST /api/advanced/mutual-funds/sip-plan
  - Input: fund_name, monthly_amount, duration_months
  - Returns: SIP projections with maturity value
```

### Reports
```
POST /api/advanced/reports/generate-daily
  - Returns: End-of-day report with AI insights and watchlist

GET /api/advanced/reports/export-html
  - Returns: HTML-formatted report
```

### Trade Reasoning
```
GET /api/advanced/reasoning/trades/{trade_id}
  - Returns: Complete trade reasoning and explanation
```

### Scheduler
```
GET /api/advanced/scheduler/status
  - Returns: Scheduled jobs and next run times

GET /api/advanced/scheduler/market-status
  - Returns: Whether market is open
```

---

## 💡 Usage Examples

### Example 1: Get Stock Analysis
```bash
curl -X POST "http://localhost:8000/api/advanced/analysis/comprehensive" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "INFY",
    "risk_profile": "BALANCED"
  }'
```

### Example 2: Execute Paper Trade
```bash
curl -X POST "http://localhost:8000/api/advanced/trades/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "INFY",
    "action": "BUY",
    "quantity": 10,
    "mode": "PAPER"
  }'
```

### Example 3: Get Options Strategy
```bash
curl -X POST "http://localhost:8000/api/advanced/options/select-strategy" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "INFY",
    "market_sentiment": "BULLISH",
    "volatility_level": "HIGH"
  }'
```

### Example 4: Generate Daily Report
```bash
curl -X POST "http://localhost:8000/api/advanced/reports/generate-daily"
```

---

## 📊 Dashboard Integration (Frontend)

The frontend React app should consume these endpoints to display:

1. **Stock Analysis Dashboard**
   - AI signals for tracked stocks
   - Confidence scores and target prices

2. **Portfolio Dashboard**
   - Current portfolio value (stock + cash)
   - Unrealized P&L by position
   - Performance metrics (win rate, Sharpe ratio)

3. **Trade History**
   - All executed trades
   - Entry/exit reasoning from explainable AI
   - P&L for each trade

4. **Options Strategies**
   - Available strategies for selected symbols
   - Greeks and risk/reward analysis
   - Strategy recommendations

5. **Mutual Funds**
   - Recommended funds based on profile
   - SIP projections
   - Fund comparison charts

6. **Reports & Insights**
   - Daily report with graphs
   - Trade performance breakdowns
   - Lessons learned from losing trades
   - Next-day watchlist

---

## 🔄 Automated Features

### 1. End-of-Day Report (3:30 PM IST)
- Automatically generated via scheduler
- Includes trade summary, performance metrics, AI insights
- Generated as JSON and HTML
- Identifies mistakes and extracts lessons

### 2. Market Data Updates (Every 5 minutes during market hours)
- Updates stock quotes for watched symbols
- Refreshes technical indicators
- Updates market breadth and sentiment

### 3. Trade Signal Generation (Every minute during market hours)
- Scans watchlist for AI signals
- Evaluates all tracked symbols
- Logs signals with confidence scores

---

## 🛠️ Configuration & Customization

### Adjust Trading Parameters

In `.env`:
```env
PAPER_TRADING_INITIAL_CAPITAL=100000  # Starting capital
TRADING_SLIPPAGE_PERCENT=0.05         # 0.05% slippage
TRADING_COMMISSION_PERCENT=0.02       # 0.02% commission per trade
```

### Change Report Generation Time

In `backend/app/services/orchestrator.py`:
```python
# Currently set to 3:30 PM IST (15:30)
# Modify the CronTrigger to change:
CronTrigger(
    hour=15,    # Hour (0-23)
    minute=30,  # Minute (0-59)
    timezone=self.ist
)
```

### Adjust AI Analysis Parameters

In `backend/app/services/ai_analysis_advanced.py`:
- Modify Claude prompt for different analysis depth
- Change technical indicators weights
- Adjust confidence thresholds

---

## ⚙️ Environment-Specific Setup

### Development (Paper Trading Only)
```env
LIVE_TRADING_ENABLED=false
LOG_LEVEL=DEBUG
DEBUG=true
```

### Production (Live Trading Enabled)
```env
LIVE_TRADING_ENABLED=true
LOG_LEVEL=INFO
DEBUG=false
```

⚠️ **Important**: Only enable `LIVE_TRADING_ENABLED=true` after thoroughly testing with paper trading.

---

## 📝 Database Schema

### Key Tables:
- **MarketData**: OHLCV candles with VWAP
- **IndicatorCache**: Cached technical indicators (RSI, MACD, BB, MA, volume)
- **TradeSignal**: AI-generated signals with confidence scores
- **ExecutedTrade**: Executed trades with entry/exit prices and P&L
- **OptionsTrade**: Options positions with Greeks
- **PortfolioHolding**: Current open positions
- **MutualFund**: Mutual fund database
- **DailyReport**: End-of-day reports with AI insights
- **SystemLog**: System events and errors

---

## 🧪 Testing

### Manual Test Sequence:

1. **Start Platform**
   ```bash
   python main.py
   ```

2. **Check Health**
   ```bash
   curl http://localhost:8000/api/advanced/health
   ```

3. **Test Stock Analysis**
   ```bash
   curl -X POST http://localhost:8000/api/advanced/analysis/comprehensive \
     -H "Content-Type: application/json" \
     -d '{"symbol": "SBIN", "risk_profile": "BALANCED"}'
   ```

4. **Test Paper Trade**
   ```bash
   curl -X POST http://localhost:8000/api/advanced/trades/execute \
     -H "Content-Type: application/json" \
     -d '{"symbol": "SBIN", "action": "BUY", "quantity": 5, "mode": "PAPER"}'
   ```

5. **Check Portfolio**
   ```bash
   curl http://localhost:8000/api/advanced/portfolio/performance
   ```

6. **Generate Report**
   ```bash
   curl -X POST http://localhost:8000/api/advanced/reports/generate-daily
   ```

---

## 🐛 Troubleshooting

### Issue: "Claude API Key not found"
**Solution**: Ensure `.env` file has `CLAUDE_API_KEY=your_key_here`

### Issue: "Groww API connection failed"
**Solution**: Verify Groww credentials in `.env` and internet connection

### Issue: "Database locked" error
**Solution**: Close any other processes accessing `trading.db` and restart server

### Issue: Scheduler not generating daily reports
**Solution**: Ensure APScheduler is installed and check the server logs for errors

### Issue: Live trading not working
**Solution**: 
1. Set `LIVE_TRADING_ENABLED=true` in `.env`
2. Verify Groww API credentials
3. Ensure you have sufficient funds in live account

---

## 📊 Performance Optimization

### For Better AI Analysis:
- Track only 10-15 stocks (reduce processing overhead)
- Use 1-hour or 4-hour timeframes (faster analysis)
- Cache market data locally (already implemented)

### For Faster Execution:
- Run on machine with 4+ GB RAM
- Use SSD for database storage
- Minimize number of parallel API requests

---

## 🔐 Security Best Practices

1. **Never commit `.env` file** to git
2. **Use environment variables** for all sensitive data
3. **Rotate API keys** every 3 months
4. **Enable live trading only** after extensive paper trading
5. **Monitor trade logs** for suspicious activity
6. **Backup database** daily

---

## 📞 Support & Documentation

### Valuable Resources:
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Anthropic Claude API](https://docs.anthropic.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [APScheduler Documentation](https://apscheduler.readthedocs.io/)

### Project Files Structure:
```
copilot_trade/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes.py (All API endpoints)
│   │   ├── models/
│   │   │   ├── database.py (SQLAlchemy ORM)
│   │   │   └── schemas.py (Pydantic schemas)
│   │   ├── services/
│   │   │   ├── ai_analysis_advanced.py (Claude AI)
│   │   │   ├── options_trading_engine.py (Options strategies)
│   │   │   ├── paper_trading_advanced.py (Simulator)
│   │   │   ├── explainable_ai.py (Trade reasoning)
│   │   │   ├── mutual_fund_analyzer.py (Fund analysis)
│   │   │   ├── report_generator.py (Daily reports)
│   │   │   ├── groww_api_enhanced.py (Market data)
│   │   │   └── orchestrator.py (Scheduler & execution)
│   │   └── core/
│   │       ├── config.py (Settings)
│   │       └── database.py (DB connection)
│   ├── main.py (FastAPI app)
│   └── requirements.txt (Dependencies)
├── frontend/ (React app)
└── SETUP_GUIDE.md (This file)
```

---

## 🎓 Learning Path

1. **Week 1**: Understand platform architecture, run paper trading
2. **Week 2**: Analyze stock signals, execute paper trades
3. **Week 3**: Test options strategies, mutual fund recommendations
4. **Week 4**: Review reports, optimize settings
5. **Week 5+**: Consider live trading (if confident)

---

## ✅ Platform Ready!

Your AI trading platform is now set up and ready to use. The system automatically handles:
- Real-time market analysis with Claude AI
- Automated trade execution (paper or live)
- Explainable AI reasoning for every decision
- Daily reports at 3:30 PM IST
- Portfolio performance tracking
- Options strategy recommendations
- Mutual fund intelligence

**Happy trading! 🚀**
