from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from sqlmodel import Session
from database import get_session
from models.tables import User, TradePlan, JournalEntry
from auth.security import get_current_user
from services.journal_service import JournalService

router = APIRouter(prefix="/journal", tags=["journal"])

@router.post("/plans", response_model=TradePlan)
def create_trade_plan(
    ticker: str, 
    entry: float, 
    stop: float, 
    target: float, 
    setup: str, 
    conviction: int,
    override_equity: Optional[float] = None,
    override_risk_pct: Optional[float] = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new trade plan. Automatically locks if created on a weekend.
    Supports overriding global risk settings.
    """
    service = JournalService(session)
    return service.create_plan(
        current_user.id, ticker, entry, stop, target, setup, conviction, 
        override_equity, override_risk_pct
    )

@router.post("/execute", response_model=JournalEntry)
def log_execution(
    ticker: str, 
    action: str, 
    price: float, 
    emotion: str, 
    bias_note: Optional[str] = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Log an entry/exit with emotional state. Checks for locked plan violations.
    """
    service = JournalService(session)
    return service.log_execution(current_user.id, ticker, action, price, emotion, bias_note)

@router.get("/plans", response_model=List[TradePlan])
def get_plans(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    service = JournalService(session)
    return service.get_user_plans(current_user.id)

@router.get("/entries", response_model=List[JournalEntry])
def get_journal(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    service = JournalService(session)
    return service.get_user_journal(current_user.id)
