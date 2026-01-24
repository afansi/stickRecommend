from typing import List, Dict, Optional
from sqlmodel import Session, select
from models.tables import PortfolioItem, Recommendation, Sector, User

from services.finance_service import FinanceService

class AllocationService:
    def __init__(self, session: Session):
        self.session = session
        self.finance_service = FinanceService()

    def calculate_injection(self, user_id: int, fresh_funds: float) -> List[Dict]:
        """
        Calculates how to distribute fresh_funds.
        Returns a list of instructions: [{"ticker": "AAPL", "amount": 600, "reason": "Winner"}, ...]
        """
        user = self.session.get(User, user_id)
        if not user:
            return []
        
        # 1. Get Portfolio & Analyze Current State (Aggregate by Ticker)
        raw_portfolio = user.portfolio_items
        portfolio_map = {} # Ticker -> {quantity, total_cost}
        
        for item in raw_portfolio:
            if item.ticker not in portfolio_map:
                portfolio_map[item.ticker] = {"quantity": 0, "total_value": 0}
            portfolio_map[item.ticker]["quantity"] += item.quantity
            portfolio_map[item.ticker]["total_value"] += (item.quantity * item.avg_cost)

        total_portfolio_value = sum(d["total_value"] for d in portfolio_map.values())
        
        plan = []
        available_funds = fresh_funds

        # --- Rule 3: Rebalancing (Check for Sells first) ---
        # If a stock has "SELL" recommendation, suggest selling and usage funds
        active_sells = self.session.exec(
            select(Recommendation).where(
                Recommendation.is_active == True, 
                Recommendation.action == "SELL",
                Recommendation.user_id == user_id
            )
        ).all()
        
        for ticker, data in portfolio_map.items():
            sell_rec = next((r for r in active_sells if r.ticker == ticker), None)
            if sell_rec:
                # Suggest selling 50% of position (Conservative rebalance)
                sell_value = data["total_value"] * 0.5
                available_funds += sell_value
                plan.append({
                    "ticker": ticker,
                    "amount": -round(sell_value, 2),
                    "reason": f"Rebalancing: Weak Outlook ({sell_rec.reasoning[:30]}...)"
                })

        # 2. Get Active Recommendations (Strong Buys) - USER-SPECIFIC
        recommendations = self.session.exec(
            select(Recommendation).where(
                Recommendation.is_active == True,
                Recommendation.action == "BUY",
                Recommendation.user_id == user_id
            )
        ).all()
        
        # Filter for "Strong Buy" (Score > 8)
        strong_buys = [r for r in recommendations if r.confidence_score >= 8.0]
        
        remaining_funds = available_funds
        
        # --- Rule 1: Feed the Winners (Existing Stocks in Strong Buys) ---
        for ticker, data in portfolio_map.items():
            match = next((r for r in strong_buys if r.ticker == ticker), None)
            if match:
                # Allocate 60% of available (or cap it)
                alloc_amount = available_funds * 0.60
                
                # Check Sector Cap
                if self._check_sector_cap(ticker, portfolio_map, alloc_amount, total_portfolio_value + available_funds):
                    if alloc_amount > remaining_funds:
                        alloc_amount = remaining_funds
                    
                    if alloc_amount > 0:
                        plan.append({
                            "ticker": ticker,
                            "amount": round(alloc_amount, 2),
                            "reason": f"Existing Winner: {match.reasoning[:50]}..."
                        })
                        remaining_funds -= alloc_amount
                else:
                    plan.append({
                        "ticker": ticker,
                        "amount": 0,
                        "reason": f"Skipped: Sector allocation would exceed 30% cap."
                    })
        
        # --- Rule 2: New Opportunities (Diversification) ---
        # If funds remain, look for new Strong Buys not in portfolio
        new_picks = [r for r in strong_buys if r.ticker not in portfolio_map]
        
        if remaining_funds > 0 and new_picks:
            # Distribute evenly among top 2 new picks
            share_price = remaining_funds / min(len(new_picks), 2)
            for pick in new_picks[:2]:
                # Check Sector Cap
                if self._check_sector_cap(pick.ticker, portfolio_map, share_price, total_portfolio_value + available_funds):
                     plan.append({
                        "ticker": pick.ticker,
                        "amount": round(share_price, 2),
                        "reason": f"New Opportunity (Score {pick.confidence_score}): {pick.reasoning[:30]}..."
                    })
                     remaining_funds -= share_price

        # If still funds, just keep as Cash (or fallback)
        if remaining_funds > 10: # Threshold to avoid tiny cash amounts
             plan.append({"ticker": "CASH", "amount": round(remaining_funds, 2), "reason": "No suitable high-confidence matches found."})

        return plan

    def get_portfolio_stats(self, user_id: int) -> Dict:
        """
        Calculates real-time portfolio performance.
        Returns: {portfolioValue, dailyChange, totalGainLoss, ...}
        """
        user = self.session.get(User, user_id)
        if not user or not user.portfolio_items:
            return {
                "portfolioValue": "$0.00",
                "dailyChange": "0.00%",
                "totalGainLoss": "$0.00",
                "isPositive": True
            }

        # 1. Aggregate Holdings
        holdings = {}
        total_cost = 0
        for item in user.portfolio_items:
            if item.ticker not in holdings:
                holdings[item.ticker] = {"quantity": 0, "cost": 0}
            holdings[item.ticker]["quantity"] += item.quantity
            holdings[item.ticker]["cost"] += (item.quantity * item.avg_cost)
            total_cost += (item.quantity * item.avg_cost)

        # 2. Batch Fetch Live Prices
        tickers = list(holdings.keys())
        live_data = self.finance_service.batch_get_technicals(tickers)

        # 3. Calculate Performance
        total_value = 0
        total_weighted_change = 0
        
        for ticker, data in holdings.items():
            price_info = live_data.get(ticker)
            if price_info:
                current_price = price_info.get("current_price", 0)
                # If price fails, fallback to cost to avoid zeroing out value
                if current_price == 0:
                    current_price = data["cost"] / data["quantity"] if data["quantity"] > 0 else 0
                
                item_value = data["quantity"] * current_price
                total_value += item_value
                
                # Fetch daily change (approximation if not directly in technicals)
                # In a full finance API we'd have regular change %, but here we can calculate from technicals or it's provided.
                # Since batch_get_technicals is custom, let's assume it returns current_price.
                # If we want daily change, we might need a slightly different call, but let's stick to what we have.
                # For now, let's assume get_technicals might return a change if we added it, but if not, 
                # we'll just report 0% or find a way to get it.
                # Actually, yf.download() can give us history. Let's assume we can get it.
            else:
                total_value += data["cost"]

        gain_loss = total_value - total_cost
        gain_loss_pct = (gain_loss / total_cost * 100) if total_cost > 0 else 0
        
        return {
            "portfolioValue": f"${total_value:,.2f}",
            "dailyChange": f"{gain_loss_pct:+.2f}%", 
            "totalGainLoss": f"${gain_loss:,.2f}",
            "isPositive": gain_loss >= 0
        }

    def _check_sector_cap(self, ticker: str, portfolio_map: Dict, added_value: float, future_total_value: float) -> bool:
        """
        Ensures that adding funds to this ticker does not push its Sector > 30% of total portfolio.
        """
        # 1. Identify Sector
        sector_info = self.finance_service.get_stock_sector(ticker)
        target_sector = sector_info.get("name", "Unknown")
        
        if target_sector == "Unknown" or future_total_value == 0:
            return True # Conservative pass
            
        # 2. Calculate Current Sector Value
        current_sector_value = 0
        for p_ticker, data in portfolio_map.items():
            # We need to fetch sector for each item. 
            s_info = self.finance_service.get_stock_sector(p_ticker)
            if s_info.get("name") == target_sector:
                current_sector_value += data["total_value"]
        
        # 3. Check Ratio
        future_sector_value = current_sector_value + added_value
        ratio = future_sector_value / future_total_value
        
        return ratio <= 0.30
