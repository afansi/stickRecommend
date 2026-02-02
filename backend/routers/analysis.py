from typing import List, Dict
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlmodel import Session, select
from database import get_session
from models.tables import Recommendation, User, DiscoveryOpportunity
from auth.security import get_current_user
from services.analysis_service import AnalysisService
from services.scanner_service import ScannerService

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

@router.post("/scan", response_model=Dict)
def scan_market(force: bool = False, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    """
    Trigger a manual scan of the User's active sectors.
    Returns the list of new recommendations generated.
    """
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
        "details": [r.dict() for r in results]
    }

@router.get("/discover", response_model=List[DiscoveryOpportunity])
def get_discovery_insights(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    """
    Discovery Engine: Fetches saved institutional weekly setups from the DB.
    Filtered by the user's active sectors.
    """
    # 1. Fetch all global discovery opportunities
    all_opps = session.exec(select(DiscoveryOpportunity)).all()
    
    # 2. Filter by User Sectors
    if not current_user.active_sectors:
        return all_opps # If no sectors chosen, show all (fallback)

    user_sectors = [s.strip().lower() for s in current_user.active_sectors.split(",")]
    
    # Match sector name or keywords (Simplified match for now)
    filtered = [
        opp for opp in all_opps 
        if opp.sector.lower() in user_sectors
    ]
    
    return filtered

@router.get("/discover/status")
def get_discovery_status():
    """Check if a discovery scan is currently running."""
    return ScannerService.get_status()

@router.post("/discover/scan")
def trigger_discovery_scan(
    background_tasks: BackgroundTasks, 
    session: Session = Depends(get_session), 
    current_user: User = Depends(get_current_user)
):
    """Trigger a fresh global discovery scan in the background."""
    if ScannerService.get_status()["is_scanning"]:
        raise HTTPException(status_code=409, detail="A global scan is already in progress.")

    def run_scan():
        # New session for background task
        from database import engine
        from sqlmodel import Session
        with Session(engine) as bg_session:
            try:
                scanner = ScannerService(bg_session)
                scanner.discover_opportunities()
            finally:
                bg_session.close()

    background_tasks.add_task(run_scan)
    return {"message": "Global discovery scan started in background."}
