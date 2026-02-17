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

# Helper: fetch historical data from Yahoo Finance CSV
def fetch_yahoo(symbol: str) -> pd.DataFrame:
    symbol = symbol.upper()

    period2 = int(time.time())
    period1 = period2 - 60 * 60 * 24 * 365 * 2  # last 2 years

    url = (
        f"https://query1.finance.yahoo.com/v7/finance/download/{symbol}"
        f"?period1={period1}&period2={period2}&interval=1d&events=history&includeAdjustedClose=true"
    )

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

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
        "date": str(latest["Date"]),
        "close": float(latest["Close"]),
        "open": float(latest["Open"]),
        "high": float(latest["High"]),
        "low": float(latest["Low"]),
        "prev_close": float(prev["Close"]),
    }

@app.get("/api/stocks/{symbol}/chart")
def get_chart(symbol: str):
    df = fetch_yahoo(symbol)
    df = df.tail(100)

    data = []
    for _, row in df.iterrows():
        data.append({
            "date": str(row["Date"]),
            "close": float(row["Close"])
        })

    return {
        "symbol": symbol.upper(),
        "data": data
    }

@app.get("/api/stocks/{symbol}/predict")
def predict(symbol: str):
    df = fetch_yahoo(symbol)

    last_close = float(df.iloc[-1]["Close"])

    # Simple demo prediction (+1%)
    predicted = last_close * 1.01

    return {
        "symbol": symbol.upper(),
        "last_close": last_close,
        "predicted_price": round(predicted, 2),
        "note": "Demo prediction using simple heuristic"
    }

@app.get("/api/stocks/{symbol}/indicators")
def indicators(symbol: str):
    df = fetch_yahoo(symbol)

    df["SMA_5"] = df["Close"].rolling(window=5).mean()
    df["SMA_10"] = df["Close"].rolling(window=10).mean()

    latest = df.iloc[-1]

    return {
        "symbol": symbol.upper(),
        "sma_5": None if pd.isna(latest["SMA_5"]) else round(float(latest["SMA_5"]), 2),
        "sma_10": None if pd.isna(latest["SMA_10"]) else round(float(latest["SMA_10"]), 2),
    }


# =========================
# DEMO / MOCK ENDPOINTS
# =========================

@app.get("/api/stocks/demo")
def demo_stock():
    return {
        "symbol": "AAPL",
        "price": 192.34,
        "change": "+1.24",
        "volume": 52341234,
        "currency": "USD",
        "exchange": "NASDAQ"
    }

@app.get("/api/predict/demo")
def demo_predict():
    return {
        "symbol": "AAPL",
        "predicted_price": 198.50,
        "confidence": 0.87,
        "model": "LSTM"
    }

@app.get("/api/indicators/demo")
def demo_indicators():
    return {
        "symbol": "AAPL",
        "RSI": 61.2,
        "SMA": 189.4,
        "EMA": 191.1,
        "volatility": 1.34
    }
