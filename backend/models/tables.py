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
    total_equity: float = Field(default=50000.0) # For R-Manager calculations
    risk_pct: float = Field(default=1.0) # Default risk per trade (e.g., 1.0%)
    
    portfolio_items: List["PortfolioItem"] = Relationship(back_populates="user")
    alerts: List["Alert"] = Relationship(back_populates="user")
    recommendations: List["Recommendation"] = Relationship(back_populates="user")
    trade_plans: List["TradePlan"] = Relationship(back_populates="user")
    journal_entries: List["JournalEntry"] = Relationship(back_populates="user")

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
    company_name: Optional[str] = None
    action: str # "BUY", "SELL", "HOLD"
    confidence_score: float # 0-10
    reasoning: str
    
    # Suggested Price Levels ("Hints")
    suggested_entry: Optional[float] = Field(default=None)
    suggested_stop: Optional[float] = Field(default=None)
    suggested_target: Optional[float] = Field(default=None)
    
    date_generated: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True, index=True)
    source_news_id: Optional[int] = Field(default=None, foreign_key="newsarticle.id")
    source_news_url: Optional[str] = None
    verified_sources: Optional[str] = Field(default=None) # JSON-encoded list of supporting news items
    
    user_id: int = Field(foreign_key="user.id", index=True)
    user: Optional[User] = Relationship(back_populates="recommendations")
    
    # --- Institutional Setup Flags ---
    is_vcp: bool = Field(default=False)
    is_blue_sky: bool = Field(default=False)
    has_super_trend: bool = Field(default=False)
    rs_rating: Optional[float] = Field(default=None)
    
class Alert(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ticker: str = Field(index=True)
    message: str
    severity: str # "HIGH", "MEDIUM", "LOW"
    date_created: datetime = Field(default_factory=datetime.utcnow)
    is_read: bool = Field(default=False, index=True)
    
    user_id: int = Field(foreign_key="user.id")
    user: Optional[User] = Relationship(back_populates="alerts")

# --- Phase 4: Behavioral Psychology ---

class TradePlan(SQLModel, table=True):
    """
    Trade plans finalized during the weekend.
    Decision locking prevents mid-week editing without override.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    ticker: str = Field(index=True)
    entry_price: float
    stop_loss: float
    target_price: float
    expected_duration_weeks: int = Field(default=4)
    setup_type: str # e.g., "VCP", "Blue Sky", "Relative Strength"
    conviction_score: int # 1-10
    
    # R-Manager Results (calculated at time of planning)
    num_shares: Optional[int] = Field(default=None)
    risk_amount: Optional[float] = Field(default=None)
    position_size_pct: Optional[float] = Field(default=None)
    prob_success: Optional[float] = Field(default=None) # From Monte Carlo
    
    # Decisions are considered "Locked" if made on Saturday/Sunday
    is_locked: bool = Field(default=True) 
    date_planned: datetime = Field(default_factory=datetime.utcnow)
    
    user_id: int = Field(foreign_key="user.id", index=True)
    user: Optional[User] = Relationship(back_populates="trade_plans")

class JournalEntry(SQLModel, table=True):
    """
    Execution journal for tracking emotional state and anti-bias metrics.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    ticker: str = Field(index=True)
    action: str # "ENTRY", "EXIT", "ADJUSTMENT"
    price: float
    
    # Psychological Metadata
    emotional_state: str # e.g., "Calm", "Anxious", "Greedy", "Fearful"
    bias_check: str # AI generated or user note on why they are making the move
    
    date_logged: datetime = Field(default_factory=datetime.utcnow)
    
    user_id: int = Field(foreign_key="user.id", index=True)
    user: Optional[User] = Relationship(back_populates="journal_entries")

class DiscoveryOpportunity(SQLModel, table=True):
    """
    Weekly Trader Discovery Insights (Global Wipe \u0026 Replace).
    Stores the highest-conviction setups from the weekly scan across all sectors.
    Shared by all users and filtered on display by user preferences.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    ticker: str = Field(index=True)
    sector: str = Field(index=True)
    action: str
    reasoning: str
    
    # Suggested Price Levels ("Hints")
    suggested_entry: Optional[float] = Field(default=None)
    suggested_stop: Optional[float] = Field(default=None)
    suggested_target: Optional[float] = Field(default=None)
    is_vcp: bool = Field(default=False)
    is_blue_sky: bool = Field(default=False)
    has_super_trend: bool = Field(default=False)
    rs_rating: Optional[float] = Field(default=None)
    date_generated: datetime = Field(default_factory=datetime.utcnow)
