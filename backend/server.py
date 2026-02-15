from fastapi import FastAPI, HTTPException
import pandas as pd

app = FastAPI(title="Stock Market Analyzer API")

@app.get("/")
def root():
    return {"message": "Stock Market Analyzer API is running"}

def fetch_stooq_csv(symbol: str) -> pd.DataFrame:
    symbol = symbol.lower()
    if "." not in symbol:
        symbol = symbol + ".us"  # Auto-fix: AAPL -> aapl.us

    url = f"https://stooq.pl/q/d/l/?s={symbol}&i=d"

    try:
        df = pd.read_csv(url)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch data from Stooq")

    if df.empty or "Date" not in df.columns:
        raise HTTPException(status_code=404, detail="Stock symbol not found")

    return df, symbol

@app.get("/api/stocks/{symbol}")
def get_stock(symbol: str):
    df, fixed_symbol = fetch_stooq_csv(symbol)

    latest = df.iloc[-1]

    return {
        "symbol": fixed_symbol,
        "date": str(latest["Date"]),
        "open": float(latest["Open"]),
        "high": float(latest["High"]),
        "low": float(latest["Low"]),
        "close": float(latest["Close"]),
        "volume": int(latest["Volume"]),
    }

@app.get("/api/stocks/{symbol}/chart")
def get_stock_chart(symbol: str):
    df, fixed_symbol = fetch_stooq_csv(symbol)

    # Return last 100 days for chart
    df_tail = df.tail(100)

    data = []
    for _, row in df_tail.iterrows():
        data.append({
            "date": str(row["Date"]),
            "open": float(row["Open"]),
            "high": float(row["High"]),
            "low": float(row["Low"]),
            "close": float(row["Close"]),
            "volume": int(row["Volume"]),
        })

    return {
        "symbol": fixed_symbol,
        "points": data
    }

@app.get("/api/stocks/{symbol}/indicators")
def get_indicators(symbol: str):
    df, fixed_symbol = fetch_stooq_csv(symbol)

    # Simple indicators
    df["SMA_10"] = df["Close"].rolling(window=10).mean()
    df["SMA_20"] = df["Close"].rolling(window=20).mean()

    latest = df.iloc[-1]

    return {
        "symbol": fixed_symbol,
        "sma_10": None if pd.isna(latest["SMA_10"]) else float(latest["SMA_10"]),
        "sma_20": None if pd.isna(latest["SMA_20"]) else float(latest["SMA_20"]),
        "close": float(latest["Close"])
    }

@app.get("/api/stocks/{symbol}/predict")
def predict_stock(symbol: str):
    df, fixed_symbol = fetch_stooq_csv(symbol)

    # Super simple "prediction": use last close as next prediction (demo-safe)
    latest_close = float(df.iloc[-1]["Close"])

    return {
        "symbol": fixed_symbol,
        "predicted_price": latest_close,
        "note": "This is a demo prediction using last closing price"
    }
