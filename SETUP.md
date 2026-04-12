# Setup Guide - AI Trading Assistant

Complete step-by-step instructions to get the system running.

## Prerequisites

### System Requirements
- **OS**: macOS, Linux, or Windows
- **Python**: 3.9 or higher
- **Node.js**: 16 or higher
- **npm**: 8 or higher

### Installation Verification

```bash
# Check Python
python3 --version

# Check Node.js and npm
node --version
npm --version
```

---

## 🔧 Part 1: Backend Setup

### Step 1: Navigate to Backend Directory

```bash
cd /Users/hari/Desktop/copilot_trade/backend
```

### Step 2: Create Virtual Environment

On macOS/Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

On Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This installs:
- FastAPI (web framework)
- Uvicorn (server)
- Pandas (data processing)
- TA-Lib (technical analysis)
- And more...

### Step 4: Configure Environment

Copy the example environment file and edit it:

```bash
# Copy example config
cp .env.example .env

# Edit .env with your settings
# nano .env  (or use your editor)
```

### Step 5: Start the Backend Server

```bash
python main.py
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Press CTRL+C to quit
```

### Verify Backend

Open in browser or terminal:

```bash
# Open browser to see Swagger documentation
# http://localhost:8000/docs

# Or use curl to test
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2024-04-10T...",
  "version": "1.0.0"
}
```

---

## 🎨 Part 2: Frontend Setup

### Step 1: Navigate to Frontend Directory

Open **new terminal** (keep backend running):

```bash
cd /Users/hari/Desktop/copilot_trade/frontend
```

### Step 2: Install Node Dependencies

```bash
npm install
```

This installs React, Tailwind CSS, and other dependencies (~500MB).

### Step 3: Create Environment File

```bash
# Create .env.local
echo "REACT_APP_API_URL=http://localhost:8000" > .env.local
```

### Step 4: Start Frontend Development Server

```bash
npm start
```

This will:
- Compile React components
- Start dev server on http://localhost:3000
- Open browser automatically
- Enable hot-reload

### Verify Frontend

- Dashboard should load with:
  - Trading Mode toggle
  - Portfolio Overview (₹0 initially)
  - Empty trade feed
  - Performance metrics

---

## 🧪 Part 3: Testing the System

### Test 1: Generate Test Signals

```bash
# Open a new terminal
curl -X POST http://localhost:8000/api/signals/generate \
  -H "Content-Type: application/json" \
  -d '{
    "RELIANCE": {
      "prices": [2500, 2510, 2520, 2515, 2525, 2535],
      "volumes": [1000000, 1200000, 1100000, 1300000, 1500000, 1400000],
      "current_price": 2535,
      "name": "Reliance Industries"
    }
  }'
```

Expected response:
```json
[
  {
    "asset_id": "RELIANCE",
    "asset_name": "Reliance Industries",
    "action": "BUY",
    "confidence": 0.8,
    "price": 2535,
    "reasoning": "Signal generated based on 5 indicators...",
    "risk_level": "LOW",
    "recommended_quantity": 253
  }
]
```

### Test 2: Execute Paper Trade

```bash
curl -X POST http://localhost:8000/api/trades/execute \
  -H "Content-Type: application/json" \
  -d '{
    "signal": {
      "asset_id": "RELIANCE",
      "asset_name": "Reliance Industries",
      "action": "BUY",
      "price": 2535,
      "confidence": 0.8,
      "recommended_quantity": 10
    },
    "quantity": 10
  }'
```

### Test 3: Check Portfolio

```bash
curl http://localhost:8000/api/portfolio
```

Response shows:
- Total portfolio value
- Holdings
- P&L
- Cash balance

### Test 4: Get Performance Metrics

```bash
curl http://localhost:8000/api/performance
```

Response shows:
- Win rate
- Total trades
- ROI
- Other metrics

### Test 5: Frontend - Execute Trade via UI

1. Go to `http://localhost:3000`
2. Click "Refresh" button
3. View portfolio update
4. Check trade in feed

---

## 📊 Live Demonstration

### Step 1: Generate Multiple Signals

```bash
curl -X POST http://localhost:8000/api/signals/generate \
  -H "Content-Type: application/json" \
  -d '{
    "RELIANCE": {
      "prices": [2500, 2510, 2520, 2515, 2525, 2535, 2545],
      "volumes": [1000000, 1200000, 1100000, 1300000, 1500000, 1400000, 1600000],
      "current_price": 2545,
      "name": "Reliance Industries"
    },
    "TCS": {
      "prices": [3500, 3510, 3520, 3515, 3525, 3535, 3545],
      "volumes": [800000, 900000, 850000, 950000, 1000000, 1100000, 1200000],
      "current_price": 3545,
      "name": "Tata Consultancy Services"
    }
  }'
```

### Step 2: Execute Trades

Execute 2-3 buy orders, then sell some positions.

### Step 3: Monitor Dashboard

Watch:
- Portfolio value update
- P&L change
- Trade feed populate
- Performance metrics calculate
- Equity curve draw

---

## ⚙️ Advanced Configuration

### Custom Technical Analysis

Edit `backend/app/core/config.py`:

```python
RSI_PERIOD = 14          # Change RSI lookback
MACD_FAST = 12           # Change MACD fast line
MACD_SLOW = 26           # Change MACD slow line
STOP_LOSS_PERCENT = 2    # Change stop loss %
```

### Risk Management

Edit `.env`:

```env
MAX_POSITION_SIZE_PERCENT=10    # Change position size
PAPER_TRADING_INITIAL_CAPITAL=2000000  # Change starting capital
```

### Database

By default uses SQLite:

```env
DATABASE_URL=sqlite:///./trading_system.db
```

For PostgreSQL:

```env
DATABASE_URL=postgresql://user:password@localhost/trading_db
```

---

## 🔐 Enabling Live Trading

### ⚠️ WARNING: Only enable after thorough testing!

1. **Get Groww API Credentials**
   - Sign up at Groww
   - Generate API key and secret
   - Copy credentials

2. **Update Environment**

```bash
# Edit .env
GROWW_API_KEY=your_actual_key_here
GROWW_API_BASE_URL=https://api.groww.in
```

3. **Start Backend with Live Mode Support**

```python
# In main.py or via .env
LIVE_TRADING_ENABLED=True
```

4. **Use Dashboard Toggle**
   - Go to frontend
   - Click "Switch to Live Trading"
   - Confirm warning
   - Only then will live trades execute

---

## 🐛 Troubleshooting

### Backend Issues

**Issue**: `ModuleNotFoundError: No module named 'talib'`

Solution:
```bash
# Install system dependencies
# macOS:
brew install ta-lib

# Ubuntu:
sudo apt-get install ta-lib libta-lib0-dev

# Then reinstall Python package:
pip install --force-reinstall ta-lib
```

**Issue**: `Address already in use`

Solution:
```bash
# Kill process on port 8000:
# macOS/Linux:
lsof -ti:8000 | xargs kill -9

# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Frontend Issues

**Issue**: `npm ERR! Module not found`

Solution:
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

**Issue**: Frontend can't reach backend

Solution:
```bash
# Verify backend is running
curl http://localhost:8000/health

# Check .env.local has correct URL
cat .env.local

# Should show:
# REACT_APP_API_URL=http://localhost:8000
```

**Issue**: Port 3000 already in use

Solution:
```bash
# Use different port
PORT=3001 npm start
```

---

## 📱 Mobile Access

To access dashboard from other devices:

1. **Get your machine IP**
   ```bash
   # macOS/Linux:
   ifconfig | grep "inet "
   
   # Windows:
   ipconfig
   ```

2. **Update environment**
   ```env
   # Backend: .env
   # Allow CORS for your IP
   ```

3. **Connect from mobile**
   ```
   http://<YOUR_IP>:3000
   ```

---

## 🔄 Continuous Development

### Start Multiple Terminals

```bash
# Terminal 1: Backend
cd backend && source venv/bin/activate && python main.py

# Terminal 2: Frontend
cd frontend && npm start

# Terminal 3: Testing/Monitoring
# Use for curl commands or monitoring
```

### Code Changes

- **Backend**: Auto-reload enabled when DEBUG=True
- **Frontend**: Hot-reload on save
- No need to restart servers

### Logs

```bash
# Backend logs in terminal
# Frontend logs in browser console (F12)
# Full logs in:
# Backend: trading_system.log (future feature)
```

---

## 💾 Database Management

### View SQLite Database

```bash
# macOS/Linux
sqlite3 trading_system.db

# Windows: Use SQLite Browser GUI
```

### Reset Database

```bash
# Remove database file
rm trading_system.db

# Restart backend to recreate
python main.py
```

---

## 📈 Performance Optimization

### Frontend

- Use production build for deployment:
  ```bash
  npm build
  ```

- Serve static files:
  ```bash
  npm install -g serve
  serve -s build
  ```

### Backend

- Use Gunicorn for production:
  ```bash
  pip install gunicorn
  gunicorn -w 4 main:app
  ```

- Enable caching
- Use database pooling

---

## ✅ Checklist

- [ ] Python 3.9+ installed
- [ ] Node.js 16+ installed
- [ ] Backend dependencies installed
- [ ] Frontend dependencies installed
- [ ] `.env` file configured
- [ ] Backend running on :8000
- [ ] Frontend running on :3000
- [ ] Health check passes
- [ ] Dashboard loads
- [ ] Can execute paper trades
- [ ] Performance metrics display

---

## 🎓 Next Steps

1. **Test Paper Trading**: Execute 5-10 virtual trades
2. **Backtest Strategy**: Review signals and decisions
3. **Optimize Parameters**: Adjust technicalanalysis settings
4. **Gain Confidence**: Mix of winning and losing trades helps
5. **Enable Live Trading**: Only after 100+ paper trades

---

## 📞 Support

If stuck, check:
1. All prerequisites installed
2. Virtual environment activated
3. Backend running on :8000
4. Frontend can reach backend
5. Environment variables set correctly

---

**You're all set! Happy Trading! 🚀📈**
