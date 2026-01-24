import yfinance as yf
from typing import List, Dict

from config import SECTOR_2_ETF_MAP

from utils.cache import ttl_cache

class NewsService:
    @ttl_cache(ttl=1800) # 30 Mins Cache
    def fetch_news(self, ticker: str) -> List[Dict]:
        """
        Fetches latest news for a ticker using yfinance.
        Returns a list of dicts with title, link, publisher, relatedTickers.
        """
        try:
            stock = yf.Ticker(ticker)
            # yfinance news attribute returns a list of dictionaries
            news = stock.news
            return news if news else []
        except Exception as e:
            print(f"Error fetching news for {ticker}: {e}")
            return []

    def fetch_sector_news(self, sector_name: str) -> List[Dict]:
        """
        Fetches news for a broad sector. 
        For MVP, we might use a proxy ETF (e.g., XLK for Tech).
        """
        etf = SECTOR_2_ETF_MAP.get(sector_name)
        if etf:
            return self.fetch_news(etf)
        return []
