import yfinance as yf
import concurrent.futures
from datetime import datetime, timedelta
from typing import List, Dict
from sqlmodel import Session, select, delete
from services.finance_service import FinanceService
from services.analysis_service import AnalysisService
from models.tables import Sector, DiscoveryOpportunity
from config import SECTOR_2_ETF_MAP

class ScannerService:
    # Class-level flag to track scanning status across instances (resets on app restart)
    _is_scanning = False

    def __init__(self, session: Session):
        self.session = session
        self.finance_service = FinanceService()
        self.analysis_service = AnalysisService(session)

    @classmethod
    def get_status(cls):
        return {"is_scanning": cls._is_scanning}

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
                        
                        # Fetch detected setups
                        inst_setups = self._passes_institutional_filters(ticker)
                        rs_data = self.finance_service.get_relative_strength(ticker)
                        
                        rec = self.analysis_service.analyze_ticker(
                            ticker, 
                            user_id, 
                            is_vcp=inst_setups["vcp"],
                            is_blue_sky=inst_setups["blue_sky"],
                            has_super_trend=inst_setups["super_trend"],
                            rs_rating=rs_data.get("rs_score")
                        )
                        
                        results.append(rec)
                    else:
                        print(f"Scanner: {ticker} skipped (Technical Filter).")
        return results

    def discover_opportunities(self, user_id: int) -> List[DiscoveryOpportunity]:
        """
        Discovery Engine (Optimized):
        Scans all sectors in parallel for high-conviction setups.
        Wipes previous discovery results and replaces them with fresh ones.
        """
        if ScannerService._is_scanning:
            print("🔭 Discovery: A scan is already in progress. Skipping.")
            return []

        try:
            ScannerService._is_scanning = True
            
            # 1. Wipe previous results for this user
            print(f"🔭 Discovery: Wiping previous discovery results for user {user_id}...")
            self.session.exec(delete(DiscoveryOpportunity).where(DiscoveryOpportunity.user_id == user_id))
            self.session.commit()

            all_tickers = []
            for etf in SECTOR_2_ETF_MAP.values():
                holdings = self.finance_service.get_etf_holdings(etf)
                all_tickers.extend(holdings)
            
            # Deduplicate
            unique_tickers = list(set(all_tickers))
            print(f"🔭 Discovery: Scanning {len(unique_tickers)} unique symbols in parallel...")

            opportunities = []
            
            def process_ticker(ticker):
                try:
                    setups = self._passes_institutional_filters(ticker)
                    if setups["vcp"] or setups["blue_sky"]:
                        # Fetch RS data
                        rs_data = self.finance_service.get_relative_strength(ticker)

                        # We use the analysis service to get the reasoning, 
                        # but we'll save it as a DiscoveryOpportunity
                        rec = self.analysis_service.analyze_ticker(
                            ticker, 
                            user_id,
                            is_vcp=setups["vcp"],
                            is_blue_sky=setups["blue_sky"],
                            has_super_trend=setups["super_trend"],
                            rs_rating=rs_data.get("rs_score")
                        )
                        
                        # Convert to DiscoveryOpportunity for storage
                        opp = DiscoveryOpportunity(
                            ticker=ticker,
                            action=rec.action,
                            reasoning=rec.reasoning,
                            is_vcp=setups["vcp"],
                            is_blue_sky=setups["blue_sky"],
                            has_super_trend=setups["super_trend"],
                            rs_rating=rs_data.get("rs_score"),
                            user_id=user_id
                        )
                        return opp
                except Exception as e:
                    print(f"Error processing {ticker} during discovery: {e}")
                return None

            # Execute in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                future_to_ticker = {executor.submit(process_ticker, t): t for t in unique_tickers}
                for future in concurrent.futures.as_completed(future_to_ticker):
                    result = future.result()
                    if result:
                        self.session.add(result)
                        opportunities.append(result)
            
            self.session.commit()
            return opportunities
            
        except Exception as e:
            print(f"❌ Discovery Error: {e}")
            return []
        finally:
            ScannerService._is_scanning = False

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

    def _passes_institutional_filters(self, ticker: str) -> Dict[str, bool]:
        """
        Weekly Trader Discovery Filters (Optimized):
        Uses a single weekly history fetch for all calculations.
        """
        weekly_techs = self.finance_service.get_weekly_technicals(ticker)
        if not weekly_techs:
            return {"vcp": False, "blue_sky": False, "super_trend": False}

        price = weekly_techs.get("current_price", 0)
        ma10w = weekly_techs.get("ma_10w", 0)
        ma30w = weekly_techs.get("ma_30w", 0)
        ma30w_up = weekly_techs.get("ma_30w_slope") == "UP"
        
        super_trend = price > ma10w > ma30w and ma30w_up

        # Blue Sky Check using the high_52w from the same weekly fetch
        high_52w = weekly_techs.get("high_52w", 0)
        blue_sky = (price >= high_52w * 0.97) if high_52w > 0 else False

        return {
            "vcp": weekly_techs.get("is_vcp", False),
            "blue_sky": blue_sky,
            "super_trend": super_trend
        }
