from typing import List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from database import get_session
from models.tables import User
from auth.security import get_current_user
from services.news_service import NewsService
from config import SECTOR_2_ETF_MAP
from pydantic import BaseModel

router = APIRouter(prefix="/users", tags=["users"])

class SettingsUpdate(BaseModel):
    active_sectors: List[str]
    total_equity: Optional[float] = None
    risk_pct: Optional[float] = None

@router.get("/settings")
def get_settings(current_user: User = Depends(get_current_user)):
    # Convert CSV string back to list
    sectors = current_user.active_sectors.split(",") if current_user.active_sectors else []
    return {
        "active_sectors": sectors,
        "total_equity": current_user.total_equity,
        "risk_pct": current_user.risk_pct
    }

@router.put("/settings")
def update_settings(settings: SettingsUpdate, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    # Join list to CSV string
    current_user.active_sectors = ",".join(settings.active_sectors)
    
    if settings.total_equity is not None:
        current_user.total_equity = settings.total_equity
    if settings.risk_pct is not None:
        current_user.risk_pct = settings.risk_pct
        
    session.add(current_user)
    session.commit()
    return {
        "status": "updated", 
        "active_sectors": settings.active_sectors,
        "total_equity": current_user.total_equity,
        "risk_pct": current_user.risk_pct
    }

@router.get("/news")
def get_personalized_news(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    """
    Fetch news based on User's active sectors. Falls back to market news if none found.
    Injects sector top holdings for discovery.
    """
    news_service = NewsService()
    from services.finance_service import FinanceService
    finance_service = FinanceService()
    
    sectors = current_user.active_sectors.split(",") if current_user.active_sectors else ["Technology"]
    
    aggregated_news = []
    holdings_cache = {} # ETF -> Holdings
    
    # 1. Try fetching news from user's active sectors
    for sector in sectors: 
        sector_name = sector.strip()
        if not sector_name:
            continue
            
        etf = SECTOR_2_ETF_MAP.get(sector_name)
        if etf and etf not in holdings_cache:
            holdings_cache[etf] = finance_service.get_etf_holdings(etf)
            
        items = news_service.fetch_sector_news(sector_name)
        for item in items:
            item['sector_tag'] = sector_name
            item['sector_holdings'] = holdings_cache.get(etf, [])
        
        # Take top 3 per sector
        aggregated_news.extend(items[:3])
        
        # If we have enough news, stop to keep it fast
        if len(aggregated_news) >= 20:
            break
        
    # 2. Fallback: If no news found for sectors, get general market news
    if not aggregated_news:
        market_news = news_service.get_market_news()
        spy_holdings = finance_service.get_etf_holdings("SPY")
        for item in market_news:
            item['sector_tag'] = "Market"
            item['sector_holdings'] = spy_holdings
        aggregated_news = market_news[:min(20, len(market_news))]
        
    return aggregated_news
