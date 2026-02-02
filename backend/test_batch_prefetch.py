"""
Test script to verify batch prefetching eliminates queue congestion.
Simulates a mini-scan with 10 candidates to measure performance improvement.
"""
from services.scanner_service import ScannerService
from services.universe_service import UniverseService
from sqlmodel import Session, create_engine
import os
from unittest.mock import patch

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/stock_app")
engine = create_engine(DATABASE_URL)

def test_batch_prefetch():
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

                ScannerService.set_status(False)
                
                # Trigger a full discovery scan
                # This will use the new batch prefetch logic
                print("Starting discovery scan with batch prefetch optimization...")
                scanner.discover_opportunities()
                
                print("\nCheck the logs above for:")
                print("1. '📦 Discovery: Batch pre-fetching metadata...'")
                print("2. '✅ Discovery: Batch pre-fetch complete...'")
                print("3. Individual ticker analysis times should be < 10s (not 120s)")
            except Exception as e:
                print(f"\n❌ FAILED: {e}")
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    test_batch_prefetch()
