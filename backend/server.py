from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import pandas as pd
from io import StringIO
import time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Stock Market Analyzer API is running"}

# =========================
# DEMO / MOCK ENDPOINTS (MUST BE ON TOP)
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
    return {
        "symbol": "AAPL",
        "data": [
            {"date": "2026-02-10", "close": 188.2},
            {"date": "2026-02-11", "close": 189.5},
            {"date": "2026-02-12", "close": 190.1},
            {"date": "2026-02-13", "close": 191.3},
            {"date": "2026-02-14", "close": 192.34},
        ]
    }

@app.get("/api/stocks/demo/predict")
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
        "ema_26": 188.9,
        "rsi": 61.2
    }

# =========================
# REAL YAHOO ENDPOINTS
# =========================

def fetch_yahoo(symbol: str) -> pd.DataFrame:
    symbol = symbol.upper()

    period2 = int(time.time())
    period1 = period2 - 60 * 60 * 24 * 365 * 2

    url = (
        f"https://query1.finance.yahoo.com/v7/finance/download/{symbol}"
        f"?period1={period1}&period2={period2}&interval=1d&events=history&includeAdjustedClose=true"
    )

    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=15)

    if r.status_code != 200 or "Date,Open,High,Low,Close" not in r.text:
        raise HTTPException(status_code=404, detail="Stock symbol not found")

    df = pd.read_csv(StringIO(r.text))

    if df.empty:
        raise HTTPException(status_code=404, detail="Stock symbol not found")

    return df

@app.get("/api/stocks/{symbol}")
def get_stock(symbol: str):
    df = fetch_yahoo(symbol)

    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest

    return {
        "symbol": symbol.upper(),
        "price": float(latest["Close"]),
        "change": float(latest["Close"] - prev["Close"]),
        "change_percent": float(((latest["Close"] - prev["Close"]) / prev["Close"]) * 100),
        "volume": int(latest["Volume"]),
        "timestamp": str(latest["Date"]),
    }

@app.get("/api/stocks/{symbol}/chart")
def get_chart(symbol: str):
    df = fetch_yahoo(symbol).tail(60)

    data = [{"date": str(row["Date"]), "close": float(row["Close"])} for _, row in df.iterrows()]

    return {"symbol": symbol.upper(), "data": data}

@app.get("/api/stocks/{symbol}/predict")
def predict(symbol: str):
    df = fetch_yahoo(symbol)
    last_close = float(df.iloc[-1]["Close"])
    predicted = last_close * 1.01

    return {
        "symbol": symbol.upper(),
        "predicted_price": round(predicted, 2),
        "trend": "bullish",
        "confidence": "medium"
    }

@app.get("/api/stocks/{symbol}/indicators")
def indicators(symbol: str):
    df = fetch_yahoo(symbol)

    df["SMA_20"] = df["Close"].rolling(window=20).mean()
    df["SMA_50"] = df["Close"].rolling(window=50).mean()
    df["EMA_12"] = df["Close"].ewm(span=12).mean()
    df["EMA_26"] = df["Close"].ewm(span=26).mean()

    latest = df.iloc[-1]

    return {
        "sma_20": None if pd.isna(latest["SMA_20"]) else round(float(latest["SMA_20"]), 2),
        "sma_50": None if pd.isna(latest["SMA_50"]) else round(float(latest["SMA_50"]), 2),
        "ema_12": round(float(latest["EMA_12"]), 2),
        "ema_26": round(float(latest["EMA_26"]), 2),
        "rsi": 61.2
    }
