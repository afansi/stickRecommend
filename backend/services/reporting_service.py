import json
from datetime import datetime
from typing import List, Dict
from sqlmodel import Session, select
from models.tables import TradePlan, PerformanceReview, User
from services.finance_service import FinanceService
from services.llm_engine import LLMFactory
from config import settings

class ReportingService:
    def __init__(self, session: Session):
        self.session = session
        self.finance_service = FinanceService()
        self.llm = LLMFactory.get_client(
            use_cloud=settings.USE_CLOUD,
            api_key=settings.LLM_API_KEY,
            provider=settings.LLM_PROVIDER,
            model=settings.LLM_MODEL
        )

    def generate_weekend_review(self, user_id: int) -> PerformanceReview:
        """
        Generates a comprehensive weekend performance report.
        1. Compares active plans with closing prices.
        2. Aggregates total risk exposure.
        3. Synthesizes an institutional verdict via LLM.
        """
        # 1. Fetch Active Plans
        plans = self.session.exec(
            select(TradePlan).where(TradePlan.user_id == user_id)
        ).all()
        
        if not plans:
            return None

        # 2. Performance Analysis
        positions_summary = []
        total_exposure = 0.0
        total_risk_amount = 0.0
        
        for plan in plans:
            techs = self.finance_service.get_technicals(plan.ticker)
            close_price = techs.get("current_price", plan.entry_price)
            pnl_pct = ((close_price - plan.entry_price) / plan.entry_price) * 100
            
            total_exposure += (close_price * (plan.num_shares or 0))
            total_risk_amount += (plan.risk_amount or 0.0)

            positions_summary.append({
                "ticker": plan.ticker,
                "entry": plan.entry_price,
                "close": close_price,
                "pnl_pct": round(pnl_pct, 2),
                "stop": plan.stop_loss,
                "target": plan.target_price,
                "status": "Winning" if pnl_pct > 0 else "Losing"
            })

        user = self.session.get(User, user_id)
        equity = user.total_equity if user else 50000.0
        risk_pct_agg = (total_risk_amount / equity) * 100 if equity > 0 else 0.0

        # 3. LLM Synthesis for Verdict
        prompt = f"""
        Act as an Institutional Risk Manager. Review the following active trading portfolio performance for the week:
        
        Positions: {json.dumps(positions_summary)}
        Total Exposure: ${total_exposure:,.2f}
        Cumulative Risk: {risk_pct_agg:.2f}% of Total Equity (${equity:,.2f})
        
        Provide a concise 3-part report:
        1. PERFORMANCE OF ACTIVE POSITIONS (Technical analysis of weekly candles/closes).
           - For EACH position, provide a "Tool Action" (e.g., "EXIT", "HOLD", "ADJUST STOP", "PSYCHOLOGICAL LOCK").
           - Explain the rationale clearly (e.g., "Closed below Support", "Support held, maintain patience").
        2. WEEKEND RISK MANAGEMENT (Should we hedge? Is total exposure acceptable?).
        3. ARCHIVING & LEARNING (One lesson or adjustment for next week).
        
        Format as clear Markdown with headers.
        """
        
        verdict_text = self.llm.analyze_text(text="", prompt=prompt)

        # 4. Save Review
        review = PerformanceReview(
            user_id=user_id,
            positions_data=json.dumps(positions_summary),
            total_exposure=total_exposure,
            cumulative_risk_pct=risk_pct_agg,
            risk_verdict="Acceptable" if risk_pct_agg < 3.0 else "Caution",
            global_market_analysis=verdict_text,
            date_generated=datetime.utcnow()
        )
        
        self.session.add(review)
        self.session.commit()
        self.session.refresh(review)
        return review

    def get_latest_review(self, user_id: int) -> PerformanceReview:
        return self.session.exec(
            select(PerformanceReview)
            .where(PerformanceReview.user_id == user_id)
            .order_by(PerformanceReview.date_generated.desc())
        ).first()
