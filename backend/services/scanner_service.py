from datetime import datetime, timedelta
from typing import List, Dict
from sqlmodel import Session, select
from services.finance_service import FinanceService
from services.analysis_service import AnalysisService
from models.tables import Sector
from config import SECTOR_2_ETF_MAP

class ScannerService:
    def __init__(self, session: Session):
        self.session = session
        self.finance_service = FinanceService()
        self.analysis_service = AnalysisService(session)

    def scan_active_sectors(self, active_sectors: List[str], user_id: int) -> List[Dict]:
        """
        Scans top stocks in active sectors for a specific user.
        Updates sector holdings if older than 30 days.
        """
        results = []
        for sector_name in active_sectors:
            # 1. Get or Create Sector in DB
            sector_db = self.session.exec(select(Sector).where(Sector.name == sector_name)).first()
            if not sector_db:
                sector_db = Sector(name=sector_name, keywords=sector_name)
                self.session.add(sector_db)
                self.session.commit()
                self.session.refresh(sector_db)

            # 2. Check Freshness (30 Days)
            needs_update = False
            if not sector_db.top_holdings or not sector_db.last_updated:
                needs_update = True
            elif datetime.utcnow() - sector_db.last_updated > timedelta(days=30):
                needs_update = True

            candidates = []
            if needs_update:
                print(f"Scanner: Updating holdings for {sector_name}...")
                etf = SECTOR_2_ETF_MAP.get(sector_name)
                if etf:
                    # Fetch from Finance Service (Live or Cache)
                    holdings_list = self.finance_service.get_etf_holdings(etf)
                    if holdings_list:
                        sector_db.top_holdings = ",".join(holdings_list)
                        sector_db.last_updated = datetime.utcnow()
                        self.session.add(sector_db)
                        self.session.commit()
                        candidates = holdings_list
            else:
                # Use cached
                candidates = sector_db.top_holdings.split(",") if sector_db.top_holdings else []

            # 3. Batch fetch technicals for all candidates (MUCH more efficient)
            if candidates:
                print(f"Scanner: Batch fetching technicals for {len(candidates)} candidates...")
                batch_technicals = self.finance_service.batch_get_technicals(candidates)
                
                # 4. Filter and analyze
                for ticker in candidates:
                    tech_data = batch_technicals.get(ticker)
                    if tech_data and self._passes_technical_filter_from_data(tech_data):
                        # Trigger full analysis with user context
                        print(f"Scanner: {ticker} passed filter. Analyzing for user {user_id}...")
                        rec = self.analysis_service.analyze_ticker(ticker, user_id)
                        results.append(rec)
                    else:
                        print(f"Scanner: {ticker} skipped (Technical Filter).")
        return results

    def _passes_technical_filter_from_data(self, tech_data: dict) -> bool:
        """
        Cheap Gatekeeper using pre-fetched technical data.
        """
        if not tech_data:
            return False
            
        rsi = tech_data.get("rsi_14")
        trend = tech_data.get("trend")
        
        # Rule 1: Oversold (Dip Opportunity)
        if rsi and rsi < 35:
            return True
            
        # Rule 2: Strong Momentum
        if rsi and rsi > 65:
            return True
            
        # Rule 3: Clear Uptrend
        if trend == "UP":
            return True
            
        return False

    def _passes_technical_filter(self, ticker: str) -> bool:
        """
        Cheap Gatekeeper: fast check of RSI/Trend.
        Pass if:
        - RSI < 30 (Oversold/Dip Buy) OR
        - RSI > 70 (Momentum Breakout) OR
        - Trend = UP (Price > MA50)
        """
        techs = self.finance_service.get_technicals(ticker)
        if not techs:
            return False # No data, skip
            
        rsi = techs.get("rsi_14")
        trend = techs.get("trend")
        
        # Rule 1: Oversold (Dip Opportunity)
        if rsi and rsi < 35:
            return True
            
        # Rule 2: Strong Momentum
        if rsi and rsi > 65:
            return True
            
        # Rule 3: Clear Uptrend
        if trend == "UP":
            return True
            
        # Otherwise, stock is chopping/neutral -> Skip expensive LLM analysis
        return False
