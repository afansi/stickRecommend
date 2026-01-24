from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from database import get_session
from models.tables import User, PortfolioItem
from auth.security import get_current_user
from services.allocation_service import AllocationService

router = APIRouter(prefix="/portfolio", tags=["portfolio"])

@router.get("/", response_model=List[PortfolioItem])
def get_portfolio(current_user: User = Depends(get_current_user)):
    return current_user.portfolio_items

@router.post("/", response_model=PortfolioItem)
def add_stock(item: PortfolioItem, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    item.user_id = current_user.id
    session.add(item)
    session.commit()
    session.refresh(item)
    return item

@router.post("/inject_funds")
def calculate_injection(amount: float, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    alloc_service = AllocationService(session)
    plan = alloc_service.calculate_injection(current_user.id, amount)
    return plan

@router.get("/stats")
def get_portfolio_stats(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    alloc_service = AllocationService(session)
    return alloc_service.get_portfolio_stats(current_user.id)
