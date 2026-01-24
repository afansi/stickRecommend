from datetime import datetime, timedelta
from typing import List
from sqlmodel import Session
from models.tables import Alert, User, PortfolioItem, Recommendation
from services.finance_service import FinanceService

class AlertService:
    def __init__(self, session: Session):
        self.session = session
        self.finance_service = FinanceService()

    def generate_alerts_for_portfolio(self, user: User) -> List[Alert]:
        """
        Generate alerts for portfolio holdings:
        1. Upcoming earnings (within 7 days)
        2. Strong price movements (RSI extreme)
        """
        alerts = []
        
        # Aggregate portfolio by ticker
        portfolio_map = {}
        for item in user.portfolio_items:
            if item.ticker not in portfolio_map:
                portfolio_map[item.ticker] = True
        
        for ticker in portfolio_map.keys():
            # Check earnings
            earnings_date = self.finance_service.get_next_earnings_date(ticker)
            if earnings_date:
                try:
                    # Parse date string to datetime
                    from dateutil import parser
                    earnings_dt = parser.parse(earnings_date)
                    days_until = (earnings_dt - datetime.now()).days
                    
                    if 0 <= days_until <= 7:
                        severity = "HIGH" if days_until <= 3 else "MEDIUM"
                        alert = Alert(
                            user_id=user.id,
                            ticker=ticker,
                            message=f"Earnings report in {days_until} day(s) on {earnings_date}",
                            severity=severity
                        )
                        alerts.append(alert)
                        self.session.add(alert)
                except:
                    pass
            
            # Check technicals for extreme movements
            technicals = self.finance_service.get_technicals(ticker)
            if technicals:
                rsi = technicals.get("rsi_14")
                if rsi:
                    if rsi < 30:
                        alert = Alert(
                            user_id=user.id,
                            ticker=ticker,
                            message=f"Oversold (RSI: {rsi:.1f}) - Potential bounce",
                            severity="MEDIUM"
                        )
                        alerts.append(alert)
                        self.session.add(alert)
                    elif rsi > 75:
                        alert = Alert(
                            user_id=user.id,
                            ticker=ticker,
                            message=f"Overbought (RSI: {rsi:.1f}) - Consider taking profits",
                            severity="MEDIUM"
                        )
                        alerts.append(alert)
                        self.session.add(alert)
        
        if alerts:
            self.session.commit()
        
        return alerts
    
    def generate_alerts_from_recommendations(self, user: User, recommendations: List[Recommendation]) -> List[Alert]:
        """
        Generate alerts from high-confidence recommendations.
        """
        alerts = []
        
        for rec in recommendations:
            if rec.confidence_score >= 8.5 and rec.action in ["BUY", "SELL"]:
                severity = "HIGH" if rec.confidence_score >= 9.0 else "MEDIUM"
                
                action_text = "Strong Buy" if rec.action == "BUY" else "Sell Signal"
                alert = Alert(
                    user_id=user.id,
                    ticker=rec.ticker,
                    message=f"{action_text} ({rec.confidence_score}/10): {rec.reasoning[:50]}...",
                    severity=severity
                )
                alerts.append(alert)
                self.session.add(alert)
        
        if alerts:
            self.session.commit()
        
        return alerts
    
    def cleanup_old_alerts(self, user: User, days: int = 7):
        """
        Mark alerts older than X days as read to keep the list clean.
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        old_alerts = [a for a in user.alerts if a.date_created < cutoff and not a.is_read]
        
        for alert in old_alerts:
            alert.is_read = True
            self.session.add(alert)
        
        if old_alerts:
            self.session.commit()
