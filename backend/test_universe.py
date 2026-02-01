import sys
import os

# Add the parent directory to sys.path to allow imports from services
sys.path.append(os.getcwd())

from services.universe_service import UniverseService, SECTOR_CACHE

def test_universe_scraping():
    print("🧪 Starting UniverseService Scraping Test...")
    service = UniverseService()
    try:
        tickers = service._get_all_raw_tickers()
        print(f"\n✅ SUCCESS: Scraped {len(tickers)} total unique tickers.")
        print("\nSample Tickers (First 20):")
        print(tickers[:20])
        
        print("\nSample Tickers (Last 20):")
        print(tickers[-20:])
        
        # Check for international suffixes
        international = [t for t in tickers if "." in t or "-" in t]
        print(f"\n🌍 International/Special Tickers Found: {len(international)}")
        if international:
            print(f"Sample International: {international[:10]}")

        # Check Sector Cache
        print(f"\n🏭 Sectors Cached: {len(SECTOR_CACHE)}")
        if SECTOR_CACHE:
            print("Sample Sectors:")
            # Print 5 samples
            for t in list(SECTOR_CACHE.keys())[:5]:
                print(f"  {t}: {SECTOR_CACHE[t][0]}")
            
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_universe_scraping()
