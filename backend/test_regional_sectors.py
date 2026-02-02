import sys
import os

# Add the parent directory to sys.path
sys.path.append(os.getcwd())

from services.finance_service import FinanceService

def test_regional_benchmarks():
    f_service = FinanceService()
    
    test_cases = [
        {"ticker": "NVDA", "expected_region": "US", "expected_etf": "XLK"},
        {"ticker": "SAP.DE", "expected_region": "EU", "expected_etf": "EXV3.DE"},
        {"ticker": "LVMH.PA", "expected_region": "EU", "expected_etf": "EXV2.DE"}, # Consumer Cyclical
        {"ticker": "SHOP.TO", "expected_region": "CA", "expected_etf": "XIT.TO"},
        {"ticker": "RY.TO", "expected_region": "CA", "expected_etf": "XFN.TO"},
    ]
    
    print("\n🧪 Testing Regional Sector Benchmarks...")
    print("-" * 50)
    
    for case in test_cases:
        ticker = case["ticker"]
        region = f_service._get_region_for_ticker(ticker)
        metadata = f_service.get_stock_metadata(ticker)
        sector = metadata["sector"]["name"]
        etf = metadata["sector"]["etf"]
        
        print(f"Ticker: {ticker: <8} | Region: {region: <3} | Sector: {sector: <20} | ETF: {etf: <10}")
        
        # Check against expectations if provided
        if "expected_etf" in case:
            if etf == case["expected_etf"]:
                print(f"  ✅ MATCH: {etf}")
            else:
                print(f"  ❌ MISMATCH: Expected {case['expected_etf']}, got {etf}")
        print("-" * 50)

    print("\n🧪 Testing Regional News & Holdings...")
    print("-" * 50)
    from services.news_service import NewsService
    n_service = NewsService()
    
    # Test European Tech News
    print("Checking EU Tech News (SAP.DE region)...")
    eu_news = n_service.fetch_sector_news("Technology", region="EU")
    print(f"Found {len(eu_news)} news items for EU Technology.")
    if eu_news:
        print(f"Sample: {eu_news[0]['title']}")
        
    print("-" * 50)
    # Test Canadian Finance Holdings
    print("Checking CA Financial Holdings (XFN.TO)...")
    ca_holdings = f_service.get_etf_holdings("XFN.TO")
    print(f"Found {len(ca_holdings)} holdings for XFN.TO.")
    if ca_holdings:
        print(f"Sample: {ca_holdings[:3]}")

if __name__ == "__main__":
    test_regional_benchmarks()
