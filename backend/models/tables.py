from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

# --- Authentication ---
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str
    is_active: bool = Field(default=True)
    active_sectors: str = Field(default="Technology,Financials,Healthcare") # Comma-separated preferences
    
    portfolio_items: List["PortfolioItem"] = Relationship(back_populates="user")
    alerts: List["Alert"] = Relationship(back_populates="user")
    recommendations: List["Recommendation"] = Relationship(back_populates="user")

# --- Core Data ---
class Sector(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True) # e.g., "Technology", "Healthcare"
    keywords: str # Comma-separated, e.g., "semiconductor, software, AI"
    is_active: bool = Field(default=True)
    top_holdings: Optional[str] = Field(default=None) # JSON/CSV of tickers
    last_updated: Optional[datetime] = Field(default=None)

class PortfolioItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ticker: str = Field(index=True)
    quantity: float
    avg_cost: float
    date_added: datetime = Field(default_factory=datetime.utcnow)
    
    user_id: int = Field(foreign_key="user.id")
    user: Optional[User] = Relationship(back_populates="portfolio_items")

class NewsArticle(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ticker: Optional[str] = Field(index=True, default=None) # Can be None if general market news
    title: str
    url: str = Field(unique=True)
    source: str
    published_date: datetime
    content_summary: Optional[str] = None
    sentiment_score: float = Field(default=0.0) # -1.0 to 1.0
    impact_analysis: Optional[str] = None # AI reasoning
    
    sector_id: Optional[int] = Field(default=None, foreign_key="sector.id")

class Recommendation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ticker: str = Field(index=True)
    action: str # "BUY", "SELL", "HOLD"
    confidence_score: float # 0-10
    reasoning: str
    date_generated: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True, index=True)
    source_news_id: Optional[int] = Field(default=None, foreign_key="newsarticle.id")
    
    user_id: int = Field(foreign_key="user.id", index=True)
    user: Optional[User] = Relationship(back_populates="recommendations")

class Alert(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ticker: str = Field(index=True)
    message: str
    severity: str # "HIGH", "MEDIUM", "LOW"
    date_created: datetime = Field(default_factory=datetime.utcnow)
    is_read: bool = Field(default=False, index=True)
    
    user_id: int = Field(foreign_key="user.id")
    user: Optional[User] = Relationship(back_populates="alerts")
