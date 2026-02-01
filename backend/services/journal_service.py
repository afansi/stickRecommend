from datetime import datetime
from typing import List, Dict, Optional
from sqlmodel import Session, select, and_
from models.tables import TradePlan, JournalEntry, User

class JournalService:
    def __init__(self, session: Session):
        self.session = session

    def create_plan(self, user_id: int, ticker: str, entry: float, stop: float, target: float, setup: str, conviction: int, 
                    override_equity: Optional[float] = None, override_risk_pct: Optional[float] = None) -> TradePlan:
        """
        Create a new trade plan. 
        Automatically calculates position size using R-Manager logic.
        Supports optional overrides for equity and risk %.
        """
        today = datetime.utcnow()
        is_weekend = today.weekday() >= 5
        
        # 1. Fetch User Risk Settings
        user = self.session.get(User, user_id)
        
        # Use overrides if provided, else DB values, else defaults
        equity = override_equity if override_equity is not None else (user.total_equity if user else 50000.0)
        risk_pct = override_risk_pct if override_risk_pct is not None else (user.risk_pct if user else 1.0)
        
        # 2. Calculate Position Size
        from services.risk_service import RiskService
        risk_service = RiskService()
        risk_results = risk_service.calculate_position_size(equity, risk_pct, entry, stop)
        
        # 3. Running Monte Carlo Simulation
        print(f"🎲 Monte Carlo: Running simulation for {ticker}...")
        mc_results = risk_service.run_monte_carlo(ticker, entry, stop, target)
        prob_success = mc_results.get("prob_target_hit") if "error" not in mc_results else None
        
        plan = TradePlan(
            user_id=user_id,
            ticker=ticker.upper(),
            entry_price=entry,
            stop_loss=stop,
            target_price=target,
            setup_type=setup,
            conviction_score=conviction,
            num_shares=risk_results.get("num_shares", 0),
            risk_amount=risk_results.get("risk_amount", 0.0),
            position_size_pct=risk_results.get("position_size_pct", 0.0),
            prob_success=prob_success,
            is_locked=is_weekend,
            date_planned=today
        )
        self.session.add(plan)
        self.session.commit()
        self.session.refresh(plan)
        return plan

    def log_execution(self, user_id: int, ticker: str, action: str, price: float, emotion: str, bias_note: Optional[str] = None) -> JournalEntry:
        """
        Log a trade execution with emotional state and bias check.
        If trying to close a locked plan mid-week, a warning/intervention should be logged.
        """
        # Check for existing locked plan
        plan = self.session.exec(
            select(TradePlan).where(
                TradePlan.user_id == user_id,
                TradePlan.ticker == ticker.upper(),
                TradePlan.is_locked == True
            )
        ).first()

        intervention_note = ""
        if plan and action == "EXIT":
            today = datetime.utcnow()
            days_held = (today - plan.date_planned).days
            if today.weekday() < 5 and days_held < (plan.expected_duration_weeks * 7):
                intervention_note = f"[ANTI-BIAS WARNING]: Impulse exit attempted on a {today.strftime('%A')}. " \
                                   f"Plan was for {plan.expected_duration_weeks} weeks ({plan.expected_duration_weeks * 7} days). " \
                                   f"Only {days_held} days have passed."

        full_note = f"{intervention_note} {bias_note or ''}".strip()

        entry = JournalEntry(
            user_id=user_id,
            ticker=ticker.upper(),
            action=action,
            price=price,
            emotional_state=emotion,
            bias_check=full_note
        )
        self.session.add(entry)
        self.session.commit()
        self.session.refresh(entry)
        return entry

    def get_user_plans(self, user_id: int) -> List[TradePlan]:
        return self.session.exec(select(TradePlan).where(TradePlan.user_id == user_id)).all()

    def get_user_journal(self, user_id: int) -> List[JournalEntry]:
        return self.session.exec(select(JournalEntry).where(JournalEntry.user_id == user_id).order_by(JournalEntry.date_logged.desc())).all()
