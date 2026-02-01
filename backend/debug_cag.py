import yfinance as yf
import pandas as pd

def debug_cag():
    ticker = "CAG"
    stock = yf.Ticker(ticker)
    hist = stock.history(period="6mo")
    print(f"Hist empty: {hist.empty}")
    if not hist.empty:
        print(f"First 5 rows:\n{hist.head()}")
        print(f"Last 5 rows:\n{hist.tail()}")
        stock_ret = (hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0]
        print(f"Stock Ret: {stock_ret}")

if __name__ == "__main__":
    debug_cag()
