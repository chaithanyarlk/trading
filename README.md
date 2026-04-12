# AI Trading Assistant - Complete System

A full-stack intelligent trading system powered by Claude AI for stock market analysis, paper trading simulation, and live trading execution via Groww API.

## 🎯 Core Features

### 1. **Intelligent Decision Engine**
- Real-time technical analysis using RSI, MACD, Bollinger Bands, Moving Averages
- Multi-indicator signal generation with confidence scoring
- Risk-adjusted trade recommendations
- Explainable AI reasoning for every trade decision

### 2. **Dual Trading Modes**
- **Paper Trading**: Simulate trades with ₹10L virtual capital
- **Live Trading**: Execute real trades via Groww API (with explicit user approval)
- Seamless mode switching with risk warnings

### 3. **Comprehensive Dashboard**
- Real-time trade feed with reasoning
- Live portfolio tracking
- Performance metrics (win rate, ROI, Sharpe ratio)
- Equity curve visualization
- Trade distribution analysis
- Portfolio allocation breakdown

### 4. **Advanced Features**
- Options trading strategies (calls, puts, spreads)
- Mutual fund recommendations with expected returns
- Stocks to watch with technical/fundamental scores
- Risk management (stop-loss, position sizing, diversification)
- Trade logging and audit trail

### 5. **Safety & Risk Management**
- Configurable position sizing (max 10% per trade)
- Stop-loss enforcement (default 2%)
- Trade approval workflow
- Comprehensive logging
- Real-time risk warnings

---

## 📁 Project Structure

```
copilot_trade/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes.py          # FastAPI endpoints
│   │   ├── core/
│   │   │   └── config.py          # Configuration management
│   │   ├── models/
│   │   │   └── schemas.py         # Pydantic data models
│   │   ├── services/
│   │   │   ├── groww_api.py       # Groww API client
│   │   │   ├── technical_analysis.py # Technical analysis engine
│   │   │   ├── paper_trading.py   # Paper trading simulator
│   │   │   └── trading_engine.py  # Main trading logic
│   │   └── utils/
│   ├── main.py                    # FastAPI app entry point
│   ├── requirements.txt           # Python dependencies
│   ├── .env                       # Configuration file
│   └── .env.example               # Example env config
├── frontend/
│   ├── public/
│   │   └── index.html             # HTML entry point
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.jsx      # Dashboard components
│   │   │   ├── Charts.jsx         # Chart components
│   │   │   └── Modals.jsx         # Modal components
│   │   ├── pages/
│   │   ├── services/
│   │   │   └── api.js             # API client
│   │   ├── App.jsx                # Main app component
│   │   ├── App.css                # App styles
│   │   ├── index.js               # React entry point
│   │   └── index.css              # Global styles
│   ├── package.json               # Node dependencies
│   ├── tailwind.config.js         # Tailwind CSS config
│   └── postcss.config.js          # PostCSS config
├── README.md                      # This file
└── SETUP.md                       # Setup instructions
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+
- Groww API credentials (optional for paper trading)

### Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Groww API key if using live trading

# Run the server
python main.py
```

Server will start on `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`
- Redoc: `http://localhost:8000/redoc`

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

Frontend will open on `http://localhost:3000`

---

## 🔑 Configuration

### Backend Environment Variables (`.env`)

```env
# Server
DEBUG=True
LOG_LEVEL=INFO

# Groww API
GROWW_API_KEY=your_api_key_here
GROWW_API_BASE_URL=https://api.groww.in

# Trading Settings
LIVE_TRADING_ENABLED=False          # Safety: disabled by default
PAPER_TRADING_INITIAL_CAPITAL=1000000
MAX_POSITION_SIZE_PERCENT=10        # Max 10% per trade
STOP_LOSS_PERCENT=2                 # Automatic 2% stop-loss

# Technical Analysis
RSI_PERIOD=14
MACD_FAST=12
MACD_SLOW=26
MACD_SIGNAL=9

# Database
DATABASE_URL=sqlite:///./trading_system.db
```

### Frontend Environment

Create `.env.local` in `frontend/`:

```env
REACT_APP_API_URL=http://localhost:8000
```

---

## 📊 API Endpoints

### Trade Signals
- `POST /api/signals/generate` - Generate trade signals from market data
- `GET /api/market/quote?symbol=TCS` - Get current stock quote
- `GET /api/market/historical?symbol=TCS&period=1y&interval=1d` - Get historical data

### Portfolio
- `GET /api/portfolio` - Get portfolio overview
- `GET /api/performance` - Get performance metrics
- `POST /api/trades/execute` - Execute a paper trade
- `GET /api/trades` - Get all trades

### Recommendations
- `GET /api/options/suggestions?underlying=TCS&current_price=3500` - Options strategies
- `GET /api/mutual-funds/recommendations` - Mutual fund suggestions
- `GET /api/stocks/watch` - Stocks to watch

### Trading Mode
- `POST /api/trading/mode` - Toggle between live/paper trading
- `WebSocket /ws/trades` - Real-time trade stream

---

## 🎮 Trading Examples

### Generate Signals

```python
import requests

market_data = {
    "TCS": {
        "prices": [3500, 3510, 3520, 3515, 3525],
        "volumes": [10000000, 12000000, 11000000, 13000000, 15000000],
        "current_price": 3525,
        "name": "Tata Consultancy Services"
    }
}

response = requests.post(
    "http://localhost:8000/api/signals/generate",
    json=market_data
)

signals = response.json()
for signal in signals:
    print(f"{signal['asset_name']}: {signal['action']} (Confidence: {signal['confidence']})")
    print(f"Reasoning: {signal['reasoning']}")
```

### Execute Paper Trade

```python
signal = signals[0]

trade_response = requests.post(
    "http://localhost:8000/api/trades/execute",
    json={
        "signal": signal,
        "quantity": 10
    }
)

trade_result = trade_response.json()
print(f"Trade Status: {trade_result['success']}")
print(f"Message: {trade_result['message']}")
```

---

## 🛡️ Safety Features

### 1. **Live Trading Safeguards**
- Disabled by default (`LIVE_TRADING_ENABLED=False`)
- Requires explicit configuration in `.env`
- User approval toggle on dashboard
- Real-time warning when enabled

### 2. **Position Sizing**
- Max 10% of portfolio per trade (configurable)
- Automatic calculation of optimal quantity
- Risk-per-trade limits enforcea

### 3. **Stop-Loss Protection**
- Automatic 2% stop-loss on all trades
- Configurable per trade type
- Strict enforcement for live mode

### 4. **Logging & Audit Trail**
- All trades logged with reasoning
- Timestamp for every action
- Error tracking and monitoring
- Audit trail for compliance

### 5. **API Safeguards**
- Error handling for failed API calls
- Automatic retry logic
- Timeout protection (10 seconds)
- Graceful degradation

---

## 📈 Technical Analysis Details

### 1. RSI (Relative Strength Index)
- Period: 14 days
- Signals: Oversold (<30) = BUY, Overbought (>70) = SELL
- Confidence: 0.8

### 2. MACD (Moving Average Convergence Divergence)
- Fast: 12, Slow: 26, Signal: 9
- Signal: Positive histogram = BUY, Negative = SELL
- Confidence: 0.75

### 3. Bollinger Bands
- Period: 20, Std Dev: 2
- Signal: Price at lower band = BUY, Upper band = SELL
- Confidence: 0.7

### 4. Moving Average Crossover
- Short MA: 20, Long MA: 50
- Golden Cross (20>50) = BUY, Death Cross (20<50) = SELL
- Confidence: 0.75

### 5. Volume Analysis
- Recent volume vs historical average
- Confirmation on trending moves
- Confidence: 0.6

### Signal Aggregation
- Combines all indicators with weighted confidence
- Final confidence = percentage of bullish indicators
- Risk level: LOW (>80%), MEDIUM (60-80%), HIGH (<60%)

---

## 🎯 Paper Trading Mode

### Capabilities
- Simulates real trades with virtual ₹10 lakh capital
- Accurate P&L tracking
- Position management (average cost calculation)
- Performance metrics calculation

### Performance Metrics
- **Win Rate**: Percentage of profitable trades
- **ROI**: Total profit / Initial investment
- **Max Drawdown**: Largest peak-to-trough decline
- **Sharpe Ratio**: Risk-adjusted returns (optional)
- **Average Trade Return**: Mean profit/loss per trade

### Use Cases
- Backtest strategies
- Learn system behavior
- Optimize parameters
- Gain confidence before live trading

---

## 🔐 Live Trading Mode

### Prerequisites
1. Groww API credentials
2. Funded account with Groww
3. `LIVE_TRADING_ENABLED=True` in `.env`
4. Explicit user approval on dashboard

### Execution
1. Signals generated continuously
2. User reviews signal with reasoning
3. Manual or automated execution (with approval)
4. Real money transactions
5. Trade logged with full audit trail

### Risk Management
- Position sizing strictly enforced
- Stop-loss orders automatically placed
- Maximum exposure limits
- 24/7 monitoring (future feature)

---

## 📱 Dashboard Features

### 1. Live Trade Feed
- Real-time stream of pending/executed trades
- Asset name, action (Buy/Sell), price, timestamp
- Confidence score visualization
- Trade status indicator

### 2. Portfolio Overview
- Total portfolio value
- Unrealized P&L (real or simulated)
- Cash balance
- Holdings with individual P&L
- Allocation by asset

### 3. Performance Dashboard
- Total trades executed
- Win rate percentage
- Winning vs losing trades ratio
- Net profit/loss
- ROI and Sharpe ratio
- Max drawdown

### 4. Reasoning Panel
- Detailed explanation for each trade
- Indicators used and their values
- Risk assessment
- Confidence score breakdown

### 5. Equity Curve
- Portfolio value over time
- Cumulative profit visualization
- Drawdown periods highlighted
- Performance comparison

### 6. Modals
- **Options Strategies**: Call/Put/Spread suggestions
- **Mutual Funds**: SIP and lump-sum recommendations
- **Stocks to Watch**: Technical and fundamental scoring

---

## 🔄 Workflow

```
1. Market Data Collection
   ↓
2. Technical Analysis
   ↓
3. Signal Generation
   ↓
4. Signal Feed (WebSocket)
   ↓
5. User Reviews Reasoning
   ↓
6. Manual Approval / Auto-Execute
   ↓
7. Trade Execution
   ↓
8. Portfolio Update
   ↓
9. Performance Tracking
   ↓
10. Log & Audit
```

---

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check Python version
python3 --version  # Should be 3.9+

# Clear cache
rm -rf __pycache__ .pytest_cache

# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

### Frontend won't load data
```bash
# Check if backend is running
curl http://localhost:8000/health

# Check CORS issues in browser console
# Verify REACT_APP_API_URL in .env.local
```

### API errors
- Check `.env` configuration
- Verify Groww API credentials (if using live trading)
- Check logs in console
- Verify database connectivity

---

## 📚 Dependencies

### Backend
- **FastAPI**: Modern web framework
- **Uvicorn**: ASGI server
- **Pandas**: Data manipulation
- **TA-Lib**: Technical analysis
- **Requests**: HTTP client
- **SQLAlchemy**: Database ORM
- **Pydantic**: Data validation

### Frontend
- **React**: UI framework
- **Axios**: HTTP client
- **Recharts**: Chart library
- **Tailwind CSS**: Styling
- **React Icons**: Icon library

---

## 🚀 Deployment

### Backend Deployment (Heroku)
```bash
# Requires Procfile and runtime.txt
heroku create your-app-name
git push heroku main
```

### Frontend Deployment (Vercel)
```bash
npm install -g vercel
vercel
```

---

## 📄 License

This project is provided as-is for educational purposes.

---

## ⚠️ Disclaimer

**This is a simulation and educational tool. Not for actual financial trading.**

- No guarantees of profit
- Market conditions are volatile
- Past performance ≠ future results
- Always consult financial advisors
- Use at your own risk
- Verify all signals before trading

---

## 🤝 Support

For issues or questions:
1. Check documentation
2. Review error logs
3. Test with paper trading first
4. Verify API connections

---

## 🎓 Learning Resources

- [Technical Analysis Tutorial](https://www.investopedia.com)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [React Learning](https://react.dev)
- [Groww API Docs](https://groww.in/api-docs)

---

**Happy Trading! 🚀📈**
