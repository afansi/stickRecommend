from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from database import get_session
from services.reporting_service import ReportingService
from auth.security import get_current_user
from models.tables import User, PerformanceReview

router = APIRouter(prefix="/reporting", tags=["reporting"])

@router.post("/generate-weekend-review")
def generate_review(current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    """
    Manually trigger a weekend performance review.
    """
    service = ReportingService(session)
    review = service.generate_weekend_review(current_user.id)
    if not review:
        raise HTTPException(status_code=400, detail="No active trade plans found to review.")
    return review

@router.get("/latest-review")
def get_latest(current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    """
    Fetch the most recent weekend review.
    Returns None if no review exists.
    """
    service = ReportingService(session)
    review = service.get_latest_review(current_user.id)
    return review
