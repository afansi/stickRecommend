import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from typing import List, Dict, Set
import concurrent.futures
import time
import os
import io

# Ticker universe cache (Long term: 7 days)
# Ticker universe cache (Long term: 7 days)
UNIVERSE_CACHE = {} # { "USA": (["AAPL", ...], timestamp), ... }
LIQUIDITY_CACHE = {} # { "AAPL": (is_qualified, timestamp), ... }
SECTOR_CACHE = {} # { "AAPL": ("Technology", timestamp), ... }

INDEX_URLS = {
    "USA_SP500": "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
    "USA_NASDAQ100": "https://en.wikipedia.org/wiki/Nasdaq-100",
    "GER_DAX": "https://en.wikipedia.org/wiki/DAX",
    "FRA_CAC40": "https://en.wikipedia.org/wiki/CAC_40",
    "UK_FTSE100": "https://en.wikipedia.org/wiki/FTSE_100_Index",
    "CAN_TSX60": "https://en.wikipedia.org/wiki/S%26P/TSX_60"
}

SUFFIXES = {
    "GER_DAX": ".DE",
    "FRA_CAC40": ".PA",
    "UK_FTSE100": ".L",
    "CAN_TSX60": ".TO"
}

class UniverseService:
    def __init__(self):
        self.cache_names_expiry = timedelta(days=7)
        self.cache_liquidity_expiry = timedelta(hours=24)
        self.cache_sector_expiry = timedelta(days=7)

    def get_sector_map(self, tickers: List[str]) -> Dict[str, str]:
        """
        Returns a map of Ticker -> Sector, using caching to avoid excessive API calls.
        Items not in cache are fetched in parallel.
        """
        print("🌍 UniverseService: Building Sector Map...")
        global SECTOR_CACHE
        ticker_map = {}
        missing_tickers = []
        
        now = datetime.utcnow()
        for t in tickers:
            if t in SECTOR_CACHE:
                sector, ts = SECTOR_CACHE[t]
                if now - ts < self.cache_sector_expiry:
                    ticker_map[t] = sector
                    continue
            missing_tickers.append(t)
            
        if not missing_tickers:
            return ticker_map
            
        print(f"🌍 UniverseService: Fetching sectors for {len(missing_tickers)} tickers...")
        
        def fetch_sector(t):
            try:
                # 'info' call can be slow, but it's the only reliable source for sector
                info = yf.Ticker(t).info
                s = info.get("sector", "Unknown")
                return t, s
            except:
                return t, "Unknown"

        # Fetch in parallel with higher workers since it's IO bound
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            future_to_ticker = {executor.submit(fetch_sector, t): t for t in missing_tickers}
            for future in concurrent.futures.as_completed(future_to_ticker):
                t, s = future.result()
                SECTOR_CACHE[t] = (s, now)
                ticker_map[t] = s
                
        return ticker_map

    def get_investable_universe(self, min_volume=500000, min_price=5) -> List[str]:
        """
        Main entry point: Returns the filtered global universe.
        """
        print("🌍 UniverseService: Starting Get Investable Universe...")
        all_tickers = self._get_all_raw_tickers()
        print(f"🌍 UniverseService: Scraped {len(all_tickers)} raw tickers. Filtering for liquidity...")
        
        qualified = self._filter_liquidity_batch(all_tickers, min_volume, min_price)
        print(f"✅ UniverseService: {len(qualified)} tickers passed the liquidity gate.")
        return qualified

    def _get_all_raw_tickers(self) -> List[str]:
        global UNIVERSE_CACHE
        global SECTOR_CACHE
        all_tickers = set()
        all_tickers_data = {}
        
        for key, url in INDEX_URLS.items():
            # Check cache
            if key in UNIVERSE_CACHE:
                tickers, timestamp = UNIVERSE_CACHE[key]
                if datetime.utcnow() - timestamp < self.cache_names_expiry:
                    all_tickers.update(tickers)
                    continue

            try:
                print(f"📡 UniverseService: Scraping {key} from Wikipedia...")
                import requests
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                tables = pd.read_html(io.StringIO(response.text))

                df = None
            
                # Chercher le tableau contenant une colonne de type 'Symbol'
                for t in tables:
                    # Normalisation des noms de colonnes pour la détection
                    cols = [str(c[0]) if isinstance(c, tuple) else str(c) for c in t.columns]
                    
                    ticker_col = next((c for c in cols if c in ["Symbol", "Ticker", "Ticker symbol"]), None)
                    sector_col = next((c for c in cols if c in ["GICS Sector", "Sector", "Industry", "ICB Industry", "Prime Standard Sector", "FTSE industry classification benchmark sector"]), None)

                    if ticker_col:
                        suffix = SUFFIXES.get(key, "")
                        all_cleaned = []
                        for _, row in t.iterrows():
                            v = str(row[ticker_col]).strip() if isinstance(row[ticker_col], str) else None
                            if v is not None:
                                v = v[:-len(suffix)] if v.endswith(suffix) and len(suffix) > 0 else v 
                                # Nettoyage : Yahoo utilise '-' au lieu de '.' pour les classes d'actions (ex: BRK.B -> BRK-B)
                                cleaned = str(v).strip().replace('.', '-') + suffix
                                sector = str(row[sector_col]) if sector_col else None
                                all_cleaned.append(cleaned)
                                all_tickers_data[cleaned]= sector

                        UNIVERSE_CACHE[key] = (all_cleaned, datetime.utcnow())
                        print(f"✅ UniverseService: Successfully scraped {len(all_cleaned)} tickers for {key}. Samples: {all_cleaned[:5]}")
                        break
    
            except Exception as e:
                print(f"❌ UniverseService: Error scraping {key}: {e}")
        for k, v in all_tickers_data.items():
            if v is not None:
                SECTOR_CACHE[k] = (v, datetime.utcnow())
        return sorted(list(all_tickers_data.keys()))

    def _filter_liquidity_batch(self, tickers: List[str], min_volume: int, min_price: int) -> List[str]:
        """
        Efficient multi-threaded liquidity check using yfinance.
        """
        print(f"🔍 UniverseService: Starting liquidity check for {len(tickers)} tickers...")
        global LIQUIDITY_CACHE
        qualified = []
        to_check = []

        # Check cache first
        now = datetime.utcnow()
        for t in tickers:
            if t in LIQUIDITY_CACHE:
                is_q, ts = LIQUIDITY_CACHE[t]
                if now - ts < self.cache_liquidity_expiry:
                    if is_q: qualified.append(t)
                    continue
            to_check.append(t)

        if not to_check:
            return qualified

        # Process in chunks of 100 to avoid yfinance timeouts or blocks
        chunk_size = 100
        for i in range(0, len(to_check), chunk_size):
            chunk = to_check[i:i + chunk_size]
            print(f"🔍 UniverseService: Checking liquidity for chunk {i//chunk_size + 1} ({len(chunk)} tickers)...")
            
            try:
                # Group fetch: period 5d is enough for average volume
                data = yf.download(chunk, period="5d", group_by='ticker', threads=True, progress=False, interval="1d")
                
                for ticker in chunk:
                    try:
                        t_data = data[ticker] if len(chunk) > 1 else data
                        if t_data.empty:
                            LIQUIDITY_CACHE[ticker] = (False, now)
                            continue

                        avg_vol = t_data['Volume'].mean()
                        last_price = t_data['Close'].iloc[-1]

                        is_qualified = (avg_vol >= min_volume and last_price >= min_price)
                        if not is_qualified:
                            print(f"🚫 UniverseService: Rejected {ticker} (Vol: {avg_vol}, Price: {last_price})")
                        LIQUIDITY_CACHE[ticker] = (is_qualified, now)
                        if is_qualified:
                            qualified.append(ticker)
                    except Exception:
                        LIQUIDITY_CACHE[ticker] = (False, now)
            except Exception as e:
                print(f"❌ UniverseService: Batch download failed for chunk: {e}")

        return sorted(qualified)
