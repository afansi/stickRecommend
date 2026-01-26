import yfinance as yf
import pandas as pd
from typing import Dict, Optional, List
from config import SECTOR_2_ETF_MAP

from utils.cache import ttl_cache
from utils.rate_limiter import yahoo_rate_limiter

class FinanceService:
    @ttl_cache(ttl=86400)
    def get_stock_metadata(self, ticker: str) -> Dict:
        """
        Fetch all metadata (financials + sector) in one go to save API calls.
        """
        try:
            yahoo_rate_limiter.wait_if_needed()
            stock = yf.Ticker(ticker)
            info = stock.info
            
            sector_name = info.get('sector', 'Unknown')
            etf = SECTOR_2_ETF_MAP.get(sector_name, "SPY")

            return {
                "financials": {
                    "company_name": info.get("longName", "Unknown"),
                    "pe_ratio": info.get("trailingPE", "N/A"),
                    "forward_pe": info.get("forwardPE", "N/A"),
                    "debt_to_equity": info.get("debtToEquity"),
                    "earnings_growth": info.get("earningsGrowth"),
                    "revenue_growth": info.get("revenueGrowth"),
                    "current_price": info.get("currentPrice")
                },
                "sector": {
                    "name": sector_name,
                    "etf": etf
                }
            }
        except Exception as e:
            print(f"Error fetching metadata for {ticker}: {e}")
            return {"financials": {}, "sector": {"name": "Unknown", "etf": "SPY"}}

    def get_financials(self, ticker: str) -> Dict:
        """Deprecated: Use get_stock_metadata"""
        return self.get_stock_metadata(ticker).get("financials", {})

    def get_stock_sector(self, ticker: str) -> Dict[str, str]:
        """Deprecated: Use get_stock_metadata"""
        return self.get_stock_metadata(ticker).get("sector", {})

    @ttl_cache(ttl=14400)  # 4 Hour Cache
    def get_technicals(self, ticker: str) -> Dict:
        """
        Calculate technical indicators (RSI, MACD, Bollinger Bands, Moving Averages)
        """
        try:
            yahoo_rate_limiter.wait_if_needed()
            # Fetch 1 year of data to support MA200 and long-term trends
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1y")
            if hist.empty:
                return {}
            
            close = hist['Close']
            
            # 1. Moving Averages
            ma50 = close.rolling(window=50).mean().iloc[-1]
            ma200 = close.rolling(window=200).mean().iloc[-1]
            current_price = close.iloc[-1]
            
            # 2. RSI Calculation
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1]
            
            # 3. MACD Calculation
            ema12 = close.ewm(span=12, adjust=False).mean()
            ema26 = close.ewm(span=26, adjust=False).mean()
            macd_line = ema12 - ema26
            signal_line = macd_line.ewm(span=9, adjust=False).mean()
            
            # 4. Bollinger Bands (20-day)
            bb_middle = close.rolling(window=20).mean()
            bb_std = close.rolling(window=20).std()
            bb_upper = bb_middle + (bb_std * 2)
            bb_lower = bb_middle - (bb_std * 2)
            
            return {
                "current_price": round(current_price, 2),
                "rsi_14": round(current_rsi, 2) if not pd.isna(current_rsi) else None,
                "ma_50": round(ma50, 2) if not pd.isna(ma50) else None,
                "ma_200": round(ma200, 2) if not pd.isna(ma200) else None,
                "macd": {
                    "line": round(macd_line.iloc[-1], 3),
                    "signal": round(signal_line.iloc[-1], 3),
                    "histogram": round(macd_line.iloc[-1] - signal_line.iloc[-1], 3)
                },
                "bollinger": {
                    "upper": round(bb_upper.iloc[-1], 2),
                    "middle": round(bb_middle.iloc[-1], 2),
                    "lower": round(bb_lower.iloc[-1], 2)
                },
                "trend": "BULLISH" if current_price > ma50 and current_price > ma200 else "BEARISH" if current_price < ma50 else "NEUTRAL"
            }
        except Exception as e:
            print(f"Error fetching technicals for {ticker}: {e}")
            return {}
    @ttl_cache(ttl=3600)
    def get_market_performance(self, ticker: str = "SPY") -> float:
        """
        Get 1-month return for the market proxy (SPY).
        Cached independently to prevent redundant fetches across different sectors.
        """
        try:
            yahoo_rate_limiter.wait_if_needed()
            spy = yf.Ticker(ticker)
            spy_hist = spy.history(period="1mo")
            if spy_hist.empty:
                return 0.0
            return (spy_hist['Close'].iloc[-1] - spy_hist['Close'].iloc[0]) / spy_hist['Close'].iloc[0]
        except Exception as e:
            print(f"Error fetching market performance: {e}")
            return 0.0

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

            yahoo_rate_limiter.wait_if_needed()  # Rate limit protection

            sector = yf.Ticker(sector_etf)
            
            # 1 Month Performance (Sector)
            sector_hist = sector.history(period="1mo")
            if sector_hist.empty:
                return {}

            # Use Cached Market Performance
            spy_return = self.get_market_performance("SPY")
            sector_return = (sector_hist['Close'].iloc[-1] - sector_hist['Close'].iloc[0]) / sector_hist['Close'].iloc[0]
            
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

    @ttl_cache(ttl=86400) # 24 Hour Cache
    def get_next_earnings_date(self, ticker: str) -> Optional[str]:
        """
        Get next earnings date safely handling both datetime and date objects.
        """
        try:
            yahoo_rate_limiter.wait_if_needed()
            stock = yf.Ticker(ticker)
            calendar = stock.calendar
            
            # Helper to safely get string date
            def to_date_str(dt_obj):
                if hasattr(dt_obj, 'date'):
                    return str(dt_obj.date())
                return str(dt_obj)

            if calendar and 'Earnings Date' in calendar:
                dates = calendar['Earnings Date']
                if dates and len(dates) > 0:
                    return to_date_str(dates[0])

            # Fallback for newer yfinance versions
            if hasattr(stock, 'earnings_dates') and stock.earnings_dates is not None:
                 future_dates = stock.earnings_dates.index[stock.earnings_dates.index > pd.Timestamp.now(tz=None)]
                 if not future_dates.empty:
                      return to_date_str(future_dates[0]) # Closest future date is the first in a filtered index
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
        Tries yfinance 1.0 funds_data, falls back to static map if failed/empty.
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
            print(f"FinanceService: Attempting live fetch for {etf_ticker} holdings...")
            stock = yf.Ticker(etf_ticker)
            
            # Method 1: yfinance 1.0 funds_data (Dynamic)
            if hasattr(stock, 'funds_data') and stock.funds_data is not None:
                holdings = stock.funds_data.top_holdings
                if holdings is not None and not holdings.empty:
                    # Symbol is in the index of the DataFrame
                    symbols = [s for s in holdings.index.tolist() if s and isinstance(s, str)]
                    if symbols:
                        print(f"FinanceService: Successfully fetched {len(symbols)} dynamic holdings for {etf_ticker}")
                        return symbols[:10]

            print(f"FinanceService: Live fetch failed or empty for {etf_ticker}. Using fallback map.")
            return FALLBACK_MAP.get(etf_ticker, [])
            
        except Exception as e:
            print(f"Error fetching holdings for {etf_ticker}: {e}")
            return FALLBACK_MAP.get(etf_ticker, [])

    @ttl_cache(ttl=3600)
    def batch_get_technicals(self, tickers: List[str]) -> Dict[str, Dict]:
        """
        Optimized technical fetch for multiple tickers.
        """
        if not tickers:
            return {}
            
        try:
            # yfinance download is faster for multiple tickers than individual fetches
            # Use 3 months of data to ensure we have enough for MA50 and RSI
            data = yf.download(tickers, period="3mo", group_by="ticker", threads=True, progress=False)
            
            results = {}
            for ticker in tickers:
                try:
                    # Handle single ticker edge case (different df structure)
                    ticker_data = data[ticker] if len(tickers) > 1 else data
                    
                    if ticker_data.empty:
                        continue
                        
                    # Basic calculations
                    close_prices = ticker_data['Close']
                    ma50 = close_prices.rolling(window=50).mean().iloc[-1]
                    
                    # Simple RSI
                    delta = close_prices.diff()
                    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                    rs = gain / loss
                    rsi = 100 - (100 / (1 + rs))
                    current_rsi = rsi.iloc[-1]
                    
                    current_price = close_prices.iloc[-1]
                    
                    results[ticker] = {
                        "rsi_14": round(current_rsi, 2) if not pd.isna(current_rsi) else None,
                        "ma_50": round(ma50, 2) if not pd.isna(ma50) else None,
                        "trend": "UP" if current_price > ma50 else "DOWN",
                        "current_price": round(current_price, 2)
                    }
                except Exception:
                    continue
            return results
        except Exception as e:
            print(f"Batch Technicals failed: {e}")
            # Fallback to individual fetches (slower but safer)
            return {t: self.get_technicals(t) for t in tickers}
