import yfinance as yf
import pandas as pd
from typing import Dict, Optional, List
from config import SECTOR_2_ETF_MAP

from utils.cache import ttl_cache
from utils.rate_limiter import yahoo_rate_limiter

class FinanceService:
    @ttl_cache(ttl=86400)  # 24 Hour Cache (increased from 1h to reduce API calls)
    def get_financials(self, ticker: str) -> Dict:
        """
        Fetch fundamental data (P/E, EPS, etc.)
        """
        try:
            yahoo_rate_limiter.wait_if_needed()  # Rate limit protection
            stock = yf.Ticker(ticker)
            info = stock.info
            
            return {
                "company_name": info.get("longName", "Unknown"),
                "pe_ratio": info.get("trailingPE", "N/A"),
                "forward_pe": info.get("forwardPE", "N/A"),
                "debt_to_equity": info.get("debtToEquity"),
                "earnings_growth": info.get("earningsGrowth"),
                "revenue_growth": info.get("revenueGrowth"),
                "current_price": info.get("currentPrice")
            }
        except Exception as e:
            print(f"Error fetching financials for {ticker}: {e}")
            return {}

    @ttl_cache(ttl=14400)  # 4 Hour Cache (technicals change slower)
    def get_technicals(self, ticker: str) -> Dict:
        """
        Calculate technical indicators (RSI, MA50, Trend)
        """
        try:
            yahoo_rate_limiter.wait_if_needed()  # Rate limit protection
            # Fetch 3 months of data for MA50
            stock = yf.Ticker(ticker)
            hist = stock.history(period="3mo")
            if hist.empty:
                return {}
            
            # Simple Moving Average (50)
            ma50 = hist['Close'].rolling(window=50).mean().iloc[-1]
            
            # RSI Calculation
            delta = hist['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1]
            
            return {
                "rsi_14": round(current_rsi, 2) if not pd.isna(current_rsi) else None,
                "ma_50": round(ma50, 2) if not pd.isna(ma50) else None,
                "trend": "UP" if hist['Close'].iloc[-1] > ma50 else "DOWN"
            }
        except Exception as e:
            print(f"Error fetching technicals for {ticker}: {e}")
            return {}

    @ttl_cache(ttl=3600)
    def get_sector_performance(self, sector_etf: str) -> Dict:
        """Calculate sector momentum vs S&P 500 (SPY)."""
        try:
            # If sector is Market (SPY), return Neutral
            if sector_etf == "SPY":
                 return {
                    "sector_return_1mo": 0.0,
                    "market_return_1mo": 0.0,
                    "relative_strength": "NEUTRAL"
                }

            sector = yf.Ticker(sector_etf)
            spy = yf.Ticker("SPY")
            
            # 1 Month Performance
            sector_hist = sector.history(period="1mo")
            spy_hist = spy.history(period="1mo")
            
            if sector_hist.empty or spy_hist.empty:
                return {}

            sector_return = (sector_hist['Close'].iloc[-1] - sector_hist['Close'].iloc[0]) / sector_hist['Close'].iloc[0]
            spy_return = (spy_hist['Close'].iloc[-1] - spy_hist['Close'].iloc[0]) / spy_hist['Close'].iloc[0]
            
            # Helper logic for Strength
            if sector_return > spy_return:
                strength = "LEADER"
            elif sector_return < spy_return:
                strength = "LAGGARD"
            else:
                strength = "NEUTRAL"

            return {
                "sector_return_1mo": round(sector_return * 100, 2),
                "market_return_1mo": round(spy_return * 100, 2),
                "relative_strength": strength
            }
        except Exception as e:
            return {}

    @ttl_cache(ttl=86400) # 24 Hour Cache (earnings dates don't change often)
    def get_next_earnings_date(self, ticker: str) -> Optional[str]:
        """
        Get next earnings date
        """
        try:
            yahoo_rate_limiter.wait_if_needed()  # Rate limit protection
            stock = yf.Ticker(ticker)
            calendar = stock.calendar
            # calendar is a dict, keys include 'Earnings Date' (list) or 'Earnings High', etc.
            # yfinance structure varies, safer to try parsing
            if calendar and 'Earnings Date' in calendar:
                dates = calendar['Earnings Date']
                if dates:
                    return str(dates[0].date())
            # Fallback for newer yfinance versions where calendar is a dataframe
            if hasattr(stock, 'earning_dates') and stock.earnings_dates is not None:
                 # Find next future date
                 future_dates = stock.earnings_dates.index[stock.earnings_dates.index > pd.Timestamp.now()]
                 if not future_dates.empty:
                     return str(future_dates[-1].date()) # Closest future date
            return None
        except Exception as e:
            print(f"Error fetching earnings date for {ticker}: {e}")
            return None

    @ttl_cache(ttl=86400) # 24 Hours (Sectors rarely change)
    def get_stock_sector(self, ticker: str) -> Dict[str, str]:
        """
        Identify the sector of a ticker and return its name and proxy ETF.
        Returns: {"name": "Technology", "etf": "XLK"} or None/Default
        """
        try:
            stock = yf.Ticker(ticker)
            sector_name = stock.info.get('sector', 'Unknown')
            
            # Map yfinance sector names to SPDR ETFs            
            etf = SECTOR_2_ETF_MAP.get(sector_name)
            
            # Fallback for subsets or if exact match fails
            if not etf:
                return {"name": sector_name, "etf": "SPY"} # Default to Market
                
            return {"name": sector_name, "etf": etf}
            
            
        except Exception as e:
            return {"name": "Unknown", "etf": "SPY"}

    @ttl_cache(ttl=86400) # 24h cache for the fetch itself, though DB will cache for 30 days
    def get_etf_holdings(self, etf_ticker: str) -> List[str]:
        """
        Fetches top 10 holdings for an ETF.
        Tries yfinance, falls back to static map if failed/empty.
        """
        # Static Fallback Map (Mini version)
        FALLBACK_MAP = {
            "XLK": ["NVDA", "MSFT", "AAPL", "AVGO", "ORCL", "CRM", "AMD", "ADBE", "QCOM", "TXN"],
            "XLF": ["JPM", "V", "MA", "BAC", "WFC", "MS", "GS", "AXP", "BLK", "C"],
            "XLV": ["LLY", "UNH", "JNJ", "ABBV", "MRK", "TMO", "AMGN", "PFE", "ISRG", "DHR"],
            "XLE": ["XOM", "CVX", "COP", "EOG", "SLB", "MPC", "PSX", "VLO", "WMB", "OKE"],
            "XLY": ["AMZN", "TSLA", "HD", "MCD", "NKE", "LOW", "SBUX", "BKNG", "TJX", "MAR"],
            "SOXX": ["NVDA", "AVGO", "AMD", "QCOM", "TXN", "MU", "INTC", "AMAT", "LRCX", "ADI"],
            "ITA": ["RTX", "LMT", "GD", "NOC", "BA", "TDG", "LHX", "HWM", "TXT", "AXON"],
            "XLC": ["GOOGL", "META", "NFLX", "DIS", "TMUS", "CMCSA", "VZ", "T", "CHTR", "WBD"],
            'XLP': ['WMT', 'COST', 'PG', 'KO', 'PM', 'PEP', 'MDLZ', 'MO', 'CL', 'MNST'],
            'XLI': ['GE', 'CAT', 'RTX', 'BA', 'UBER', 'GEV', 'UNP', 'HON', 'ETN', 'DE'],
            'XLB': ['LIN', 'NEM', 'CRH', 'SHW', 'FCX', 'ECL', 'APD', 'CTVA', 'MLM', 'NUE'],
            'XLU': ['NEE', 'CEG', 'SO', 'DUK', 'AEP', 'SRE', 'VST', 'D', 'EXC', 'XEL'],
        }
        
        try:
            # Try Live Fetch
            # Note: yf.Ticker(etf).funds_data.top_holdings is available in newer versions
            # But structure varies. We'll try a safe approach.
            stock = yf.Ticker(etf_ticker)
            
            # Method 1: funds_data (Best actions)
            if hasattr(stock, 'funds_data') and stock.funds_data:
                 holdings = stock.funds_data.top_holdings
                 if holdings:
                     # holdings is often a dict {ticker: percent} or dataframe
                     if isinstance(holdings, pd.DataFrame):
                         return list(holdings.index)[:10]
                     elif isinstance(holdings, dict):
                         return list(holdings.keys())[:10]

            # Method 2: Fallback to static
            return FALLBACK_MAP.get(etf_ticker, [])
            
        except Exception as e:
            print(f"Error fetching holdings for {etf_ticker}: {e}")
            return FALLBACK_MAP.get(etf_ticker, [])
