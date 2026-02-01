import numpy as np
import yfinance as yf
from typing import Dict, List
from utils.cache import ttl_cache
from utils.rate_limiter import yahoo_rate_limiter

class RiskService:
    """
    Institutional Risk Management Service:
    - Monte Carlo Simulation for Trade Probability
    - Position Sizing (R-Manager)
    """

    def calculate_position_size(self, equity: float, risk_pct: float, entry: float, stop_loss: float) -> Dict:
        """
        R-Manager: Calculates how many shares to buy to risk only X% of total equity.
        """
        if entry <= stop_loss:
            return {"error": "Entry must be higher than Stop Loss for a BUY setup."}
            
        risk_amount = equity * (risk_pct / 100)
        risk_per_share = entry - stop_loss
        
        num_shares = int(risk_amount / risk_per_share)
        total_cost = num_shares * entry
        
        return {
            "num_shares": num_shares,
            "risk_amount": round(risk_amount, 2),
            "total_investment": round(total_cost, 2),
            "position_size_pct": round((total_cost / equity) * 100, 2)
        }

    @ttl_cache(ttl=43200)
    def run_monte_carlo(self, ticker: str, entry: float, stop_loss: float, target: float, days: int = 20, iterations: int = 10000) -> Dict:
        """
        Runs a Monte Carlo simulation (GBM) to estimate the probability of hitting 
        the target vs the stop loss within a specific timeframe (default 4 weeks / 20 days).
        """
        try:
            yahoo_rate_limiter.wait_if_needed()
            stock = yf.Ticker(ticker)
            # Use 6 months of daily data to estimate volatility
            hist = stock.history(period="6mo")
            if hist.empty or len(hist) < 20: 
                return {"error": "Insufficient data"}

            returns = hist['Close'].pct_change().dropna()
            
            # Estimate parameters (Daily)
            mu = returns.mean()
            sigma = returns.std()
            
            # Simulation using Vectorized GBM
            # Price_t = Price_0 * exp((mu - 0.5 * sigma^2) * t + sigma * epsilon * sqrt(t))
            
            # Create a matrix of random daily shocks
            dt = 1
            z = np.random.standard_normal((iterations, days))
            
            # Calculate daily price paths
            daily_returns = np.exp((mu - 0.5 * sigma**2) * dt + sigma * z * np.sqrt(dt))
            
            # Cumulative product across days for each iteration
            price_paths = entry * np.cumprod(daily_returns, axis=1)
            
            # Analyze results
            hits_stop = np.any(price_paths <= stop_loss, axis=1).sum()
            hits_target = np.any(price_paths >= target, axis=1).sum()
            
            prob_stop = (hits_stop / iterations) * 100
            prob_target = (hits_target / iterations) * 100
            
            # Expected Value (Final Day)
            final_prices = price_paths[:, -1]
            expected_price = np.mean(final_prices)

            return {
                "ticker": ticker,
                "iterations": iterations,
                "horizon_days": days,
                "prob_target_hit": round(prob_target, 2),
                "prob_stop_hit": round(prob_stop, 2),
                "expected_price_20d": round(expected_price, 2),
                "risk_reward_ratio": round((target - entry) / (entry - stop_loss), 2)
            }
            
        except Exception as e:
            print(f"Monte Carlo failed for {ticker}: {e}")
            return {"error": str(e)}
