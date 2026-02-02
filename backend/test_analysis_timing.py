from services.analysis_service import AnalysisService
from models.tables import Recommendation
from sqlmodel import Session, create_engine
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/stock_app")
engine = create_engine(DATABASE_URL)

def test_timing():
    with Session(engine) as session:
        service = AnalysisService(session)
        print("Starting analysis for AME...")
        rec = service.analyze_ticker("AME", user_id=1, force_refresh=True)
        print(f"Analysis complete. Action: {rec.action}, Score: {rec.confidence_score}")

if __name__ == "__main__":
    test_timing()
