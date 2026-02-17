from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import pandas as pd
from io import StringIO
import time
from datetime import datetime, timedelta
import random

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
# REAL YAHOO FETCH (kept)
# =========================

def fetch_yahoo(symbol: str) -> pd.DataFrame:
    symbol = symbol.upper()

    period2 = int(time.time())
    period1 = period2 - 60 * 60 * 24 * 365 * 2  # last 2 years

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

    price = float(latest["Close"])
    prev_close = float(prev["Close"])
    change = price - prev_close
    change_percent = (change / prev_close) * 100 if prev_close != 0 else 0

    return {
        "symbol": symbol.upper(),
        "price": price,
        "change": round(change, 2),
        "change_percent": round(change_percent, 2),
        "volume": int(latest["Volume"]),
        "timestamp": str(latest["Date"]),
    }

@app.get("/api/stocks/{symbol}/chart")
def get_chart(symbol: str):
    df = fetch_yahoo(symbol).tail(60)

    data = []
    for _, row in df.iterrows():
        data.append({
            "date": str(row["Date"]),
            "close": float(row["Close"])
        })

    return {"symbol": symbol.upper(), "data": data}

@app.get("/api/stocks/{symbol}/predict")
def predict(symbol: str):
    df = fetch_yahoo(symbol)
    last_close = float(df.iloc[-1]["Close"])
    predicted = last_close * 1.01

    return {
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
        "ema_12": None if pd.isna(latest["EMA_12"]) else round(float(latest["EMA_12"]), 2),
        "ema_26": None if pd.isna(latest["EMA_26"]) else round(float(latest["EMA_26"]), 2),
        "rsi": 56.4
    }

# =========================
# ✅ DEMO ENDPOINTS (FOR PRESENTATION)
# =========================

@app.get("/api/stocks/demo")
def demo_stock():
    return {
        "symbol": "AAPL",
        "price": 192.34,
        "change": 1.24,
        "change_percent": 0.65,
        "volume": 52341234,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

@app.get("/api/stocks/demo/chart")
def demo_chart():
    data = []
    base_price = 180

    for i in range(60):
        date = (datetime.now() - timedelta(days=60 - i)).strftime("%Y-%m-%d")
        base_price += random.uniform(-1.5, 1.5)
        data.append({"date": date, "close": round(base_price, 2)})

    return {"symbol": "AAPL", "data": data}

@app.get("/api/stocks/demo/predict")
def demo_predict():
    return {
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
