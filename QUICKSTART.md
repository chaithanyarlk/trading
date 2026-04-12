# Quick Start Guide

Get the AI Trading System running in 5 minutes.

## Option 1: Docker (Recommended)

### Requirements
- Docker and Docker Compose installed

### Run

```bash
cd /Users/hari/Desktop/copilot_trade

# Start both frontend and backend
docker-compose up

# Access dashboard
# Frontend: http://localhost:3000
# Backend: http://localhost:8000/docs
```

That's it! Everything runs in containers.

---

## Option 2: Manual Setup

### Step 1: Backend (Terminal 1)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

### Step 2: Frontend (Terminal 2)

```bash
cd frontend
npm install
npm start
```

### Access Dashboard

- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs

---

## Option 3: Generate Test Data

In a third terminal:

```bash
cd /Users/hari/Desktop/copilot_trade

# Generate mock trading signals
python mock_data_generator.py --cycles 5

# Or test just once
python mock_data_generator.py --test
```

---

## 🎮 First Trade

1. **Open Dashboard**: http://localhost:3000
2. **Generate Signals**: See sample stocks
3. **Execute Trades**: Click "Execute" on high-confidence signals
4. **Monitor Portfolio**: Watch P&L update in real-time
5. **Review Metrics**: Check win rate and performance

---

## 📊 Next Steps

1. **Review README.md**: Full system documentation
2. **Read SETUP.md**: Detailed setup instructions
3. **Explore API**: http://localhost:8000/docs
4. **Try Paper Trading**: Execute 10+ mock trades
5. **Enable Live Trading**: Only after gaining confidence

---

## ⚡ Useful Commands

```bash
# Check backend health
curl http://localhost:8000/health

# Generate signals
curl -X POST http://localhost:8000/api/signals/generate \
  -H "Content-Type: application/json" \
  -d '{"RELIANCE": {"prices": [2500, 2510, 2520], "volumes": [1000000, 1200000, 1100000], "current_price": 2520, "name": "Reliance"}}'

# Get portfolio
curl http://localhost:8000/api/portfolio

# Get performance
curl http://localhost:8000/api/performance

# Get stocks to watch
curl http://localhost:8000/api/stocks/watch

# Get mutual fund recommendations
curl http://localhost:8000/api/mutual-funds/recommendations

# Get options suggestions
curl http://localhost:8000/api/options/suggestions?underlying=TCS&current_price=3500
```

---

## 🐛 Quick Fixes

**Backend won't start?**
```bash
pip install --force-reinstall ta-lib
```

**Frontend won't connect?**
```bash
# Verify backend is running
curl http://localhost:8000/health
```

**Port already in use?**
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or use different port
PORT=3001 npm start
```

---

## 📁 Project Structure

```
copilot_trade/
├── README.md              # Full documentation
├── SETUP.md              # Detailed setup
├── QUICKSTART.md         # This file
├── mock_data_generator.py # Test data tool
├── docker-compose.yml    # Docker setup
├── Dockerfile.backend    # Backend container
├── Dockerfile.frontend   # Frontend container
├── backend/              # Python FastAPI
│   ├── main.py
│   ├── requirements.txt
│   ├── .env
│   └── app/
├── frontend/             # React dashboard
│   ├── package.json
│   ├── src/
│   └── public/
└── ...
```

---

## ✨ Features at a Glance

✅ Real-time technical analysis
✅ Multi-indicator signal generation
✅ Paper trading simulator
✅ Live trading mode (optional)
✅ Portfolio tracking
✅ Performance metrics
✅ Equity curve visualization
✅ Options strategies
✅ Mutual fund recommendations
✅ Risk management
✅ Audit trails

---

## 🚀 You're Ready!

- Dashboard loads? ✓
- Signals generating? ✓
- Trades executing? ✓
- Portfolio updating? ✓

**Happy trading!** 📈

---

## 📞 Need Help?

1. Check `README.md` for detailed docs
2. Read `SETUP.md` for troubleshooting
3. Review logs in terminal
4. Test with mock data generator
5. Check API documentation at `/docs`

---

**Built with Claude AI| Designed for Learning| Not for Real Trading**

⚠️ **Disclaimer**: This system is for educational purposes only. Use at your own risk. Always verify signals before any real trading.
