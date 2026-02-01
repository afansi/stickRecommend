from fastapi import APIRouter, Depends
from typing import Dict
from services.macro_service import MarketMacroService
from services.finance_service import FinanceService
from auth.security import get_current_user
from models.tables import User

router = APIRouter(prefix="/macro", tags=["macro"])

@router.get("/indicators")
def get_macro_indicators(current_user: User = Depends(get_current_user)):
    """
    Get inter-market levels and sentiment (DXY, TNX, VIX, etc.)
    """
    macro_service = MarketMacroService()
    return macro_service.get_macro_indicators()

@router.get("/correlations")
def get_macro_correlations(current_user: User = Depends(get_current_user)):
    """
    Get SPY correlations with macro drivers.
    """
    macro_service = MarketMacroService()
    return macro_service.get_correlations()

@router.get("/relative-strength/{ticker}")
def get_relative_strength(ticker: str, current_user: User = Depends(get_current_user)):
    """
    Get RS Rating and Alpha Flag for a specific ticker.
    """
    finance_service = FinanceService()
    return finance_service.get_relative_strength(ticker)
