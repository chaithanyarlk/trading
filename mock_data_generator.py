import json
import random
from datetime import datetime, timedelta
import requests

BASE_URL = "http://localhost:8000"

# Popular Indian stocks
STOCKS = {
    "RELIANCE": {"name": "Reliance Industries", "base_price": 2500},
    "TCS": {"name": "Tata Consultancy Services", "base_price": 3500},
    "INFY": {"name": "Infosys", "base_price": 1400},
    "ICICIBANK": {"name": "ICICI Bank", "base_price": 950},
    "BAJAJFINSV": {"name": "Bajaj Finserv", "base_price": 1500},
}

def generate_mock_market_data():
    """Generate realistic mock market data"""
    market_data = {}
    
    for stock_id, stock_info in STOCKS.items():
        base_price = stock_info["base_price"]
        
        # Generate realistic price series with trend
        prices = []
        volumes = []
        current_price = base_price
        
        for i in range(30):
            # Random walk with slight uptrend
            change = random.uniform(-1, 2)  # Slight uptrend bias
            current_price = max(base_price * 0.9, current_price + change)
            prices.append(current_price)
            
            # Volume with some spikes
            base_volume = 1000000
            spike = 0.5 if random.random() < 0.2 else 1.0
            volume = base_volume * random.uniform(0.8, 1.3) * spike
            volumes.append(volume)
        
        market_data[stock_id] = {
            "name": stock_info["name"],
            "prices": prices,
            "volumes": volumes,
            "current_price": prices[-1] if prices else base_price
        }
    
    return market_data

def generate_signals(market_data):
    """Request signal generation from backend"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/signals/generate",
            json=market_data,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error generating signals: {e}")
        return []

def execute_mock_trades(signals):
    """Execute mock trades on high-confidence signals"""
    executed = []
    
    for signal in signals:
        # Only execute high-confidence signals
        if signal.get("confidence", 0) >= 0.7:
            try:
                quantity = signal.get("recommended_quantity", 10)
                
                response = requests.post(
                    f"{BASE_URL}/api/trades/execute",
                    json={
                        "signal": signal,
                        "quantity": quantity
                    },
                    timeout=10
                )
                response.raise_for_status()
                
                result = response.json()
                executed.append({
                    "asset": signal["asset_name"],
                    "action": signal["action"],
                    "quantity": quantity,
                    "price": signal["price"],
                    "success": result.get("success", False),
                    "message": result.get("message", "")
                })
                
                print(f"✓ Executed {signal['action']} for {signal['asset_name']}")
            except Exception as e:
                print(f"✗ Failed to execute trade: {e}")
        else:
            print(f"⊘ Skipped {signal['asset_name']} (confidence: {signal.get('confidence', 0):.2%})")
    
    return executed

def get_portfolio_status():
    """Fetch current portfolio status"""
    try:
        response = requests.get(f"{BASE_URL}/api/portfolio", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching portfolio: {e}")
        return None

def get_performance_metrics():
    """Fetch performance metrics"""
    try:
        response = requests.get(f"{BASE_URL}/api/performance", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching performance: {e}")
        return None

def run_trading_simulation(num_cycles=5, delay_seconds=5):
    """Run multiple trading cycles with delay"""
    print(f"\n{'='*60}")
    print(f"🚀 Starting Mock Trading Simulation")
    print(f"{'='*60}\n")
    
    for cycle in range(1, num_cycles + 1):
        print(f"\n--- Cycle {cycle} of {num_cycles} ---\n")
        
        # Generate market data
        print("📊 Generating market data...")
        market_data = generate_mock_market_data()
        
        # Generate signals
        print("🔍 Analyzing markets...")
        signals = generate_signals(market_data)
        
        if not signals:
            print("⚠️ No signals generated")
            continue
        
        print(f"📈 Generated {len(signals)} signals")
        for signal in signals:
            print(f"  • {signal['asset_name']}: {signal['action']} "
                  f"(${signal['price']:.2f}, {signal['confidence']:.0%})")
        
        # Execute trades
        print("\n💹 Executing trades...")
        executed = execute_mock_trades(signals)
        
        # Get portfolio status
        print("\n💼 Portfolio Status:")
        portfolio = get_portfolio_status()
        if portfolio:
            print(f"  Total Value: ₹{portfolio['total_value']:,.0f}")
            print(f"  Holdings: {len(portfolio['holdings'])}")
            if portfolio['unrealized_pnl'] != 0:
                print(f"  P&L: ₹{portfolio['unrealized_pnl']:,.0f}")
        
        # Get performance
        metrics = get_performance_metrics()
        if metrics and metrics['total_trades'] > 0:
            print(f"\n📊 Performance Metrics:")
            print(f"  Total Trades: {metrics['total_trades']}")
            print(f"  Win Rate: {metrics['win_rate']:.1f}%")
            if metrics['net_profit'] != 0:
                print(f"  Net Profit: ₹{metrics['net_profit']:,.0f}")
                print(f"  ROI: {metrics['roi']:.2f}%")
        
        if cycle < num_cycles:
            print(f"\n⏳ Waiting {delay_seconds}s before next cycle...")
            # In real usage: time.sleep(delay_seconds)

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Mock data generator and trading simulator"
    )
    parser.add_argument(
        "--cycles",
        type=int,
        default=5,
        help="Number of trading cycles (default: 5)"
    )
    parser.add_argument(
        "--url",
        type=str,
        default="http://localhost:8000",
        help="Backend URL (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run single test cycle"
    )
    
    args = parser.parse_args()
    
    global BASE_URL
    BASE_URL = args.url
    
    cycles = 1 if args.test else args.cycles
    
    try:
        run_trading_simulation(num_cycles=cycles)
    except KeyboardInterrupt:
        print("\n\n⛔ Simulation interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
