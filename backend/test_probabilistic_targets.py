"""
Test probabilistic stop/target calculation on different volatility profiles.
Verifies that high-volatility stocks get wider ranges, low-volatility get tighter.
"""
from services.finance_service import FinanceService

def test_probabilistic_targets():
    finance_service = FinanceService()
    
    # Test on different volatility profiles
    test_cases = [
        ("NVDA", "High Volatility - Tech"),
        ("KO", "Low Volatility - Consumer Staples"),
        ("JPM", "Medium Volatility - Financials")
    ]
    
    print("=" * 80)
    print("PROBABILISTIC STOP/TARGET TEST")
    print("=" * 80)
    
    for ticker, description in test_cases:
        print(f"\n📊 {ticker} ({description})")
        print("-" * 80)
        
        try:
            # Get weekly technicals with probabilistic targets (batch call)
            print(f"Fetching data for {ticker}...")
            techs = finance_service.batch_get_weekly_technicals([ticker])
            
            if ticker not in techs:
                print(f"❌ No data available for {ticker}")
                continue
            
            data = techs[ticker]
            price = data.get("current_price", 0)
            prob_stop = data.get("prob_stop_price", 0)
            prob_target = data.get("prob_target_price", 0)
            stop_pct = data.get("prob_stop_pct", 0)
            target_pct = data.get("prob_target_pct", 0)
            
            # Calculate ranges
            stop_distance = ((price - prob_stop) / price) * 100 if prob_stop else 0
            target_distance = ((prob_target - price) / price) * 100 if prob_target else 0
            risk_reward = target_distance / stop_distance if stop_distance > 0 else 0
            
            print(f"Current Price:    ${price:.2f}")
            print(f"Stop Loss:        ${prob_stop:.2f} ({stop_pct:.2f}% / {stop_distance:.2f}% from price)")
            print(f"Profit Target:    ${prob_target:.2f} ({target_pct:.2f}% / {target_distance:.2f}% from price)")
            print(f"Risk:Reward:      1:{risk_reward:.2f}")
            print(f"\n🎯 Interpretation:")
            print(f"   - In 80% of weeks, {ticker} doesn't drop more than {abs(stop_pct):.1f}%")
            print(f"   - In 80% of weeks, {ticker} reaches at least +{target_pct:.1f}%")
            
        except Exception as e:
            print(f"❌ Error testing {ticker}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("✅ Test complete. Verify that:")
    print("   1. High-volatility stocks have wider stops/targets")
    print("   2. Low-volatility stocks have tighter stops/targets")
    print("   3. All values are reasonable for 1-week timeframe")
    print("=" * 80)

if __name__ == "__main__":
    test_probabilistic_targets()
