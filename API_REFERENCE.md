# API Reference - AI Trading Assistant

Complete API documentation with examples.

## Base URL
```
http://localhost:8000
```

## Authentication
Currently no authentication required. In production, add JWT tokens.

---

## Health Check

### Endpoint
```
GET /health
```

### Response
```json
{
  "status": "healthy",
  "timestamp": "2024-04-10T10:30:00",
  "version": "1.0.0"
}
```

### Example
```bash
curl http://localhost:8000/health
```

---

## Trade Signals

### Generate Signals

**Endpoint**
```
POST /api/signals/generate
```

**Request Body**
```json
{
  "RELIANCE": {
    "prices": [2500, 2510, 2520, 2515, 2525, 2535],
    "volumes": [1000000, 1200000, 1100000, 1300000, 1500000, 1400000],
    "current_price": 2535,
    "name": "Reliance Industries"
  },
  "TCS": {
    "prices": [3500, 3510, 3520, 3515, 3525, 3535],
    "volumes": [800000, 900000, 850000, 950000, 1000000, 1100000],
    "current_price": 3535,
    "name": "Tata Consultancy Services"
  }
}
```

**Response**
```json
[
  {
    "asset_id": "RELIANCE",
    "asset_name": "Reliance Industries",
    "asset_type": "STOCK",
    "action": "BUY",
    "price": 2535,
    "confidence": 0.8,
    "indicators": [
      {
        "name": "RSI",
        "value": 45.5,
        "threshold_upper": 70,
        "threshold_lower": 30,
        "signal": "NEUTRAL",
        "confidence": 0.8
      },
      {
        "name": "MACD",
        "value": 15.23,
        "signal": "BUY",
        "confidence": 0.75
      }
    ],
    "reasoning": "Signal generated based on 5 indicators. Buy signals: 3, Sell signals: 2. Bullish momentum detected...",
    "risk_level": "LOW",
    "recommended_quantity": 253,
    "timestamp": "2024-04-10T10:30:00"
  }
]
```

**Example**
```bash
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

---

## Portfolio Management

### Get Portfolio Overview

**Endpoint**
```
GET /api/portfolio
```

**Response**
```json
{
  "total_value": 1050000,
  "total_invested": 1000000,
  "realized_pnl": 0,
  "unrealized_pnl": 50000,
  "cash_balance": 750000,
  "holdings": [
    {
      "asset_id": "RELIANCE",
      "asset_name": "Reliance Industries",
      "quantity": 10,
      "average_cost": 2500,
      "current_price": 2535,
      "current_value": 25350,
      "unrealized_pnl": 350,
      "unrealized_pnl_percent": 1.4
    }
  ],
  "last_updated": "2024-04-10T10:30:00"
}
```

**Example**
```bash
curl http://localhost:8000/api/portfolio
```

---

## Trading

### Execute Trade

**Endpoint**
```
POST /api/trades/execute
```

**Request Body**
```json
{
  "signal": {
    "asset_id": "RELIANCE",
    "asset_name": "Reliance Industries",
    "action": "BUY",
    "price": 2535,
    "confidence": 0.8,
    "recommended_quantity": 10,
    "reasoning": "Bullish signal",
    "risk_level": "LOW"
  },
  "quantity": 10
}
```

**Response**
```json
{
  "success": true,
  "trade": {
    "id": "trade_001",
    "asset_id": "RELIANCE",
    "asset_name": "Reliance Industries",
    "action": "BUY",
    "entry_price": 2535,
    "quantity": 10,
    "timestamp": "2024-04-10T10:30:00",
    "status": "EXECUTED",
    "reasoning": "Bullish signal",
    "confidence": 0.8
  },
  "message": "Buy order executed successfully"
}
```

**Example**
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

---

## Performance Metrics

### Get Performance

**Endpoint**
```
GET /api/performance
```

**Response**
```json
{
  "total_trades": 5,
  "winning_trades": 3,
  "losing_trades": 2,
  "win_rate": 60.0,
  "total_profit": 15000,
  "total_loss": 5000,
  "net_profit": 10000,
  "roi": 1.0,
  "sharpe_ratio": 1.25,
  "max_drawdown": 2.5,
  "average_trade_return": 2000
}
```

**Example**
```bash
curl http://localhost:8000/api/performance
```

---

## Options Trading

### Get Options Suggestions

**Endpoint**
```
GET /api/options/suggestions?underlying=TCS&current_price=3500
```

**Parameters**
- `underlying` (string): Stock symbol
- `current_price` (float): Current stock price

**Response**
```json
[
  {
    "strategy_name": "LONG_CALL",
    "underlying": "TCS",
    "strike_prices": [3570],
    "expiry": "30DTE",
    "risk_reward_ratio": 0.333,
    "max_profit": 999999,
    "max_loss": 200,
    "breakeven": 3770,
    "reasoning": "Moderate bullish outlook. Limited downside risk (option premium), unlimited upside potential."
  },
  {
    "strategy_name": "SHORT_PUT",
    "underlying": "TCS",
    "strike_prices": [3430],
    "expiry": "30DTE",
    "risk_reward_ratio": 0.5,
    "max_profit": 150,
    "max_loss": 342700,
    "breakeven": 3280,
    "reasoning": "Neutral to bullish. Collect premium while waiting for stock to rise."
  }
]
```

**Example**
```bash
curl "http://localhost:8000/api/options/suggestions?underlying=TCS&current_price=3500"
```

---

## Mutual Funds

### Get Mutual Fund Recommendations

**Endpoint**
```
GET /api/mutual-funds/recommendations
```

**Response**
```json
[
  {
    "fund_name": "Axis Bluechip Fund",
    "fund_category": "Large Cap",
    "sip_amount": 5000,
    "lump_sum_amount": 100000,
    "expected_return": 12.5,
    "risk_level": "LOW",
    "reasoning": "Large-cap fund with established track record. Suitable for risk-averse investors..."
  },
  {
    "fund_name": "HDFC Mid-Cap Opportunities Fund",
    "fund_category": "Mid Cap",
    "sip_amount": 5000,
    "lump_sum_amount": 100000,
    "expected_return": 15.0,
    "risk_level": "MEDIUM",
    "reasoning": "Mid-cap fund with growth potential. Suitable for balanced investors..."
  }
]
```

**Example**
```bash
curl http://localhost:8000/api/mutual-funds/recommendations
```

---

## Stocks to Watch

### Get Stocks to Watch

**Endpoint**
```
GET /api/stocks/watch
```

**Response**
```json
[
  {
    "symbol": "RELIANCE",
    "reason": "Strong uptrend, breakout from consolidation",
    "technical_score": 8.2,
    "fundamental_score": 7.5
  },
  {
    "symbol": "TCS",
    "reason": "Support at 3200, positive divergence on RSI",
    "technical_score": 7.8,
    "fundamental_score": 8.0
  }
]
```

**Example**
```bash
curl http://localhost:8000/api/stocks/watch
```

---

## Market Data

### Get Stock Quote

**Endpoint**
```
GET /api/market/quote?symbol=INFY
```

**Parameters**
- `symbol` (string): Stock symbol

**Response** (from broker API)
```json
{
  "symbol": "INFY",
  "price": 1545.50,
  "change": 15.50,
  "change_percent": 1.02,
  "high": 1550,
  "low": 1530,
  "volume": 5000000,
  "market_cap": 6500000000000
}
```

**Example**
```bash
curl "http://localhost:8000/api/market/quote?symbol=INFY"
```

---

### Get Historical Data

**Endpoint**
```
GET /api/market/historical?symbol=INFY&period=1y&interval=1d
```

**Parameters**
- `symbol` (string): Stock symbol
- `period` (string): 1d, 1w, 1m, 3m, 1y, 5y
- `interval` (string): 1m, 5m, 15m, 1h, 1d, 1w, 1m

**Response**
```json
[
  {
    "timestamp": "2024-01-10",
    "open": 1500,
    "high": 1550,
    "low": 1490,
    "close": 1545,
    "volume": 10000000
  },
  {
    "timestamp": "2024-01-11",
    "open": 1545,
    "high": 1560,
    "low": 1540,
    "close": 1555,
    "volume": 12000000
  }
]
```

**Example**
```bash
curl "http://localhost:8000/api/market/historical?symbol=INFY&period=1y&interval=1d"
```

---

## Trading Mode

### Set Trading Mode

**Endpoint**
```
POST /api/trading/mode
```

**Request Body**
```json
{
  "live_mode": false
}
```

**Response**
```json
{
  "mode": "PAPER",
  "message": "Trading mode set to PAPER",
  "timestamp": "2024-04-10T10:30:00"
}
```

**Example**
```bash
# Switch to paper trading
curl -X POST http://localhost:8000/api/trading/mode \
  -H "Content-Type: application/json" \
  -d '{"live_mode": false}'

# Switch to live trading (requires LIVE_TRADING_ENABLED=True)
curl -X POST http://localhost:8000/api/trading/mode \
  -H "Content-Type: application/json" \
  -d '{"live_mode": true}'
```

---

## WebSocket Connection

### Real-Time Trade Stream

**Endpoint**
```
WebSocket ws://localhost:8000/ws/trades
```

**Message Types**

Incoming (from server):
```json
{
  "type": "signal",
  "data": {
    "asset_name": "Reliance",
    "action": "BUY",
    "price": 2535,
    "confidence": 0.8
  }
}
```

**JavaScript Example**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/trades');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Trade signal:', data);
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};
```

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK - Request successful |
| 201 | Created - Resource created |
| 400 | Bad Request - Invalid parameters |
| 403 | Forbidden - Permission denied |
| 404 | Not Found - Resource not found |
| 500 | Server Error - Internal error |
| 503 | Unavailable - Service down |

---

## Rate Limiting

Currently no rate limiting implemented. In production:
- 100 requests/minute for normal users
- 1000 requests/minute for premium users

---

## Batch Operations

### Execute Multiple Trades

```bash
# Not directly supported, but can loop:
for qty in 10 20 30; do
  curl -X POST http://localhost:8000/api/trades/execute \
    -H "Content-Type: application/json" \
    -d "{\"signal\": {...}, \"quantity\": $qty}"
done
```

---

## Pagination

Not implemented yet. Use filters:

```bash
# Get only winning trades (future feature)
curl "http://localhost:8000/api/trades?filter=executed&sort=timestamp"
```

---

## Filtering & Sorting

Not yet implemented. Planned for v1.1:

```bash
# Get trades from last 7 days
curl "http://localhost:8000/api/trades?days=7&sort=-timestamp"

# Get stocks by score
curl "http://localhost:8000/api/stocks/watch?sort=-technical_score"
```

---

## Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

---

## Version History

- **v1.0.0** (Apr 2024): Initial release
  - Technical analysis
  - Paper trading
  - Dashboard UI
  - Options/Mutual funds suggestions

---

## Support

For API issues:
1. Check endpoint URL
2. Verify request body format
3. Check response status code
4. Review error message
5. Check backend logs

---

**API Base URL**: `http://localhost:8000`
**Documentation**: http://localhost:8000/docs
