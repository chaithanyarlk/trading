# 🚀 QUICK REFERENCE - AI Trading Platform

## **STEP-BY-STEP STARTUP** (Do This First!)

### **Terminal 1: Start Ollama** 
```bash
ollama serve
```
Wait for: `Listening on 127.0.0.1:11434`

### **Terminal 2: Download Model** (First time only)
```bash
ollama pull qwen2.5
```
Wait for: `pulling manifest` → `success`

### **Terminal 3: Start Backend API**
```bash
cd /Users/hari/Desktop/copilot_trade/backend
/Users/hari/Desktop/copilot_trade/backend/venv/bin/python main.py
```
Wait for: `Uvicorn running on http://0.0.0.0:8000`

### **Terminal 4: Start Frontend Dashboard**
```bash
bash /Users/hari/Desktop/copilot_trade/frontend-start.sh
```
Wait for: `On Your Network: http://localhost:3000`

---

## **ACCESS YOUR SYSTEM**

| Service | URL | Purpose |
|---------|-----|---------|
| 📊 **Dashboard** | http://localhost:3000 | Main UI - Charts, Portfolio, Trades |
| 📚 **API Docs** | http://localhost:8000/docs | Interactive API Explorer (Swagger) |
| 🤖 **AI Status** | http://localhost:8000/api/ai/provider | Check which AI is active |
| 💬 **Alt Docs** | http://localhost:8000/redoc | Alternative API Documentation |

---

## **CONFIGURATION** 

### **Location:** 
```
/Users/hari/Desktop/copilot_trade/backend/.env
```

### **Current Settings:**
```env
# Use LOCAL Ollama + Qwen 3.5
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:latest
```

### **To Switch to Claude:**
```env
AI_PROVIDER=anthropic
CLAUDE_API_KEY=sk-your-key-here
CLAUDE_MODEL=claude-3-5-sonnet-20241022
```

---

## **USEFUL ENDPOINTS**

### **Check AI Provider is Active**
```bash
curl http://localhost:8000/api/ai/provider | jq .
```

### **Get Portfolio Overview**
```bash
curl http://localhost:8000/api/portfolio | jq .
```

### **List All Available API Endpoints**
```bash
curl http://localhost:8000/docs  # Open in browser
```

---

## **OLLAMA MODELS** (Quick Reference)

```bash
# Popular models to try:
ollama pull qwen2.5        # Recommended (Qwen 3.5)
ollama pull llama2          # Fast and lightweight
ollama pull mistral         # Good quality
ollama pull neural-chat     # Conversational
```

### **Change Model:**
1. Run: `ollama pull mistral`
2. Edit: `.env` → `OLLAMA_MODEL=mistral:latest`
3. Restart backend

---

## **TROUBLESHOOTING** 

### **"Connection refused" (Ollama)**
```bash
# Make sure Ollama is running!
# Terminal 1 should show: ollama serve
# If not, run: ollama serve
```

### **"Model not found"**
```bash
# Pull the model first
ollama pull qwen2.5

# List what you have
ollama list
```

### **Slow first response**
- Normal! Model is loading into memory
- First request: 10-30 seconds
- Subsequent requests: 1-5 seconds

### **Frontend won't start**
```bash
# Install dependencies
cd /Users/hari/Desktop/copilot_trade/frontend
npm install
npm start
```

---

## **FILE STRUCTURE** (Key Files)

```
/Users/hari/Desktop/copilot_trade/
├── backend/
│   ├── .env                           ← EDIT THIS for configuration
│   ├── main.py                        ← START THIS: python main.py
│   ├── app/
│   │   ├── services/ai_provider.py    ← NEW: Unified AI provider
│   │   ├── services/ai_analysis_advanced.py
│   │   └── api/routes.py
│   └── requirements.txt
│
├── frontend/
│   ├── src/                           ← React components
│   └── package.json
│
└── frontend-start.sh                  ← RUN THIS: bash frontend-start.sh
```

---

## **SYSTEM STATUS CHECK**

### **Is everything running?**

Test each component:

```bash
# 1. Backend API
curl http://localhost:8000/health

# 2. AI Provider (Ollama or Claude)
curl http://localhost:8000/api/ai/provider

# 3. Frontend (open in browser)
open http://localhost:3000
```

**Expected Outputs:**
```json
✅ Backend:
{"status":"healthy","timestamp":"2026-04-12T...","version":"2.0.0"}

✅ AI Provider:
{"status":"active","provider":"ollama","model":"qwen2.5:latest",...}

✅ Frontend:
React dashboard loads in browser
```

---

## **WHAT YOU CAN DO NOW**

✅ **Analyze Stocks** - Get AI recommendations with reasoning  
✅ **Trade Options** - Execute 7 different strategies  
✅ **Paper Trading** - Risk-free with ₹1M capital  
✅ **Portfolio Tracking** - Monitor positions in real-time  
✅ **AI Explanations** - See why every trade is recommended  
✅ **Daily Reports** - Auto-generated at 3:30 PM IST  
✅ **Mutual Funds** - Get AI-powered recommendations  
✅ **Switch AI** - Easily switch between Ollama and Claude  

---

## **NEXT STEPS**

1. ✅ **Follow startup instructions above** (4 terminals)
2. ✅ **Open dashboard** at http://localhost:3000
3. ✅ **Read API docs** at http://localhost:8000/docs
4. ✅ **Configure Groww API** in `.env` for real trading
5. ✅ **Switch models** if desired (ollama pull model-name)

---

## **EXAMPLE WORKFLOW**

```
1. User views dashboard (http://localhost:3000)
   ↓
2. Clicks "Analyze Stock" button
   ↓
3. React frontend calls: POST /api/advanced/analyze
   ↓
4. Backend receives request
   ↓
5. AI Analysis Engine uses:
   - Technical indicators (RSI, MACD, etc.)
   - AI reasoning (Ollama/Claude)
   - Risk assessment
   ↓
6. AI Provider calls Ollama:
   POST http://localhost:11434/api/generate
   with Qwen 3.5 model
   ↓
7. Ollama returns analysis
   ↓
8. Backend formats response:
   {action: "BUY", confidence: 0.85, reasoning: "..."}
   ↓
9. Frontend displays result with charts & explanation
```

---

## **PRO TIPS**

🔥 **Tip 1:** Keep Ollama running in background for faster responses  
🔥 **Tip 2:** First response after restart is slower (model loading)  
🔥 **Tip 3:** Switch models without restarting backend  
🔥 **Tip 4:** Use `ollama list` to see all available models  
🔥 **Tip 5:** Check AI provider status: `curl localhost:8000/api/ai/provider`  

---

## **COMMANDS CHEAT SHEET**

```bash
# Check Ollama status
curl http://localhost:11434/api/tags

# List Ollama models
ollama list

# Pull new model
ollama pull llama2

# Check backend health
curl http://localhost:8000/health

# Check AI provider
curl http://localhost:8000/api/ai/provider

# Stop all (Ctrl+C in each terminal)
```

---

**Ready? Start with Terminal 1 above! 🚀**

Questions? See `OLLAMA_SETUP.md` or `README.md`
