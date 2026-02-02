import threading
import time
from services.finance_service import FinanceService
from sqlmodel import Session, create_engine
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/stock_app")
engine = create_engine(DATABASE_URL)

def simulate_fetch(thread_id):
    # Each thread creates its own service instance (simulating different parts of the app)
    # The cache should be shared globally across all instances!
    service = FinanceService()
    print(f"Thread {thread_id}: Requesting XEG.TO holdings...")
    holdings = service.get_etf_holdings("XEG.TO")
    print(f"Thread {thread_id}: Got {len(holdings)} holdings.")

def test_concurrency():
    threads = []
    # Launch 5 threads simultaneously
    for i in range(5):
        t = threading.Thread(target=simulate_fetch, args=(i,))
        threads.append(t)
        
    for t in threads:
        t.start()
        
    for t in threads:
        t.join()

if __name__ == "__main__":
    test_concurrency()
