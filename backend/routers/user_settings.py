from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from database import get_session
from models.tables import User
from auth.security import get_current_user
from services.news_service import NewsService
from pydantic import BaseModel

router = APIRouter(prefix="/users", tags=["users"])

class SettingsUpdate(BaseModel):
    active_sectors: List[str]

@router.get("/settings")
def get_settings(current_user: User = Depends(get_current_user)):
    # Convert CSV string back to list
    sectors = current_user.active_sectors.split(",") if current_user.active_sectors else []
    return {"active_sectors": sectors}

@router.put("/settings")
def update_settings(settings: SettingsUpdate, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    # Join list to CSV string
    current_user.active_sectors = ",".join(settings.active_sectors)
    session.add(current_user)
    session.commit()
    return {"status": "updated", "active_sectors": settings.active_sectors}

@router.get("/news")
def get_personalized_news(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    """
    Fetch news based on User's active sectors.
    """
    news_service = NewsService()
    sectors = current_user.active_sectors.split(",") if current_user.active_sectors else ["Technology"]
    
    # Fetch news for each sector (limit to first 3 to avoid slow load)
    aggregated_news = []
    for sector in sectors[:3]: 
        items = news_service.fetch_sector_news(sector)
        # Tag them with the sector for UI
        for item in items:
            item['sector_tag'] = sector
        aggregated_news.extend(items[:2]) # Take top 2 per sector
        
    return aggregated_news
