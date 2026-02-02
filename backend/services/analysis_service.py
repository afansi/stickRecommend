import concurrent.futures
from sqlmodel import Session, select, update
from datetime import datetime
from typing import List, Optional, Dict
from services.news_service import NewsService
from services.llm_engine import LLMFactory
from models.tables import Recommendation, NewsArticle
from config import settings
from services.finance_service import FinanceService
import json

class AnalysisService:
    def __init__(self, session: Session):
        self.session = session
        self.news_service = NewsService()
        self.finance_service = FinanceService()
        self.llm = LLMFactory.get_client(
            use_cloud=settings.USE_CLOUD,
            api_key=settings.LLM_API_KEY,
            provider=settings.LLM_PROVIDER,
            model=settings.LLM_MODEL
        )

    def analyze_ticker(self, 
                       ticker: str, 
                       user_id: int, 
                       force_refresh: bool = False, 
                       is_vcp: bool = False, 
                       is_blue_sky: bool = False, 
                       has_super_trend: bool = False, 
                       rs_rating: Optional[float] = None, 
                       is_decoupled: bool = False,
                       prefetched_sector_info: Optional[Dict] = None,
                       prefetched_sector_perf: Optional[str] = None,
                       prefetched_sector_news: Optional[List[Dict]] = None
                       ) -> Recommendation:
        """
        Hybrid Analysis Pipeline (Optimized):
        Concurrent fetching of News, Financials, Technicals, and Sector data.
        Includes a Freshness Check / Force Refresh toggle.
        """
        # 0. Check for existing active recommendation
        existing_rec = self.session.exec(
            select(Recommendation).where(
                Recommendation.ticker == ticker,
                Recommendation.user_id == user_id,
                Recommendation.is_active == True
            ).order_by(Recommendation.date_generated.desc())
        ).first()

        # Logic: 
        # - If force_refresh is FALSE and we have ANY active recommendation, return it.
        # - If force_refresh is TRUE, we skip this and generate a new one.
        if not force_refresh and existing_rec:
            print(f"📦 AnalysisService: Returning existing recommendation for {ticker}")
            return existing_rec

        print(f"🚀 AnalysisService: Starting fresh analysis for {ticker} (Force Refresh: {force_refresh})...")
        start_time = datetime.utcnow()

        # Wave 1: Fetch Ticker-specific data in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            ticker_news_future = executor.submit(self.news_service.fetch_news, ticker)
            financials_future = executor.submit(self.finance_service.get_financials, ticker)
            technicals_future = executor.submit(self.finance_service.get_technicals, ticker)
            earnings_future = executor.submit(self.finance_service.get_next_earnings_date, ticker)
            
            # Use pre-fetched sector info if available
            if prefetched_sector_info:
                sector_info = prefetched_sector_info
                sector_info_future = None
            else:
                sector_info_future = executor.submit(self.finance_service.get_stock_sector, ticker)

            news_items = ticker_news_future.result()
            financials = financials_future.result()
            technicals = technicals_future.result()
            earnings_date = earnings_future.result()
            if sector_info_future:
                sector_info = sector_info_future.result()

        # Wave 2: Fetch Sector-specific data in parallel
        sector_etf = sector_info.get("etf", "SPY")
        sector_name = sector_info.get("name", "Unknown")

        if prefetched_sector_perf is not None and prefetched_sector_news is not None:
            sector_perf = prefetched_sector_perf
            sector_news = prefetched_sector_news
        else:
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                sector_perf_future = executor.submit(self.finance_service.get_sector_performance, sector_etf, ticker)
                sector_news_future = executor.submit(self.news_service.fetch_news, sector_etf)

                sector_perf = sector_perf_future.result()
                sector_news = sector_news_future.result()

        print(f"✅ AnalysisService: Data gathering complete in {(datetime.utcnow() - start_time).total_seconds():.2f}s")
        
        # 2. Build Context (Enhanced with Deep Technicals)
        context = f"--- STOCK DATA FOR {ticker} ---\n"
        context += f"FINANCIALS: {financials}\n"
        if earnings_date:
            context += f"Earnings: {earnings_date}\n"
        
        # Breakdown Technicals for AI clarity
        context += f"TECHNICALS:\n"
        context += f"- RSI(14): {technicals.get('rsi_14')}\n"
        context += f"- Trend: {technicals.get('trend')} (Price vs MA50/MA200)\n"
        context += f"- MACD: {technicals.get('macd')}\n"
        context += f"- Bollinger Bands: {technicals.get('bollinger')}\n"
        
        context += f"SECTOR: {sector_name} ({sector_perf})\n"
        context += f"TICKER NEWS: {[n.get('title') for n in news_items[:3]]}\n"
        context += f"SECTOR NEWS: {[n.get('title') for n in sector_news[:2]]}\n"

        # 3. Hybrid Strategy Prompt (Professional Grade)
        prompt = f"""
        Act as a professional financial analyst. Analyze {ticker} using a Hybrid Strategy:
        
        1. FUNDAMENTALS: Value/Growth/Debt health.
        2. TREND: Is price above MA200/MA50? (BULLISH/BEARISH/NEUTRAL).
        3. MOMENTUM (MACD): Is the MACD Histogram positive? Check for crossovers.
        4. VOLATILITY (BB): Is price near Upper Band (Overextended) or Lower Band (Oversold)?
        5. SENTIMENT/CATALYSTS: News and Earnings impact.
        
        Synthesize into ACTION (BUY/SELL/HOLD), SCORE (0-10), and REASON (max 100 words).
        
        Format:
        ACTION: [Action]
        SCORE: [Score]
        REASON: [Balanced reasoning weighting all factors]
        """
        
        # 4. Call LLM
        response = self.llm.analyze_text(text=context, prompt=prompt)
        
        # 5. Robust Parse Response (Regex)
        import re
        action = "HOLD"
        score = 5.0
        reason = "Analysis synthesis failed"

        try:
            # Extract Action (BUY/SELL/HOLD)
            action_match = re.search(r"ACTION:\s*(\*\*)*(BUY|SELL|HOLD)(\*\*)*", response, re.IGNORECASE)
            if action_match:
                action = action_match.group(2).upper()

            # Extract Score (Handles decimals, markdown, etc.)
            score_match = re.search(r"SCORE:\s*(\*\*)*(\d+\.?\d*)(\*\*)*", response)
            if score_match:
                score = float(score_match.group(2))

            # Extract Reason (Matches everything after REASON: until end of line or next field)
            reason_match = re.search(r"REASON:\s*(.*)", response, re.DOTALL | re.IGNORECASE)
            if reason_match:
                reason = reason_match.group(1).strip().strip('*').strip()
                # Allow multi-line and increase character limit for deeper context
                reason = reason[:1000] 

            print(f"🎯 Parser: Regex Success [{ticker}] -> {action} ({score})")
            
            # Final sanity check: if reason is still default, take whatever response we got
            if (reason == "Analysis synthesis failed" or not reason) and response:
                print(f"⚠️ Parser: Reason missing, extracting fallback block for {ticker}")
                # Take the first 1000 chars of the cleaned response
                reason = response.strip()[:1000]
                
        except Exception as e:
            print(f"❌ Parser: Regex Failed [{ticker}]: {e} | Raw Response: {response}")
            reason = f"Parse fallback: {response[:100]}..."

        # Prepare metadata and Verified Sources
        company_name = financials.get("company_name", "Unknown")
        source_news_url = news_items[0].get("url") if news_items else None
        
        sources = []
        for item in news_items[:3]:
            # Impact labeling based on sentiment
            impact = "Neutral"
            sent = item.get("sentiment_score", 0)
            if sent > 0.1: impact = "Positive"
            elif sent < -0.1: impact = "Negative"
            
            sources.append({
                "title": item.get("title", "Market Update"),
                "publisher": item.get("publisher", "Financial News"),
                "url": item.get("link", "#"),
                "impact": impact
            })

        # 5. Technical Hints (Position Sizing Guidance)
        price = technicals.get("current_price", 0)
        ma50 = technicals.get("ma_50", 0)
        
        # Default Stop at MA50 or 8% risk
        hint_stop = float(ma50 if (ma50 > 0 and ma50 < price) else round(price * 0.92, 2))
        if hint_stop < price * 0.85:
            hint_stop = float(round(price * 0.90, 2))
        
        hint_target = float(round(price + ((price - hint_stop) * 3), 2))
        
        # 6. Save to DB
        # Archive previous active recommendations for this ticker
        statement = update(Recommendation).where(
            Recommendation.ticker == ticker, 
            Recommendation.is_active == True,
            Recommendation.user_id == user_id
        ).values(is_active=False)
        self.session.exec(statement)
        
        # Create new recommendation
        rec = Recommendation(
            ticker=ticker,
            company_name=company_name,
            action=action,
            confidence_score=score,
            reasoning=reason,
            suggested_entry=float(price),
            suggested_stop=hint_stop,
            suggested_target=hint_target,
            date_generated=datetime.utcnow(),
            is_active=True,
            user_id=user_id,
            source_news_url=source_news_url,
            verified_sources=json.dumps(sources),
            is_vcp=is_vcp,
            is_blue_sky=is_blue_sky,
            has_super_trend=has_super_trend,
            rs_rating=float(rs_rating) if rs_rating is not None else None,
            is_decoupled=is_decoupled
        )
        self.session.add(rec)
        self.session.commit()
        self.session.refresh(rec)
        
        # 6. Generate Alert
        from services.alert_service import AlertService
        alert_service = AlertService(self.session)
        alert_service.generate_alerts_from_recommendations(user=None, recommendations=[rec])

        total_duration = (datetime.utcnow() - start_time).total_seconds()
        print(f"🏁 AnalysisService: COMPLETED analysis for {ticker} in {total_duration:.2f}s")
        
        return rec
