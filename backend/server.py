from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import pandas as pd
from io import StringIO

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

# Helper: fetch data from Stooq
def fetch_stooq(symbol: str) -> pd.DataFrame:
    sym = symbol.lower()
    if not sym.endswith(".us"):
        sym = sym + ".us"

    url = f"https://stooq.pl/q/d/l/?s={sym}&i=d"
    r = requests.get(url, timeout=10)

    if r.status_code != 200 or len(r.text) < 50:
        raise HTTPException(status_code=404, detail="Stock symbol not found")

    df = pd.read_csv(StringIO(r.text))

    if df.empty or "Close" not in df.columns:
        raise HTTPException(status_code=404, detail="Stock symbol not found")

    return df

@app.get("/api/stocks/{symbol}")
def get_stock(symbol: str):
    df = fetch_stooq(symbol)

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
    df = fetch_stooq(symbol)

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
    df = fetch_stooq(symbol)

    last_close = float(df.iloc[-1]["Close"])

    # Dummy prediction: +1% (for demo/viva)
    predicted = last_close * 1.01

    return {
        "symbol": symbol.upper(),
        "last_close": last_close,
        "predicted_price": round(predicted, 2),
        "note": "This is a demo prediction based on simple heuristic"
    }

@app.get("/api/stocks/{symbol}/indicators")
def indicators(symbol: str):
    df = fetch_stooq(symbol)

    df["SMA_5"] = df["Close"].rolling(window=5).mean()
    df["SMA_10"] = df["Close"].rolling(window=10).mean()

    latest = df.iloc[-1]

    return {
        "symbol": symbol.upper(),
        "sma_5": None if pd.isna(latest["SMA_5"]) else round(float(latest["SMA_5"]), 2),
        "sma_10": None if pd.isna(latest["SMA_10"]) else round(float(latest["SMA_10"]), 2),
    }
