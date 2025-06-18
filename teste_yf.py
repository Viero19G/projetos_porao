import yfinance as yf


data = yf.download("PETR4.SA", start='2025-01-01', end='2025-05-31')

print(data)