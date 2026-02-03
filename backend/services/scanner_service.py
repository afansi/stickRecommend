import yfinance as yf
import concurrent.futures
from datetime import datetime, timedelta
from typing import List, Dict
from sqlmodel import Session, select, delete
from services.finance_service import FinanceService
from services.analysis_service import AnalysisService
from services.universe_service import UniverseService
from services.news_service import NewsService
from models.tables import Sector, DiscoveryOpportunity
from config import MAX_YF_WORKERS

class ScannerService:
    # Class-level status to track scanning progress across instances
    _status = {
        "is_scanning": False,
        "phase": "idle",
        "current": 0,
        "total": 0,
        "message": ""
    }

    def __init__(self, session: Session):
        self.session = session
        self.finance_service = FinanceService()
        self.analysis_service = AnalysisService(session)
        self.news_service = NewsService()
        self.universe_service = UniverseService()

    @classmethod
    def get_status(cls):
        return cls._status

    @classmethod
    def set_status(cls, is_scanning: bool, phase: str = "idle", current: int = 0, total: int = 0, message: str = ""):
        cls._status = {
            "is_scanning": is_scanning,
            "phase": phase,
            "current": current,
            "total": total,
            "message": message
        }

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
                print(f"Scanner: Updating global holdings for {sector_name}...")
                # Fetch all relevant regional ETFs for this sector
                etfs = self.finance_service.get_all_sector_etfs(sector_name)
                all_holdings = set()
                
                for etf in etfs:
                    holdings_list = self.finance_service.get_etf_holdings(etf)
                    if holdings_list:
                        all_holdings.update(holdings_list)
                
                if all_holdings:
                    holdings_str = ",".join(list(all_holdings))
                    sector_db.top_holdings = holdings_str
                    sector_db.last_updated = datetime.utcnow()
                    self.session.add(sector_db)
                    self.session.commit()
                    candidates = list(all_holdings)
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
        if self._status["is_scanning"]:
            print("🔭 Discovery: A global scan is already in progress. Skipping.")
            return []

        # We need SessionLocal for thread-safe workers
        from database import SessionLocal

        try:
            self.set_status(True, phase="retrieval", message="Scraping global ticker indices...")
            
            # 1. Global Wipe (Fresh weekly start)
            print("🔭 Discovery: Performing Global Wipe of previous findings...")
            self.session.execute(delete(DiscoveryOpportunity))
            self.session.commit()

            # 2. Get Global Investable Universe
            def liquidity_callback(current, total):
                self.set_status(True, phase="liquidity", current=current, total=total, message=f"Checking liquidity (Chunk {current}/{total})...")

            unique_tickers = self.universe_service.get_investable_universe(progress_callback=liquidity_callback)
            print(f"🔭 Discovery: Screening {len(unique_tickers)} unique symbols globally...")

            # 3. Batch Weekly Technical Screening
            self.set_status(True, phase="screening", message="Batch calculating indicators for screening...")
            batch_weekly_data = self.finance_service.batch_get_weekly_technicals(unique_tickers)
            
            candidates = []
            for ticker in unique_tickers:
                techs = batch_weekly_data.get(ticker)
                if techs:
                    filters = self._passes_institutional_filters_from_data(techs)
                    if filters["vcp"] or filters["blue_sky"]:
                        candidates.append((ticker, techs, filters))
            
            total_candidates = len(candidates)
            self.set_status(True, phase="analysis", current=0, total=total_candidates, message=f"Starting deep analysis for {total_candidates} candidates...")
            print(f"🔭 Discovery: {total_candidates} candidates passed technical screening. Starting deep analysis...")

            opportunities = []
            ticker_to_sector_name = self.universe_service.get_sector_map([c[0] for c in candidates])
            
            # --- OPTIMIZATION: Pre-fetch Sector Context (Region-Aware) ---
            print(f"🔭 Discovery: Pre-fetching regional performance and news for unique sector-region pairs...")
            
            # Map ticker to (sector, region) for later lookup
            ticker_to_context_key = {}
            unique_contexts = set() # Set of (sector_name, region)
            
            for ticker in ticker_to_sector_name:
                s_name = ticker_to_sector_name[ticker]
                if not s_name or s_name == "Unknown": continue
                
                region = self.finance_service._get_region_for_ticker(ticker)
                unique_contexts.add((s_name, region))
                ticker_to_context_key[ticker] = (s_name, region)
                
            sector_region_context = {}
            for s_name, region in unique_contexts:
                # Use centralized lookup to get the correct regional ETF
                etf = self.finance_service.get_etf_for_sector(s_name, region=region)
                perf = self.finance_service.get_sector_performance(etf)
                news = self.news_service.fetch_news(etf)
                
                sector_region_context[(s_name, region)] = {
                    "info": {"name": s_name, "etf": etf},
                    "perf": perf,
                    "news": news
                }
            
            # --- OPTIMIZATION: Batch Pre-fetch All Ticker Data ---
            # This eliminates the 120s queue congestion by populating the cache upfront
            candidate_tickers = [c[0] for c in candidates]
            print(f"📦 Discovery: Batch pre-fetching metadata and technicals for {len(candidate_tickers)} candidates...")
            
            # 1. Pre-fetch metadata (populates cache)
            self.finance_service.batch_get_metadata(candidate_tickers)
            
            # 2. Pre-fetch technicals (already batched, but call it to ensure cache population)
            self.finance_service.batch_get_technicals(candidate_tickers)
            
            print(f"✅ Discovery: Batch pre-fetch complete. Starting parallel analysis with warm cache...")
            
            processed_count = 0

            def process_candidate(candidate_info):
                ticker, weekly_techs, filters = candidate_info
                # CREATE A FRESH SESSION FOR THIS WORKER THREAD
                with SessionLocal() as worker_session:
                    try:
                        # Re-initialize services with the worker session
                        from services.analysis_service import AnalysisService
                        from services.finance_service import FinanceService
                        
                        f_service = FinanceService()
                        a_service = AnalysisService(worker_session)
                        
                        # 1. Fetch RS data
                        rs_data = f_service.get_relative_strength(ticker)

                        # 2. Get pre-fetched regional sector context
                        ctx_key = ticker_to_context_key.get(ticker)
                        s_ctx = sector_region_context.get(ctx_key, {})

                        # 3. Trigger Full Analysis
                        rec = a_service.analyze_ticker(
                            ticker, 
                            user_id=1, 
                            is_vcp=filters["vcp"],
                            is_blue_sky=filters["blue_sky"],
                            has_super_trend=filters["super_trend"],
                            rs_rating=rs_data.get("rs_score"),
                            is_decoupled=rs_data.get("is_decoupled", False),
                            prefetched_sector_info=s_ctx.get("info"),
                            prefetched_sector_perf=s_ctx.get("perf"),
                            prefetched_sector_news=s_ctx.get("news")
                        )
                        
                        # 3. Calculate Position Sizing Hints (Now Probabilistic!)
                        price = weekly_techs.get("current_price", 0)
                        
                        # Use probabilistic targets derived from 52-week statistical analysis
                        # Fallback to MA10W or 8% stop if probabilistic data unavailable
                        prob_stop = weekly_techs.get("prob_stop_price")
                        prob_target = weekly_techs.get("prob_target_price")
                        
                        if prob_stop and prob_stop > 0 and prob_stop < price:
                            suggested_stop = float(prob_stop)
                        else:
                            # Fallback: Use MA10W or 8% stop
                            ma10w = weekly_techs.get("ma_10w", 0)
                            suggested_stop = float(ma10w if (ma10w > 0 and ma10w < price) else round(price * 0.92, 2))
                        
                        # Ensure stop isn't too aggressive (min 10% from price)
                        if suggested_stop < price * 0.85:
                            suggested_stop = float(round(price * 0.90, 2))
                        
                        if prob_target and prob_target > price:
                            suggested_target = float(prob_target)
                        else:
                            # Fallback: 3:1 R:R ratio
                            risk = price - suggested_stop
                            suggested_target = float(round(price + (risk * 3), 2))

                        sector = ticker_to_sector_name.get(ticker, "Unknown")

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
                        
                        # SAVE INDIVIDUALLY FOR REAL-TIME UI UPDATES
                        worker_session.add(opp)
                        worker_session.commit()
                        worker_session.refresh(opp)
                        worker_session.expunge(opp)
                        return opp
                    except Exception as e:
                        print(f"Error processing {ticker} during discovery: {e}")
                        worker_session.rollback()
                        return None

            # Execute deep analysis in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_YF_WORKERS) as executor:
                future_to_ticker = {executor.submit(process_candidate, c): c[0] for c in candidates}
                for future in concurrent.futures.as_completed(future_to_ticker):
                    processed_count += 1
                    result = future.result()
                    ticker = future_to_ticker[future]
                    
                    progress_pct = (processed_count / total_candidates) * 100
                    self.set_status(True, phase="analysis", current=processed_count, total=total_candidates, message=f"Analyzed {ticker} ({processed_count}/{total_candidates})")
                    print(f"📊 Progress: {processed_count}/{total_candidates} ({progress_pct:.1f}%) | Last: {ticker} {'✅' if result else '❌'}")
                    
                    if result:
                        opportunities.append(result)
            
            self.set_status(False, phase="idle", message=f"Discovery complete. Found {len(opportunities)} opportunities.")
            print(f"✅ Discovery: Global scan complete. Found {len(opportunities)} opportunities.")
            return opportunities
            
        except Exception as e:
            print(f"❌ Discovery Error: {e}")
            self.set_status(False, phase="error", message=str(e))
            return []
        finally:
            self._status["is_scanning"] = False

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
