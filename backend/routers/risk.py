from fastapi import APIRouter, Depends
from services.risk_service import RiskService
from auth.security import get_current_user
from models.tables import User

router = APIRouter(prefix="/risk", tags=["risk"])

@router.get("/monte-carlo")
def run_monte_carlo(ticker: str, entry: float, stop_loss: float, target: float, current_user: User = Depends(get_current_user)):
    """
    Run 10,000 simulations to estimate hit probabilities for target vs stop loss.
    """
    risk_service = RiskService()
    return risk_service.run_monte_carlo(ticker, entry, stop_loss, target)

@router.get("/position-size")
def get_position_size(equity: float, risk_pct: float, entry: float, stop_loss: float, current_user: User = Depends(get_current_user)):
    """
    Calculate optimal share count based on equity risk.
    """
    risk_service = RiskService()
    return risk_service.calculate_position_size(equity, risk_pct, entry, stop_loss)
