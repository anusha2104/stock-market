import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ALPHA_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

@app.get("/")
def root():
    return {"message": "Stock Market Analyzer API is running"}

# =========================
# REAL DATA USING ALPHA VANTAGE
# =========================

def fetch_alpha(symbol: str):
    if not ALPHA_KEY:
        raise HTTPException(status_code=500, detail="Alpha Vantage API key not configured")

    url = "https://www.alphavantage.co/query"
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "apikey": ALPHA_KEY,
        "outputsize": "compact"
    }

    r = requests.get(url, params=params, timeout=15)
    data = r.json()

    if "Time Series (Daily)" not in data:
        raise HTTPException(status_code=404, detail="Stock data not found or API limit reached")

    return data["Time Series (Daily)"]

@app.get("/api/stocks/{symbol}")
def get_stock(symbol: str):
    ts = fetch_alpha(symbol.upper())
    dates = list(ts.keys())

    latest = ts[dates[0]]
    prev = ts[dates[1]]

    price = float(latest["4. close"])
    prev_close = float(prev["4. close"])
    change = price - prev_close
    change_percent = (change / prev_close) * 100

    return {
        "symbol": symbol.upper(),
        "price": price,
        "change": round(change, 2),
        "change_percent": round(change_percent, 2),
        "volume": int(latest["5. volume"]),
        "timestamp": dates[0]
    }

@app.get("/api/stocks/{symbol}/chart")
def get_chart(symbol: str):
    ts = fetch_alpha(symbol.upper())
    dates = list(ts.keys())[:60]
    dates.reverse()

    data = []
    for d in dates:
        data.append({
            "date": d,
            "close": float(ts[d]["4. close"])
        })

    return {
        "symbol": symbol.upper(),
        "data": data
    }

# =========================
# DEMO / MOCK ENDPOINTS
# =========================

@app.get("/api/stocks/demo")
def demo_stock():
    return {
        "symbol": "AAPL",
        "price": 192.34,
        "change": 1.24,
        "change_percent": 0.65,
        "volume": 52341234,
        "timestamp": "2026-02-17"
    }

@app.get("/api/stocks/demo/chart")
def demo_chart():
    data = []
    base = 180
    for i in range(30):
        data.append({
            "date": f"2026-01-{i+1:02d}",
            "close": round(base + i * 0.5, 2)
        })
    return {"symbol": "AAPL", "data": data}

@app.get("/api/predict/demo")
def demo_predict():
    return {
        "symbol": "AAPL",
        "predicted_price": 198.50,
        "trend": "bullish",
        "confidence": "high"
    }

@app.get("/api/stocks/demo/indicators")
def demo_indicators():
    return {
        "sma_20": 189.4,
        "sma_50": 185.2,
        "ema_12": 191.1,
        "ema_26": 188.7,
        "rsi": 61.2
    }
