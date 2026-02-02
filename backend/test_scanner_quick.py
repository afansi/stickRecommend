import sys
import os

# Add the parent directory to sys.path to allow imports from services
sys.path.append(os.getcwd())

from sqlmodel import Session
from database import engine
from services.scanner_service import ScannerService
from services.universe_service import UniverseService
from unittest.mock import patch

def test_scanner_quick():
    print("🧪 Starting ScannerService Discovery Test (Limited to 10 tickers)...")
    
    with Session(engine) as session:
        scanner = ScannerService(session)
        
        # Monkeypatch UniverseService to return a smaller set for speed
        original_get_universe = scanner.universe_service.get_investable_universe
        
        def mock_get_universe(*args, **kwargs):
            full_universe = original_get_universe(*args, **kwargs)
            return full_universe[:10] if full_universe else []
            
        with patch.object(UniverseService, 'get_investable_universe', side_effect=mock_get_universe):
            print("🔭 Triggering discover_opportunities()...")
            try:
                # Force scanning flag to False just in case
                ScannerService.set_status(False)
                
                opportunities = scanner.discover_opportunities()
                print(f"\n✅ SUCCESS: Found {len(opportunities)} opportunities.")
                
                if opportunities:
                    print("\nAll Results:")
                    for i, opp in enumerate(opportunities):
                        print(f"\n--- Opportunity {i+1} ---")
                        print(f"Ticker: {opp.ticker}")
                        print(f"Sector: {opp.sector}")
                        print(f"Action: {opp.action}")
                        print(f"Reasoning: {opp.reasoning[:200]}...")
                        print(f"Setup: VCP={opp.is_vcp}, BlueSky={opp.is_blue_sky}, SuperTrend={opp.has_super_trend}")
                        print(f"Entry: {opp.suggested_entry}, Stop: {opp.suggested_stop}, Target: {opp.suggested_target}")
                else:
                    print("No opportunities found in the limited set.")
                    
            except Exception as e:
                print(f"\n❌ FAILED: {e}")
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    test_scanner_quick()
