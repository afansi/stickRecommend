from services.finance_service import FinanceService
import pandas as pd

def test_region_aware_benchmarks():
    service = FinanceService()
    
    test_cases = [
        {"ticker": "AAPL", "expected": "SPY"},    # US
        {"ticker": "AIR.PA", "expected": "^FCHI"}, # France
        {"ticker": "SAP.DE", "expected": "^GDAXI"}, # Germany
        {"ticker": "SHOP.TO", "expected": "^GSPTSE"}, # Canada
        {"ticker": "HSBA.L", "expected": "^FTSE"}, # UK
    ]
    
    print("\n🌍 Testing Region-Aware Benchmarking Logic...")
    for case in test_cases:
        ticker = case["ticker"]
        benchmark = service._get_benchmark_for_ticker(ticker)
        print(f"Ticker: {ticker:10} | Detected Benchmark: {benchmark:10} | {'✅' if benchmark == case['expected'] else '❌'}")

    print("\n🔍 Verifying Relative Strength Data for AIR.PA (France)...")
    rs_data = service.get_relative_strength("AIR.PA")
    print(f"AIR.PA Benchmark used: {rs_data.get('benchmark')}")
    print(f"RS Score: {rs_data.get('rs_score')}")
    print(f"Is Decoupled: {rs_data.get('is_decoupled')}")

if __name__ == "__main__":
    test_region_aware_benchmarks()
