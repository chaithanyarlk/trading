# 🚀 AI Trading Platform - Complete Setup Guide

## **Quick Start (with Ollama + Qwen 3.5)**

### **Step 1: Install Ollama** ✓
```bash
# Visit https://ollama.ai or https://github.com/ollama/ollama
# Download and install Ollama for macOS

# After installation, start Ollama in a terminal:
ollama serve

# In another terminal, pull Qwen 3.5 (or your preferred model):
ollama pull qwen2.5  # ~8GB
# OR alternatively:
ollama pull qwen:latest
ollama pull llama2
ollama pull mistral
```

### **Step 2: Start the Backend API**
```bash
cd /Users/hari/Desktop/copilot_trade/backend

# Use the venv that already has all dependencies
/Users/hari/Desktop/copilot_trade/backend/venv/bin/python main.py
```

The backend will:
- ✅ Connect to Ollama at `http://localhost:11434`
- ✅ Use Qwen 3.5 for AI analysis (configured in `.env`)
- ✅ Initialize the database
- ✅ Start the scheduler for end-of-day reports
- ✅ Launch API at `http://localhost:8000`

### **Step 3: Launch the Frontend Dashboard**
```bash
# Option A: Using the provided script
bash /Users/hari/Desktop/copilot_trade/frontend-start.sh

# Option B: Manual
cd /Users/hari/Desktop/copilot_trade/frontend
npm install  # First time only
npm start    # Starts at http://localhost:3000
```

---

## **Configuration Options**

### **Use Ollama (Local - RECOMMENDED)**
Edit `/Users/hari/Desktop/copilot_trade/backend/.env`:
```env
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:latest  # Or llama2, mistral, etc.
```

### **Use Anthropic Claude (Cloud)**
Edit `/Users/hari/Desktop/copilot_trade/backend/.env`:
```env
AI_PROVIDER=anthropic
CLAUDE_API_KEY=sk-your-key-here
CLAUDE_MODEL=claude-3-5-sonnet-20241022
```

---

## **Available Ollama Models**

| Model | Size | Speed | Quality | Command |
|-------|------|-------|---------|---------|
| **qwen2.5** | 8GB | ⚡⚡⚡ | ⭐⭐⭐⭐ | `ollama pull qwen2.5` |
| **llama2** | 4GB | ⚡⚡⚡⚡ | ⭐⭐⭐ | `ollama pull llama2` |
| **mistral** | 5GB | ⚡⚡⚡ | ⭐⭐⭐⭐ | `ollama pull mistral` |
| **neural-chat** | 8GB | ⚡⚡⚡ | ⭐⭐⭐⭐ | `ollama pull neural-chat` |

---

## **API Endpoints**

### **View Current AI Provider**
```bash
curl http://localhost:8000/api/ai/provider
```

Response:
```json
{
  "status": "active",
  "provider": "ollama",
  "model": "qwen2.5:latest",
  "base_url": "http://localhost:11434"
}
```

### **Interactive API Documentation**
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## **Troubleshooting**

### **"Cannot connect to Ollama"**
```bash
# Make sure Ollama is running in another terminal
ollama serve

# Check if Ollama is responding
curl http://localhost:11434/api/tags
```

### **"Model not found: qwen2.5:latest"**
```bash
# Pull the model first
ollama pull qwen2.5

# List available models
ollama list
```

### **Slow Response (model is loading)**
- First request after startup may take 10-30 seconds as the model loads into memory
- Subsequent requests are faster

### **Switch back to Anthropic Claude**
```env
AI_PROVIDER=anthropic
CLAUDE_API_KEY=your_key_here
```

---

## **Portfolio Management**

### **Check Portfolio**
```bash
curl http://localhost:8000/api/portfolio
```

### **View Performance**
```bash
curl http://localhost:8000/api/performance
```

### **Start Paper Trading**
```bash
curl -X POST http://localhost:8000/api/trades/execute
```

---

## **System Architecture** 

```
┌─────────────────────────────────────────────┐
│     React Dashboard (Port 3000)             │
│  • Real-time charts & portfolio tracking    │
│  • Trade execution interface               │
│  • Performance analytics                   │
└──────────────────┬──────────────────────────┘
                   │ HTTP/WebSocket
┌──────────────────▼──────────────────────────┐
│     FastAPI Backend (Port 8000)             │
├──────────────────────────────────────────────┤
│  40+ Endpoints for all trading functions    │
└──────────────────┬──────────────────────────┘
                   │
        ┌──────────┼──────────┐
        │          │          │
        ▼          ▼          ▼
    ┌────────┬──────────┬──────────┐
    │ Ollama │ SQLite   │ Groww    │
    │ (AI)   │ Database │ API      │
    └────────┴──────────┴──────────┘
```

---

## **File Structure**

```
copilot_trade/
├── backend/
│   ├── main.py                 # FastAPI app entry point
│   ├── requirements.txt         # Python dependencies
│   ├── .env                     # Configuration (edit this!)
│   └── app/
│       ├── api/routes.py        # 40+ API endpoints
│       ├── services/
│       │   ├── ai_provider.py   # ✨ NEW: Unified AI provider (Anthropic/Ollama)
│       │   ├── ai_analysis_advanced.py    # Stock analysis
│       │   ├── options_trading_engine.py  # Options strategies
│       │   ├── paper_trading_advanced.py  # Paper trading simulation
│       │   ├── mutual_fund_analyzer.py    # Fund recommendations
│       │   ├── orchestrator.py            # Scheduler (3:30 PM EOD)
│       │   └── ... (8 services total)
│       ├── models/
│       │   ├── database.py      # 12 SQLAlchemy tables
│       │   └── schemas.py       # Pydantic models
│       └── core/
│           ├── config.py        # Settings & environment
│           └── database.py      # SQLAlchemy engine
│
├── frontend/
│   ├── src/                    # React components
│   ├── public/                 # Static assets
│   ├── package.json            # npm dependencies
│   └── tailwind.config.js      # Tailwind CSS config
│
├── frontend-start.sh           # ✨ NEW: Frontend startup script
└── SETUP_GUIDE.md             # This file!
```

---

## **Key Features**

✅ **Dual AI Support**: Switch between Claude API (cloud) or Ollama (local)  
✅ **9 Service Modules**: Complete trading ecosystem  
✅ **40+ REST Endpoints**: Full CRUD operations  
✅ **12 Database Tables**: Comprehensive data tracking  
✅ **Real-time Scheduler**: EOD reports at 3:30 PM IST  
✅ **Paper Trading**: Risk-free testing with ₹1M capital  
✅ **Explainable AI**: Every trade has detailed reasoning  
✅ **Options Trading**: 7 AI-driven strategies  
✅ **React Dashboard**: Beautiful UI with real-time charts  

---

## **Next Steps**

1. **Install Ollama** and pull a model
2. **Start backend**: `python backend/main.py`
3. **Start frontend**: `bash frontend-start.sh`
4. **Access dashboard**: http://localhost:3000
5. **Read API docs**: http://localhost:8000/docs
6. **Configure API keys** (.env) for Groww integration

Happy trading! 🚀📈
