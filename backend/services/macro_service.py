import yfinance as yf
import pandas as pd
from typing import Dict, List
from utils.cache import ttl_cache
from utils.rate_limiter import yahoo_rate_limiter

class MarketMacroService:
    """
    Service to fetch and analyze inter-market correlations
    focusing on USD (DXY), 10Y Yields (TNX), and Commodities.
    """
    
    MACRO_TICKERS = {
        "DXY": "DX-Y.NYB",    # US Dollar Index
        "TNX": "^TNX",        # 10Y Treasury Yield
        "GOLD": "GC=F",       # Gold Futures
        "OIL": "CL=F",        # Crude Oil Futures
        "SPY": "SPY",         # S&P 500 (Benchmark)
        "VIX": "^VIX"         # Volatility Index
    }

    @ttl_cache(ttl=43200) # 12 Hour Cache
    def get_macro_indicators(self) -> Dict:
        """
        Fetches current levels and 1-week changes for key macro assets.
        """
        results = {}
        try:
            yahoo_rate_limiter.wait_if_needed()
            # Batch download for speed
            tickers = list(self.MACRO_TICKERS.values())
            data = yf.download(tickers, period="1mo", interval="1d", progress=False)
            
            # Use multi-index data access
            if isinstance(data.columns, pd.MultiIndex):
                close_data = data['Close']
            else:
                close_data = data
                
            for label, ticker in self.MACRO_TICKERS.items():
                if ticker not in close_data.columns:
                    continue
                    
                asset_data = close_data[ticker].dropna()
                if asset_data.empty:
                    continue
                    
                current_val = asset_data.iloc[-1]
                prev_week_val = asset_data.iloc[-5] if len(asset_data) >= 5 else asset_data.iloc[0]
                
                change_pct = (current_val - prev_week_val) / prev_week_val
                
                results[label] = {
                    "value": round(current_val, 2),
                    "change_1w_pct": round(change_pct * 100, 2),
                    "sentiment": self._get_asset_sentiment(label, change_pct)
                }
            
            return results
        except Exception as e:
            print(f"Error fetching macro indicators: {e}")
            return {}

    def _get_asset_sentiment(self, label: str, change: float) -> str:
        """
        Simple directional sentiment logic from an equity trader's perspective.
        """
        # Rising yields or dollar are generally "Bearish" for Equities (especially Tech)
        if label in ["DXY", "TNX", "VIX"]:
            return "BEARISH" if change > 0.01 else "BULLISH" if change < -0.01 else "NEUTRAL"
        
        # Rising Gold/Oil can be mixed, but generally inflationary (Bearish for bonds/rates)
        return "BULLISH" if change > 0.01 else "BEARISH" if change < -0.01 else "NEUTRAL"

    @ttl_cache(ttl=86400)
    def get_correlations(self) -> Dict:
        """
        Calculates 1-month correlation between SPY and Macro drivers.
        """
        try:
            yahoo_rate_limiter.wait_if_needed()
            tickers = list(self.MACRO_TICKERS.values())
            data = yf.download(tickers, period="3mo", interval="1d", progress=False)
            
            if isinstance(data.columns, pd.MultiIndex):
                close_data = data['Close']
            else:
                close_data = data
                
            corr_matrix = close_data.corr()
            if "SPY" not in corr_matrix:
                return {}
                
            spy_corr = corr_matrix["SPY"].to_dict()
            
            # Map back to human labels
            named_corr = {}
            for label, ticker in self.MACRO_TICKERS.items():
                if ticker in spy_corr:
                    named_corr[label] = round(spy_corr[ticker], 2)
            
            return named_corr
        except Exception as e:
            print(f"Error calculating macro correlations: {e}")
            return {}
