from typing import List
from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from database import get_session
from models.tables import Recommendation, User
from auth.security import get_current_user
from services.analysis_service import AnalysisService

router = APIRouter(prefix="/analysis", tags=["analysis"])

@router.post("/{ticker}", response_model=Recommendation)
def analyze_stock(
    ticker: str, 
    force_refresh: bool = False,
    session: Session = Depends(get_session), 
    current_user: User = Depends(get_current_user)
):
    """
    Analyze a stock or fetch existing analysis.
    Set force_refresh=true to ignore cached results and trigger a fresh AI scan.
    """
    service = AnalysisService(session)
    rec = service.analyze_ticker(ticker.upper(), current_user.id, force_refresh=force_refresh)
    return rec

@router.get("/{ticker}/technicals")
def get_technical_data(ticker: str, session: Session = Depends(get_session)):
    """
    Fetch live technical indicators for a ticker.
    """
    from services.finance_service import FinanceService
    finance_service = FinanceService()
    return finance_service.get_technicals(ticker.upper())

@router.get("/recommendations", response_model=List[Recommendation])
def get_recommendations(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    # Return active recommendations for the current user only
    recs = session.exec(
        select(Recommendation).where(
            Recommendation.is_active == True,
            Recommendation.user_id == current_user.id
        )
    ).all()
    return recs

@router.post("/scan")
def trigger_scan(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    """
    Trigger a manual scan of the User's active sectors.
    Returns the list of new recommendations generated.
    """
    from services.scanner_service import ScannerService
    scanner = ScannerService(session)
    
    # Get active sectors
    sectors = current_user.active_sectors.split(",") if current_user.active_sectors else []
    if not sectors:
        return {"message": "No active sectors configured. Please go to Settings."}
        
    results = scanner.scan_active_sectors(sectors, current_user.id)
    
    # Generate Alerts for new recommendations
    from services.alert_service import AlertService
    alert_service = AlertService(session)
    alert_service.generate_alerts_from_recommendations(current_user, results)
    
    # Also check portfolio for any new alerts (Price/Earnings)
    alert_service.generate_alerts_for_portfolio(current_user)
    
    return {
        "status": "scan_complete", 
        "sectors_scanned": sectors,
        "new_recommendations": len(results),
        "details": results
    }
