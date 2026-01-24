from sqlmodel import Session, select, update
from datetime import datetime
from services.news_service import NewsService
from services.llm_engine import LLMFactory
from models.tables import Recommendation, NewsArticle

from config import settings

class AnalysisService:
    def __init__(self, session: Session):
        self.session = session
from services.finance_service import FinanceService

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

    def analyze_ticker(self, ticker: str, user_id: int) -> Recommendation:
        """
        Hybrid Analysis Pipeline:
        1. News (Sentiment)
        2. Financials (Fundamentals: P/E, EPS)
        3. Technicals (RSI, MA50)
        4. LLM Synthesis -> Recommendation
        """
        # 1. Fetch Data
        news_items = self.news_service.fetch_news(ticker)
        financials = self.finance_service.get_financials(ticker)
        technicals = self.finance_service.get_technicals(ticker)
        earnings_date = self.finance_service.get_next_earnings_date(ticker)
        
        # Determine Sector dynamically
        sector_info = self.finance_service.get_stock_sector(ticker)
        sector_etf = sector_info.get("etf", "SPY")
        sector_name = sector_info.get("name", "Unknown")
        
        sector_perf = self.finance_service.get_sector_performance(sector_etf)
        
        # Fetch Sector News (Macro Context)
        sector_news = self.news_service.fetch_news(sector_etf)
        
        # 2. Build Context
        context = f"--- STOCK DATA FOR {ticker} ---\n\n"
        
        # Add Financials & Earnings
        context += "FUNDAMENTALS:\n"
        for k, v in financials.items():
            context += f"- {k}: {v}\n"
        if earnings_date:
            context += f"- Next Earnings Date: {earnings_date} (Potential Run-up Play?)\n"
        
        # Add Technicals
        context += "\nTECHNICALS:\n"
        for k, v in technicals.items():
            context += f"- {k}: {v}\n"

        # Add Sector Momentum
        if sector_perf:
            context += "\nSECTOR MOMENTUM (vs SPY):\n"
            context += f"- 1 Mo Return: {sector_perf.get('sector_return_1mo')}%\n"
            context += f"- Market Return: {sector_perf.get('market_return_1mo')}%\n"
            context += f"- Status: {sector_perf.get('relative_strength')}\n"
            
        # Add News (Specific)
        context += "\nRECENT NEWS (Specific to Ticker):\n"
        if news_items:
            for item in news_items[:5]:
                context += f"- {item.get('title')} ({item.get('providerPublishTime')})\n"
        else:
            context += "(No recent news found)\n"

        # Add News (Sector)
        context += f"\nSECTOR NEWS ({sector_name}/{sector_etf}):\n"
        if sector_news:
            for item in sector_news[:3]: # Top 3 sector stories
                context += f"- {item.get('title')}\n"
        else:
             context += "(No sector news found)\n"

        # 3. Hybrid Strategy Prompt
        prompt = f"""
        You are a sophisticated financial analyst using a Hybrid Strategy.
        Analyze the provided data for {ticker}.
        
        STRATEGY RULES:
        1. FUNDAMENTALS: Check if P/E and PEG indicate value. Growth metrics should be positive.
        2. TECHNICALS: RSI < 30 is Oversold (Potential Buy), RSI > 70 is Overbought. MA50 indicates trend.
        3. SECTOR ROTATION: If Sector is a "LEADER", favor the stock (Momentum). If "LAGGARD", be cautious.
        4. EARNINGS RUN-UP: If Earnings Date is approaching (within 2-3 weeks), look for "Run-up" potential.
        5. NEWS: Look for catalysts.
        
        Synthesize all factors into a Recommendation.
        
        Format your response exactly like this:
        ACTION: [BUY/SELL/HOLD]
        SCORE: [0-10]
        REASON: [Your concise analysis weighting all 5 factors, max 50 words]
        """
        
        # 4. Call LLM
        response = self.llm.analyze_text(text=context, prompt=prompt)
        
        # 5. Parse Response
        action = "HOLD"
        score = 5.0
        reason = "Analysis failed parse"

        
        try:
            lines = response.split('\n')
            for line in lines:
                if "ACTION:" in line:
                    action = line.split("ACTION:")[1].strip().upper()
                if "SCORE:" in line:
                    score = float(line.split("SCORE:")[1].strip())
                if "REASON:" in line:
                    reason = line.split("REASON:")[1].strip()
        except Exception as e:
            reason = f"Parse Error: {str(e)} raw: {response[:20]}..."

        # 5. Save to DB
        # Archive previous active recommendations for this ticker (Bulk Update)
        statement = update(Recommendation).where(
            Recommendation.ticker == ticker, 
            Recommendation.is_active == True,
            Recommendation.user_id == user_id
        ).values(is_active=False)
        self.session.exec(statement)
        
        # Create new recommendation
        rec = Recommendation(
            ticker=ticker,
            action=action,
            confidence_score=score,
            reasoning=reason,
            date_generated=datetime.utcnow(),
            is_active=True,
            user_id=user_id
        )
        self.session.add(rec)
        self.session.commit()
        self.session.refresh(rec)
        
        return rec
