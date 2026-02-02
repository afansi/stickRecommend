import sys
import os

# Add the parent directory to sys.path to allow imports from services
sys.path.append(os.getcwd())

from sqlmodel import Session
from database import engine
from services.scanner_service import ScannerService

def test_scanner():
    print("🧪 Starting ScannerService Discovery Test...")
    
    with Session(engine) as session:
        scanner = ScannerService(session)
        print("🔭 Triggering discover_opportunities()...")
        try:
            # Force scanning flag to False just in case
            ScannerService.set_status(False)
            
            opportunities = scanner.discover_opportunities()
            print(f"\n✅ SUCCESS: Found {len(opportunities)} opportunities.")
            
            if opportunities:
                print("\nSample Opportunities (First 5):")
                for i, opp in enumerate(opportunities[:5]):
                    print(f"\n--- Opportunity {i+1} ---")
                    print(f"Ticker: {opp.ticker}")
                    print(f"Sector: {opp.sector}")
                    print(f"Action: {opp.action}")
                    print(f"Reasoning: {opp.reasoning[:100]}...") # Truncate reasoning
                    print(f"Setup: VCP={opp.is_vcp}, BlueSky={opp.is_blue_sky}, SuperTrend={opp.has_super_trend}")
                    print(f"Entry: {opp.suggested_entry}, Stop: {opp.suggested_stop}, Target: {opp.suggested_target}")
            else:
                print("No opportunities found.")
                
        except Exception as e:
            print(f"\n❌ FAILED: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_scanner()
