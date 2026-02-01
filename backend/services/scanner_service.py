import yfinance as yf
import concurrent.futures
from datetime import datetime, timedelta
from typing import List, Dict
from sqlmodel import Session, select, delete
from services.finance_service import FinanceService
from services.analysis_service import AnalysisService
from services.universe_service import UniverseService
from models.tables import Sector, DiscoveryOpportunity
from config import SECTOR_2_ETF_MAP

class ScannerService:
    # Class-level flag to track scanning status across instances (resets on app restart)
    _is_scanning = False

    def __init__(self, session: Session):
        self.session = session
        self.finance_service = FinanceService()
        self.analysis_service = AnalysisService(session)
        self.universe_service = UniverseService()

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

    def discover_opportunities(self) -> List[DiscoveryOpportunity]:
        """
        Discovery Engine (Global):
        Scans all sectors in parallel for institutional setups.
        Shared across all users. Results are filtered by user sectors in the API.
        """
        if ScannerService._is_scanning:
            print("🔭 Discovery: A global scan is already in progress. Skipping.")
            return []

        try:
            ScannerService._is_scanning = True
            
            # 1. Global Wipe (Fresh weekly start)
            print("🔭 Discovery: Performing Global Wipe of previous findings...")
            self.session.execute(delete(DiscoveryOpportunity))
            self.session.commit()

            # 2. Get Global Investable Universe
            unique_tickers = self.universe_service.get_investable_universe()
            print(f"🔭 Discovery: Screening {len(unique_tickers)} unique symbols globally...")

            # 3. Batch Weekly Technical Screening (The Speedup)
            # This fetches indicators in bulk and avoids hundreds of individual requests
            print(f"🔭 Discovery: Batch calculating indicators for screening...")
            batch_weekly_data = self.finance_service.batch_get_weekly_technicals(unique_tickers)
            
            # Prune the universe to only those passing the initial technical setup
            candidates = []
            for ticker in unique_tickers:
                techs = batch_weekly_data.get(ticker)
                if techs:
                    filters = self._passes_institutional_filters_from_data(techs)
                    if filters["vcp"] or filters["blue_sky"]:
                        candidates.append((ticker, techs, filters))
            
            print(f"🔭 Discovery: {len(candidates)} candidates passed technical screening. Starting deep analysis...")

            opportunities = []
            
            # Helper to map ticker to sector
            ticker_to_sector = self.universe_service.get_sector_map([c[0] for c in candidates])
            
            def process_candidate(candidate_info):
                ticker, weekly_techs, filters = candidate_info
                try:
                    # 1. Fetch RS data
                    rs_data = self.finance_service.get_relative_strength(ticker)

                    # 2. Trigger Full Analysis (AI reasoning/News/Financials)
                    # We use System User (ID 1)
                    rec = self.analysis_service.analyze_ticker(
                        ticker, 
                        user_id=1, 
                        is_vcp=filters["vcp"],
                        is_blue_sky=filters["blue_sky"],
                        has_super_trend=filters["super_trend"],
                        rs_rating=rs_data.get("rs_score"),
                        is_decoupled=rs_data.get("is_decoupled", False)
                    )
                    
                    # 3. Calculate "Hints" (Suggested Levels)
                    price = weekly_techs.get("current_price", 0)
                    ma10w = weekly_techs.get("ma_10w", 0)
                    
                    suggested_stop = float(ma10w if (ma10w > 0 and ma10w < price) else round(price * 0.92, 2))
                    if suggested_stop < price * 0.85:
                        suggested_stop = float(round(price * 0.90, 2))
                        
                    risk = price - suggested_stop
                    suggested_target = float(round(price + (risk * 3), 2))

                    sector = ticker_to_sector.get(ticker, "Unknown")

                    opp = DiscoveryOpportunity(
                        ticker=ticker,
                        sector=sector,
                        action=rec.action,
                        reasoning=rec.reasoning,
                        suggested_entry=float(price),
                        suggested_stop=float(suggested_stop),
                        suggested_target=float(suggested_target),
                        is_vcp=filters["vcp"],
                        is_blue_sky=filters["blue_sky"],
                        has_super_trend=filters["super_trend"],
                        rs_rating=float(rs_data.get("rs_score", 0)),
                        is_decoupled=rs_data.get("is_decoupled", False)
                    )
                    return opp
                except Exception as e:
                    print(f"Error processing {ticker} during discovery: {e}")
                return None

            # Execute deep analysis in parallel (I/O and LLM bound)
            # Increased workers since many tickers were pruned by screening
            with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
                future_to_ticker = {executor.submit(process_candidate, c): c[0] for c in candidates}
                for future in concurrent.futures.as_completed(future_to_ticker):
                    result = future.result()
                    if result:
                        self.session.add(result)
                        opportunities.append(result)
            
            self.session.commit()
            print(f"✅ Discovery: Global scan complete. Found {len(opportunities)} opportunities.")
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

    def _passes_institutional_filters_from_data(self, weekly_techs: dict) -> Dict[str, bool]:
        """
        Weekly Trader Discovery Filters (Optimized):
        Uses pre-fetched weekly history data.
        """
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

    def _passes_institutional_filters(self, ticker: str) -> Dict[str, bool]:
        """
        Weekly Trader Discovery Filters (Standalone):
        Fetches data and delegates to the data-based filter.
        """
        weekly_techs = self.finance_service.get_weekly_technicals(ticker)
        return self._passes_institutional_filters_from_data(weekly_techs)
