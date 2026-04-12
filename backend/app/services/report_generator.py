"""
AITrading Report Generator
Generates end-of-day reports with tables, graphs, and insights
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime, date
import json
from dataclasses import dataclass
import anthropic
from app.core.config import settings

logger = logging.getLogger(__name__)

@dataclass
class ReportData:
    """Data structure for report generation"""
    report_date: date
    trades_executed: List[Dict]
    strategies_used: Dict
    portfolio_performance: Dict
    daily_pnl: float
    insights: List[str]

class ReportGenerator:
    """
    Comprehensive trading report generator
    Creates end-of-day reports with graphs and insights
    """
    
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.CLAUDE_API_KEY)
        self.model = settings.CLAUDE_MODEL
    
    async def generate_daily_report(
        self,
        trades: List[Dict],
        portfolio: Dict,
        initial_portfolio: Dict,
        market_data: Dict
    ) -> Dict:
        """
        Generate comprehensive end-of-day report
        
        Returns: {
            "report_date": "2026-04-12",
            "summary": {...},
            "trades_table": {...},
            "performance_metrics": {...},
            "insights": [...],
            "recommendations": [...],
            "graphs_data": {...}
        }
        """
        
        try:
            # Calculate daily metrics
            daily_pnl = portfolio["total_pnl"] - initial_portfolio.get("total_pnl", 0)
            daily_pnl_percent = (daily_pnl / initial_portfolio.get("total_value", 1)) * 100 if initial_portfolio.get("total_value") else 0
            
            # Separate winning and losing trades
            profit_trades = [t for t in trades if t.get("pnl", 0) > 0]
            loss_trades = [t for t in trades if t.get("pnl", 0) < 0]
            
            # Generate AI insights
            insights = await self._generate_ai_insights(
                trades, portfolio, daily_pnl, daily_pnl_percent, market_data
            )
            
            report = {
                "report_date": datetime.utcnow().date().isoformat(),
                "report_time": datetime.utcnow().isoformat(),
                "summary": {
                    "total_trades": len(trades),
                    "profit_trades": len(profit_trades),
                    "loss_trades": len(loss_trades),
                    "win_rate": f"{(len(profit_trades) / len(trades) * 100):.1f}%" if trades else "0%",
                    "daily_pnl": daily_pnl,
                    "daily_pnl_percent": daily_pnl_percent,
                    "portfolio_value": portfolio["total_value"],
                    "cash_balance": portfolio["cash_balance"]
                },
                "trades_table": self._create_trades_table(trades),
                "performance_comparison": {
                    "start_of_day": initial_portfolio,
                    "end_of_day": portfolio,
                    "change": {
                        "value_change": portfolio["total_value"] - initial_portfolio.get("total_value", 0),
                        "pnl_change": daily_pnl,
                        "percentage_change": daily_pnl_percent
                    }
                },
                "strategy_analysis": self._analyze_strategy_performance(trades),
                "ai_insights": insights,
                "key_observations": self._extract_key_observations(trades, portfolio),
                "mistakes_and_lessons": await self._analyze_mistakes(trades, profit_trades, loss_trades),
                "tomorrow_watchlist": await self._generate_watchlist(market_data),
                "graphs_data": self._prepare_graph_data(trades, portfolio),
                "recommendations": await self._generate_recommendations(
                    trades, portfolio, daily_pnl, insights
                )
            }
            
            return report
        except Exception as e:
            logger.error(f"Error generating daily report: {e}")
            return {
                "error": str(e),
                "report_date": datetime.utcnow().date().isoformat()
            }
    
    async def _generate_ai_insights(
        self,
        trades: List[Dict],
        portfolio: Dict,
        daily_pnl: float,
        daily_pnl_percent: float,
        market_data: Dict
    ) -> List[str]:
        """Generate AI-driven insights using Claude"""
        
        try:
            trade_summary = f"""
Total Trades: {len(trades)}
Daily P&L: ₹{daily_pnl:,.0f} ({daily_pnl_percent:.2f}%)
Portfolio Value: ₹{portfolio['total_value']:,.0f}
"""
            
            for trade in trades[:5]:  # First 5 trades
                trade_summary += f"\n- {trade.get('symbol')}: {trade.get('action')} {trade.get('quantity')} @ ₹{trade.get('price'):.2f}"
            
            prompt = f"""
Analyze this trading day and provide 3-5 key insights:

=== DAILY SUMMARY ===
{trade_summary}

Market Sentiment: {market_data.get('sentiment', 'Neutral')}
Market Advance/Decline: {market_data.get('ad_ratio', 'N/A')}

Provide concise, actionable insights about:
1. What worked well today
2. What could be improved
3. Pattern recognition if any
4. Market observations
5. Tomorrow's setup

Keep each insight to 1-2 sentences, actionable and specific.
"""
            
            message = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            response_text = message.content[0].text
            
            # Extract insights from response
            lines = response_text.split('\n')
            insights = [line.strip() for line in lines if line.strip() and len(line.strip()) > 20][:5]
            
            return insights if insights else [response_text]
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return ["Daily trading completed. Review trades for patterns."]
    
    def _create_trades_table(self, trades: List[Dict]) -> Dict:
        """Create formatted trades table data"""
        
        table_rows = []
        for trade in trades:
            row = {
                "timestamp": trade.get("timestamp", "N/A"),
                "symbol": trade.get("symbol"),
                "action": trade.get("action"),
                "quantity": trade.get("quantity"),
                "price": f"₹{trade.get('price', 0):.2f}",
                "value": f"₹{trade.get('value', 0):,.0f}",
                "pnl": f"₹{trade.get('pnl', 0):,.0f}",
                "pnl_percent": f"{trade.get('pnl_percent', 0):.2f}%" if "pnl_percent" in trade else "N/A",
                "status": trade.get("status", "UNKNOWN")
            }
            table_rows.append(row)
        
        return {
            "headers": ["Time", "Symbol", "Action", "Qty", "Price", "Value", "P&L", "P&L %", "Status"],
            "rows": table_rows,
            "total_rows": len(table_rows)
        }
    
    def _analyze_strategy_performance(self, trades: List[Dict]) -> Dict:
        """Analyze performance by strategy"""
        
        strategies = {}
        
        for trade in trades:
            strategy = trade.get("strategy", "Unnamed")
            if strategy not in strategies:
                strategies[strategy] = {
                    "trades": 0,
                    "profit_trades": 0,
                    "loss_trades": 0,
                    "total_pnl": 0,
                    "win_rate": 0
                }
            
            strategies[strategy]["trades"] += 1
            if trade.get("pnl", 0) > 0:
                strategies[strategy]["profit_trades"] += 1
            elif trade.get("pnl", 0) < 0:
                strategies[strategy]["loss_trades"] += 1
            
            strategies[strategy]["total_pnl"] += trade.get("pnl", 0)
        
        # Calculate win rates
        for strategy in strategies:
            total = strategies[strategy]["trades"]
            strategies[strategy]["win_rate"] = (
                strategies[strategy]["profit_trades"] / total * 100 if total > 0 else 0
            )
        
        return strategies
    
    def _extract_key_observations(self, trades: List[Dict], portfolio: Dict) -> List[str]:
        """Extract key observations from trading day"""
        
        observations = []
        
        if not trades:
            observations.append("No trades executed.")
            return observations
        
        # Win rate observation
        profit_trades = len([t for t in trades if t.get("pnl", 0) > 0])
        win_rate = profit_trades / len(trades) * 100
        
        if win_rate >= 70:
            observations.append(f"Excellent win rate: {win_rate:.0f}% of trades were profitable.")
        elif win_rate >= 50:
            observations.append(f"Good trading day: {win_rate:.0f}% win rate achieved.")
        else:
            observations.append(f"Challenging day: Only {win_rate:.0f}% of trades were profitable.")
        
        # Biggest winner and loser
        profitable = [t for t in trades if t.get("pnl", 0) > 0]
        losing = [t for t in trades if t.get("pnl", 0) < 0]
        
        if profitable:
            best_trade = max(profitable, key=lambda x: x.get("pnl", 0))
            observations.append(f"Best trade: {best_trade.get('symbol')} earned ₹{best_trade.get('pnl', 0):,.0f}")
        
        if losing:
            worst_trade = min(losing, key=lambda x: x.get("pnl", 0))
            observations.append(f"Worst trade: {worst_trade.get('symbol')} lost ₹{abs(worst_trade.get('pnl', 0)):,.0f}")
        
        # Portfolio change
        total_pnl = sum([t.get("pnl", 0) for t in trades])
        observations.append(f"Net daily P&L: ₹{total_pnl:,.0f}")
        
        return observations
    
    async def _analyze_mistakes(
        self,
        all_trades: List[Dict],
        profit_trades: List[Dict],
        loss_trades: List[Dict]
    ) -> Dict:
        """Analyze common mistakes and lessons learned"""
        
        try:
            if not loss_trades:
                return {
                    "common_mistakes": ["No losing trades - excellent execution!"],
                    "lessons": ["Continue current strategy"]
                }
            
            loss_summary = f"""
Total Losing Trades: {len(loss_trades)}
Total Loss: ₹{sum([t.get('pnl', 0) for t in loss_trades]):,.0f}

Recent Losses:
"""
            for trade in loss_trades[:3]:
                loss_summary += f"\n- {trade.get('symbol')}: ₹{trade.get('pnl', 0):,.0f}"
            
            prompt = f"""
Analyze these trading mistakes and provide lessons:

{loss_summary}

What were the common mistake patterns?
What could have been done differently?
What's the key lesson from these losses?

Provide 2-3 actionable mistakes and 2-3 lessons learned.
"""
            
            message = self.client.messages.create(
                model=self.model,
                max_tokens=400,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            response = message.content[0].text
            return {
                "analysis": response,
                "losing_trades_count": len(loss_trades),
                "total_losses": sum([t.get("pnl", 0) for t in loss_trades])
            }
        except Exception as e:
            logger.error(f"Error analyzing mistakes: {e}")
            return {
                "analysis": "Unable to generate analysis",
                "losing_trades_count": len(loss_trades)
            }
    
    async def _generate_watchlist(self, market_data: Dict) -> List[Dict]:
        """Generate watch list for tomorrow"""
        
        try:
            prompt = f"""
Based on today's market conditions, suggest 5 stocks to watch tomorrow:

Market Sentiment Today: {market_data.get('sentiment', 'Neutral')}
Market Breadth: {market_data.get('ad_ratio', 'N/A')}
VIX Level: {market_data.get('vix', 'N/A')}

For each recommendation:
- Stock name
- Why to watch
- Setup to look for

JSON format:
[
  {{
    "symbol": "...",
    "reason": "...",
    "setup": "..."
  }}
]
"""
            
            message = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            response_text = message.content[0].text
            
            try:
                json_start = response_text.find('[')
                json_end = response_text.rfind(']') + 1
                watchlist = json.loads(response_text[json_start:json_end])
                return watchlist
            except:
                return []
        except Exception as e:
            logger.error(f"Error generating watchlist: {e}")
            return []
    
    def _prepare_graph_data(self, trades: List[Dict], portfolio: Dict) -> Dict:
        """Prepare data for graph visualization"""
        
        # Cumulative P&L
        cumulative_pnl = []
        running_pnl = 0
        pnl_timestamps = []
        
        for trade in sorted(trades, key=lambda x: x.get("timestamp", "")):
            if trade.get("action") == "SELL":
                running_pnl += trade.get("pnl", 0)
            cumulative_pnl.append(running_pnl)
            pnl_timestamps.append(trade.get("timestamp", ""))
        
        # Hourly performance
        hourly_pnl = {}
        for trade in trades:
            if trade.get("timestamp"):
                hour = trade["timestamp"].split("T")[1][:2]  # Extract hour
                if hour not in hourly_pnl:
                    hourly_pnl[hour] = 0
                if trade.get("action") == "SELL":
                    hourly_pnl[hour] += trade.get("pnl", 0)
        
        return {
            "cumulative_pnl": {
                "values": cumulative_pnl,
                "timestamps": pnl_timestamps
            },
            "hourly_pnl": {
                "hours": list(hourly_pnl.keys()),
                "values": list(hourly_pnl.values())
            },
            "portfolio_allocation": portfolio
        }
    
    async def _generate_recommendations(
        self,
        trades: List[Dict],
        portfolio: Dict,
        daily_pnl: float,
        insights: List[str]
    ) -> List[str]:
        """Generate recommendations for tomorrow"""
        
        try:
            if daily_pnl > 0:
                trend = "profitable"
            elif daily_pnl < 0:
                trend = "loss-making"
            else:
                trend = "neutral"
            
            prompt = f"""
Based on today's {trend} trading day, provide 3-4 recommendations for tomorrow:

Daily P&L: ₹{daily_pnl:,.0f}
Trades: {len(trades)}
Portfolio Value: ₹{portfolio['total_value']:,.0f}

Insights from today:
{chr(10).join(insights[:3])}

Provide specific, actionable recommendations for tomorrow trading.
"""
            
            message = self.client.messages.create(
                model=self.model,
                max_tokens=300,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            response = message.content[0].text
            recommendations = response.split('\n')
            return [r.strip() for r in recommendations if r.strip() and len(r.strip()) > 10][:4]
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return ["Review today's trades", "Identify patterns", "Plan tomorrow's strategy"]
    
    def export_report_as_html(self, report: Dict) -> str:
        """Export report as HTML"""
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Trading Report - {report.get('report_date')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
        .summary {{ background-color: #e8f4f8; padding: 15px; border-radius: 5px; }}
        .positive {{ color: green; }}
        .negative {{ color: red; }}
    </style>
</head>
<body>
    <h1>Daily Trading Report - {report.get('report_date')}</h1>
    
    <div class="summary">
        <h2>Summary</h2>
        <p>Total Trades: {report['summary']['total_trades']}</p>
        <p>Winning Trades: {report['summary']['profit_trades']}</p>
        <p>Losing Trades: {report['summary']['loss_trades']}</p>
        <p>Win Rate: {report['summary']['win_rate']}</p>
        <p class="{'positive' if report['summary']['daily_pnl'] > 0 else 'negative'}">
            Daily P&L: ₹{report['summary']['daily_pnl']:,.0f} ({report['summary']['daily_pnl_percent']:.2f}%)
        </p>
    </div>
    
    <h2>Trades</h2>
    <table>
        <tr>
"""
        
        # Add headers
        for header in report['trades_table']['headers']:
            html += f"<th>{header}</th>"
        html += "</tr>"
        
        # Add rows
        for row in report['trades_table']['rows']:
            html += "<tr>"
            for header in report['trades_table']['headers']:
                html += f"<td>{row.get(header.lower(), 'N/A')}</td>"
            html += "</tr>"
        
        html += """
    </table>
    
    <h2>AI Insights</h2>
    <ul>
"""
        for insight in report.get('ai_insights', []):
            html += f"<li>{insight}</li>"
        
        html += """
    </ul>
    
    <h2>Recommendations</h2>
    <ul>
"""
        for rec in report.get('recommendations', []):
            html += f"<li>{rec}</li>"
        
        html += """
    </ul>
</body>
</html>
"""
        
        return html
    
    def export_report_as_json(self, report: Dict) -> str:
        """Export report as JSON"""
        return json.dumps(report, indent=2, default=str)

# Global instance
report_generator: Optional[ReportGenerator] = None

async def get_report_generator() -> ReportGenerator:
    """Get or create report generator"""
    global report_generator
    if not report_generator:
        report_generator = ReportGenerator()
    return report_generator
