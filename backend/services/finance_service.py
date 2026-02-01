import yfinance as yf
import pandas as pd
from typing import Dict, Optional, List
from config import SECTOR_2_ETF_MAP

from utils.cache import ttl_cache
from utils.rate_limiter import yahoo_rate_limiter

class FinanceService:
    @ttl_cache(ttl=86400) # 24 Hours (Sectors rarely change)
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
                "current_price": float(round(current_price, 2)),
                "rsi_14": float(round(current_rsi, 2)) if not pd.isna(current_rsi) else None,
                "ma_50": float(round(ma50, 2)) if not pd.isna(ma50) else None,
                "ma_200": float(round(ma200, 2)) if not pd.isna(ma200) else None,
                "macd": {
                    "line": float(round(macd_line.iloc[-1], 3)),
                    "signal": float(round(signal_line.iloc[-1], 3)),
                    "histogram": float(round(macd_line.iloc[-1] - signal_line.iloc[-1], 3))
                },
                "bollinger": {
                    "upper": float(round(bb_upper.iloc[-1], 2)),
                    "middle": float(round(bb_middle.iloc[-1], 2)),
                    "lower": float(round(bb_lower.iloc[-1], 2))
                },
                "trend": "UP" if (ma50 and ma200 and current_price > ma50 and current_price > ma200) else "DOWN" if (ma50 and current_price < ma50) else "NEUTRAL"
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
                        "rsi_14": float(round(current_rsi, 2)) if not pd.isna(current_rsi) else None,
                        "ma_50": float(round(ma50, 2)) if not pd.isna(ma50) else None,
                        "trend": "UP" if current_price > ma50 else "DOWN",
                        "current_price": float(round(current_price, 2))
                    }
                except Exception:
                    continue
            return results
        except Exception as e:
            print(f"Batch Technicals failed: {e}")
            # Fallback to individual fetches (slower but safer)
            return {t: self.get_technicals(t) for t in tickers}

    @ttl_cache(ttl=43200) # 12 Hour Cache
    def get_weekly_technicals(self, ticker: str) -> Dict:
        """
        Calculate Weekly Technicals (W1):
        - 30-week MA (MM30W) - Stan Weinstein Stage indicator
        - 10-week MA (MM10W) - Short-term momentum
        - Weekly RSI(14)
        - Bollinger Band Width (Volatility Compression)
        """
        try:
            yahoo_rate_limiter.wait_if_needed()
            stock = yf.Ticker(ticker)
            # Fetch 2 years to ensure enough history for 30-week MA
            hist = stock.history(period="2y", interval="1wk")
            if hist.empty or len(hist) < 30:
                return {}

            close = hist['Close']
            
            # 1. Weekly Moving Averages
            ma10w = close.rolling(window=10).mean().iloc[-1]
            ma30w = close.rolling(window=30).mean().iloc[-1]
            prev_ma30w = close.rolling(window=30).mean().iloc[-2]
            
            # 2. Weekly RSI
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            # 3. Bollinger Band Width
            bb_middle = close.rolling(window=20).mean()
            bb_std = close.rolling(window=20).std()
            bb_upper = bb_middle + (bb_std * 2)
            bb_lower = bb_middle - (bb_std * 2)
            bb_width = (bb_upper - bb_lower) / bb_middle
            
            # 4. Volatility Compression Check (is width at 52-week low?)
            bbw_52w_low = bb_width.rolling(window=52).min().iloc[-1]
            is_compressed = bb_width.iloc[-1] <= (bbw_52w_low * 1.1) # Within 10% of 52w low

            # 5. 52-Week High (for Blue Sky setups)
            high_52w = hist['High'].rolling(window=52).max().iloc[-1]

            return {
                "ma_10w": float(round(ma10w, 2)),
                "ma_30w": float(round(ma30w, 2)),
                "ma_30w_slope": "UP" if ma30w > prev_ma30w else "DOWN",
                "rsi_w1": float(round(rsi.iloc[-1], 2)),
                "bb_width": float(round(bb_width.iloc[-1], 4)),
                "is_vcp": bool(is_compressed),
                "current_price": float(round(close.iloc[-1], 2)),
                "high_52w": float(round(high_52w, 2))
            }
        except Exception as e:
            print(f"Error fetching weekly technicals for {ticker}: {e}")
            return {}

    @ttl_cache(ttl=86400)
    def get_relative_strength(self, ticker: str, benchmark: str = "SPY") -> Dict:
        """
        Calculate Relative Strength Rating:
        Performance of stock vs benchmark over the last 6 months.
        """
        try:
            yahoo_rate_limiter.wait_if_needed()
            stock = yf.Ticker(ticker)
            spy = yf.Ticker(benchmark)
            
            # 6-month performance
            hist_stock = stock.history(period="6mo")
            hist_spy = spy.history(period="6mo")
            
            if hist_stock.empty or hist_spy.empty:
                return {"rs_score": 0, "alpha_flag": False}

            stock_ret = (hist_stock['Close'].iloc[-1] - hist_stock['Close'].iloc[0]) / hist_stock['Close'].iloc[0]
            spy_ret = (hist_spy['Close'].iloc[-1] - hist_spy['Close'].iloc[0]) / hist_spy['Close'].iloc[0]
            
            # Alpha Flag: Stock up while market down in last week?
            last_week_stock = (hist_stock['Close'].iloc[-1] - hist_stock['Close'].iloc[-5]) / hist_stock['Close'].iloc[-5]
            last_week_spy = (hist_spy['Close'].iloc[-1] - hist_spy['Close'].iloc[-5]) / hist_spy['Close'].iloc[-5]
            
            # Compare vs Benchmark
            alpha_flag = last_week_stock > 0 and last_week_spy < 0

            # Calculate a simplified "Rating" (0-100) based on ratio
            # A ratio of 1.0 means it matched the market. 
            # We'll map a 2.0 ratio (2x market) to ~90 score.
            rs_score = 50 + (stock_ret / spy_ret * 20) if spy_ret > 0 else 50
            rs_score = min(max(rs_score, 1), 99) # Clip between 1-99

            # Institutional "Decoupling" Check: 1-month correlation vs SPY
            # Low correlation (<0.4) + High RS (>80) = Institutional Accumulation
            is_decoupled = False
            try:
                # 1 Month correlation
                s_1m = hist_stock['Close'].iloc[-21:] # ~21 trading days
                m_1m = hist_spy['Close'].iloc[-21:]
                if len(s_1m) == len(m_1m) and len(s_1m) > 10:
                    corr = s_1m.corr(m_1m)
                    if corr < 0.4 and rs_score > 80:
                        is_decoupled = True
                        print(f"💎 Institutional Alpha: {ticker} DECOUPLED from SPY (Corr: {corr:.2f}, RS: {rs_score})")
            except Exception:
                pass

            return {
                "ticker_ret_6mo": float(round(stock_ret * 100, 2)),
                "spy_ret_6mo": float(round(spy_ret * 100, 2)),
                "rs_ratio": float(round(stock_ret / spy_ret, 2)) if spy_ret != 0 else 0.0,
                "rs_score": float(round(rs_score, 0)),
                "alpha_flag": bool(alpha_flag),
                "is_decoupled": is_decoupled
            }
        except Exception as e:
            print(f"Error calculating RS for {ticker}: {e}")
            return {"rs_score": 0, "alpha_flag": False}
