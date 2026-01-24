from typing import List
from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from database import get_session
from models.tables import Alert, User
from auth.security import get_current_user
from services.alert_service import AlertService

router = APIRouter(prefix="/alerts", tags=["alerts"])

@router.get("", response_model=List[Alert])
def get_alerts(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    """
    Get unread alerts for the current user, sorted by severity and date.
    """
    alerts = session.exec(
        select(Alert).where(
            Alert.user_id == current_user.id,
            Alert.is_read == False
        ).order_by(Alert.date_created.desc())
    ).all()
    
    # Sort by severity (HIGH -> MEDIUM -> LOW)
    severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    sorted_alerts = sorted(alerts, key=lambda a: severity_order.get(a.severity, 3))
    
    return sorted_alerts

@router.patch("/{alert_id}/read")
def mark_alert_read(alert_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    """
    Mark an alert as read.
    """
    alert = session.get(Alert, alert_id)
    if not alert or alert.user_id != current_user.id:
        return {"error": "Alert not found"}
    
    alert.is_read = True
    session.add(alert)
    session.commit()
    
    return {"status": "marked_read"}

@router.post("/generate")
def generate_alerts(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    """
    Manually trigger alert generation for current user's portfolio.
    """
    alert_service = AlertService(session)
    
    # Generate portfolio alerts
    portfolio_alerts = alert_service.generate_alerts_for_portfolio(current_user)
    
    # Cleanup old alerts
    alert_service.cleanup_old_alerts(current_user)
    
    return {
        "status": "generated",
        "new_alerts": len(portfolio_alerts)
    }
