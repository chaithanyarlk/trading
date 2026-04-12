"""
Mutual Fund Intelligence & Recommendation Engine
Analyzes funds, predicts performance, and provides AI-driven recommendations
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime
import anthropic
from app.core.config import settings
import json

logger = logging.getLogger(__name__)

class MutualFundAnalyzer:
    """
    AI-powered mutual fund analyzer
    Analyzes funds and provides intelligent recommendations
    """
    
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.CLAUDE_API_KEY)
        self.model = settings.CLAUDE_MODEL
        self.cache = {}
    
    async def analyze_fund(self, fund_data: Dict) -> Dict:
        """
        Comprehensive AI analysis of a mutual fund
        
        Returns: {
            "fund_name": "Axis Bluechip Fund",
            "rating": 5,
            "recommendation": "STRONG BUY",
            "analysis": {...},
            "risks": [...],
            "opportunities": [...]
        }
        """
        
        try:
            prompt = f"""
Analyze this mutual fund and provide investment recommendation:

=== FUND DETAILS ===
Fund Name: {fund_data.get('fund_name')}
Category: {fund_data.get('category')}
Fund Type: {fund_data.get('fund_type', 'Regular')}

=== PERFORMANCE ===
Current NAV: ₹{fund_data.get('nav')}
1-Year Return: {fund_data.get('return_1y', 0):.2f}%
3-Year Return: {fund_data.get('return_3y', 0):.2f}%
5-Year Return: {fund_data.get('return_5y', 0):.2f}%

=== FUND METRICS ===
AUM: ₹{fund_data.get('aum', 0)/10000000:.0f} Cr
Expense Ratio: {fund_data.get('expense_ratio', 0):.2f}%
Fund Manager: {fund_data.get('fund_manager', 'Not specified')}
Inception Date: {fund_data.get('inception_date', 'N/A')}

=== RISK METRICS ===
Risk Rating: {fund_data.get('risk_rating', 3)}/5
Downside Deviation: {fund_data.get('downside_deviation', 'N/A')}
Sortino Ratio: {fund_data.get('sortino_ratio', 'N/A')}
Beta: {fund_data.get('beta', 'N/A')}

=== PORTFOLIO ===
Top Holdings: {', '.join(fund_data.get('top_holdings', []))}

Provide:
1. **Overall Rating** (1-5 stars)
2. **Recommendation** (STRONG BUY, BUY, HOLD, SELL, or AVOID)
3. **Strengths** (why invest in this fund)
4. **Weaknesses** (potential concerns)
5. **Risk Assessment** (specific risks to know)
6. **Ideal Investor** (who should invest)
7. **Investment Horizon** (short/medium/long term)
8. **SIP/Lump Sum** (recommendation on investment approach)

Provide response as JSON.
"""
            
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            response_text = message.content[0].text
            
            try:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                analysis = json.loads(response_text[json_start:json_end])
            except:
                analysis = {"analysis": response_text}
            
            analysis["fund_name"] = fund_data.get("fund_name")
            analysis["analyzed_at"] = datetime.utcnow().isoformat()
            
            return analysis
        except Exception as e:
            logger.error(f"Error analyzing fund: {e}")
            return {
                "fund_name": fund_data.get("fund_name"),
                "error": str(e)
            }
    
    async def recommend_funds(
        self,
        all_funds: List[Dict],
        investment_amount: float,
        horizon: str = "LONG",  # SHORT, MEDIUM, LONG
        risk_profile: str = "BALANCED",  # CONSERVATIVE, BALANCED, AGGRESSIVE
        objective: str = "GROWTH"  # GROWTH, INCOME, BALANCED
    ) -> Dict:
        """
        AI-driven fund recommendation engine
        
        Returns: {
            "recommendations": [...],
            "portfolio_suggestion": {...},
            "expected_return": 12.5,
            "risk_level": "MEDIUM"
        }
        """
        
        try:
            # Prepare fund summary
            fund_summary = f"""
Available Funds: {len(all_funds)}
Top Performers:
{chr(10).join([f"- {f.get('fund_name')}: 1Y={f.get('return_1y', 0):.1f}%, 3Y={f.get('return_3y', 0):.1f}%" for f in sorted(all_funds, key=lambda x: x.get('return_1y', 0), reverse=True)[:5]])}
"""
            
            prompt = f"""
Recommend best mutual funds based on investor profile:

=== INVESTMENT PROFILE ===
Amount: ₹{investment_amount:,.0f}
Time Horizon: {horizon} term {'(1-2 years)' if horizon == 'SHORT' else '(3-5 years)' if horizon == 'MEDIUM' else '(5+ years)'}
Risk Profile: {risk_profile}
Objective: {objective}

=== MARKET CONTEXT ===
{fund_summary}

Task: Recommend 3-5 best mutual funds that match this profile.

For each recommendation:
1. Fund name and category
2. Why recommended for this profile
3. Investment amount suggestion (out of ₹{investment_amount:,.0f})
4. Expected annual return
5. Risk factors specific to this fund

Provide allocation strategy:
- 3-5 recommended funds
- Percentage allocation for each
- Rebalancing frequency
- Expected portfolio return
- Portfolio risk level

Respond with structured JSON:
{{
  "recommendations": [
    {{
      "rank": 1,
      "fund_name": "...",
      "category": "...",
      "allocation_percent": 30,
      "allocation_amount": {investment_amount * 0.3},
      "sip_amount": ...,
      "lump_sum_recommended": true/false,
      "expected_return": 12.5,
      "reasoning": "Why this fund for your profile",
      "holding_period": "Hold for X years"
    }}
  ],
  "portfolio_expected_return": 12.8,
  "portfolio_risk_level": "MODERATE",
  "rebalancing_frequency": "Quarterly/Annually",
  "additional_advice": "Specific tips for this investor profile"
}}
"""
            
            message = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            response_text = message.content[0].text
            
            try:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                recommendations = json.loads(response_text[json_start:json_end])
            except:
                recommendations = {"recommendations": [], "analysis": response_text}
            
            recommendations["investment_profile"] = {
                "amount": investment_amount,
                "horizon": horizon,
                "risk_profile": risk_profile,
                "objective": objective
            }
            recommendations["generated_at"] = datetime.utcnow().isoformat()
            
            return recommendations
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return {
                "error": str(e),
                "investment_profile": {
                    "amount": investment_amount,
                    "horizon": horizon,
                    "risk_profile": risk_profile,
                    "objective": objective
                }
            }
    
    async def create_sip_plan(
        self,
        fund_code: str,
        monthly_amount: float,
        duration_years: int,
        fund_data: Dict
    ) -> Dict:
        """
        Create and analyze SIP (Systematic Investment Plan)
        """
        
        try:
            prompt = f"""
Analyze this SIP investment plan:

=== SIP DETAILS ===
Fund: {fund_data.get('fund_name')}
Category: {fund_data.get('category')}
Monthly Investment: ₹{monthly_amount:,.0f}
Duration: {duration_years} years
Total Investment: ₹{monthly_amount * 12 * duration_years:,.0f}

=== FUND PERFORMANCE ===
Current NAV: ₹{fund_data.get('nav')}
1-Year Return: {fund_data.get('return_1y', 0):.2f}%
3-Year Return: {fund_data.get('return_3y', 0):.2f}%
5-Year Return: {fund_data.get('return_5y', 0):.2f}%

Provide:
1. Why SIP is good for this fund
2. Expected maturity amount (assume historical returns)
3. Benefit vs lump sum investment
4. Risk reduction through SIP
5. When to continue/stop/increase SIP
6. Tax implications

Respond as JSON:
{{
  "total_investment": {monthly_amount * 12 * duration_years},
  "assumed_annual_return": 12.5,
  "expected_maturity_value": ...estimate...,
  "estimated_gains": ...estimate...,
  "expected_gain_percent": ...estimate...,
  "sip_benefits": ["Rupee cost averaging", ...],
  "rupee_cost_averaging_effect": "Explanation",
  "risk_reduction": "How SIP reduces volatility",
  "recommendation": "Analysis of this SIP plan"
}}
"""
            
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            response_text = message.content[0].text
            
            try:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                plan = json.loads(response_text[json_start:json_end])
            except:
                plan = {"analysis": response_text}
            
            plan["sip_parameters"] = {
                "fund_code": fund_code,
                "monthly_amount": monthly_amount,
                "duration_years": duration_years,
                "fund_name": fund_data.get("fund_name")
            }
            plan["created_at"] = datetime.utcnow().isoformat()
            
            return plan
        except Exception as e:
            logger.error(f"Error creating SIP plan: {e}")
            return {
                "error": str(e),
                "sip_parameters": {
                    "fund_code": fund_code,
                    "monthly_amount": monthly_amount,
                    "duration_years": duration_years
                }
            }
    
    def get_fund_comparison(
        self,
        funds: List[Dict]
    ) -> Dict:
        """Compare multiple funds side-by-side"""
        
        if not funds:
            return {"error": "No funds to compare"}
        
        comparison = {
            "comparison_date": datetime.utcnow().isoformat(),
            "funds_compared": len(funds),
            "funds": []
        }
        
        # Extract key metrics
        for fund in funds:
            comparison["funds"].append({
                "name": fund.get("fund_name"),
                "category": fund.get("category"),
                "nav": fund.get("nav"),
                "return_1y": fund.get("return_1y"),
                "return_3y": fund.get("return_3y"),
                "return_5y": fund.get("return_5y"),
                "expense_ratio": fund.get("expense_ratio"),
                "aum": fund.get("aum"),
                "risk_rating": fund.get("risk_rating"),
                "sharpe_ratio": fund.get("sharpe_ratio", "N/A"),
                "sortino_ratio": fund.get("sortino_ratio", "N/A")
            })
        
        # Calculate comparisons
        comparison["best_1y_return"] = max(funds, key=lambda x: x.get("return_1y", 0))["fund_name"]
        comparison["lowest_expense_ratio"] = min(funds, key=lambda x: x.get("expense_ratio", 100))["fund_name"]
        comparison["highest_aum"] = max(funds, key=lambda x: x.get("aum", 0))["fund_name"]
        comparison["lowest_risk"] = min(funds, key=lambda x: x.get("risk_rating", 5))["fund_name"]
        
        return comparison
    
    async def analyze_portfolio_fit(
        self,
        current_funds: List[Dict],
        new_fund: Dict
    ) -> Dict:
        """Analyze if new fund fits well in existing portfolio"""
        
        try:
            prompt = f"""
Analyze if this new fund is a good fit for adding to existing portfolio:

=== CURRENT PORTFOLIO ===
Funds: {', '.join([f.get('fund_name') for f in current_funds])}
Categories: {', '.join(set([f.get('category') for f in current_funds]))}
Average Expense Ratio: {sum([f.get('expense_ratio', 0) for f in current_funds])/len(current_funds):.2f}%
Average Risk: {sum([f.get('risk_rating', 3) for f in current_funds])/len(current_funds):.1f}/5

=== NEW FUND TO ADD ===
Fund: {new_fund.get('fund_name')}
Category: {new_fund.get('category')}
Expense Ratio: {new_fund.get('expense_ratio')}%
Risk Rating: {new_fund.get('risk_rating')}/5
Return 1Y: {new_fund.get('return_1y')}%
Return 3Y: {new_fund.get('return_3y')}%

Assess:
1. Diversification benefit
2. Overlap/redundancy with existing funds
3. Category coverage after addition
4. Whether to ADD, SKIP, or REPLACE

JSON response:
{{
  "recommendation": "ADD/SKIP/REPLACE",
  "diversification_benefit": "explanation",
  "overlap_analysis": "overlap with existing funds",
  "portfolio_improvement": "how it improves portfolio",
  "replacement_candidate": "if REPLACE, which fund"
}}
"""
            
            message = self.client.messages.create(
                model=self.model,
                max_tokens=800,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            response_text = message.content[0].text
            
            try:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                analysis = json.loads(response_text[json_start:json_end])
            except:
                analysis = {"analysis": response_text}
            
            return analysis
        except Exception as e:
            logger.error(f"Error analyzing portfolio fit: {e}")
            return {
                "error": str(e),
                "recommendation": "Manual review needed"
            }

# Global instance
mutual_fund_analyzer: Optional[MutualFundAnalyzer] = None

async def get_mutual_fund_analyzer() -> MutualFundAnalyzer:
    """Get or create mutual fund analyzer"""
    global mutual_fund_analyzer
    if not mutual_fund_analyzer:
        mutual_fund_analyzer = MutualFundAnalyzer()
    return mutual_fund_analyzer
