from fastapi import FastAPI, APIRouter, HTTPException
from starlette.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import logging
from pathlib import Path
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import httpx
import numpy as np
from sklearn.linear_model import LinearRegression

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

ALPHA_VANTAGE_KEY = os.environ.get("ALPHA_VANTAGE_KEY", "")

app = FastAPI()
api_router = APIRouter(prefix="/api")

# ---------- Models ----------

class StockData(BaseModel):
    symbol: str
    price: float
    change: float
    change_percent: float
    volume: int
    timestamp: str

class StockPrediction(BaseModel):
    symbol: str
    current_price: float
    predicted_price: float
    confidence: str
    trend: str

class TechnicalIndicators(BaseModel):
    symbol: str
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    ema_12: Optional[float] = None
    ema_26: Optional[float] = None
    rsi: Optional[float] = None

# ---------- Helpers ----------

def safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(str(value).replace("%", ""))
    except:
        return default

def safe_int(value, default=0):
    try:
        if value is None:
            return default
        return int(value)
    except:
        return default

# ---------- Alpha Vantage ----------

async def fetch_stock_data(symbol: str) -> dict:
    async with httpx.AsyncClient(timeout=15.0) as client:
        url = (
            "https://www.alphavantage.co/query"
            f"?function=GLOBAL_QUOTE&symbol={symbol}&apikey={ALPHA_VANTAGE_KEY}"
        )
        r = await client.get(url)
        data = r.json()

        # Rate limit case
        if "Note" in data:
            raise HTTPException(status_code=429, detail="Alpha Vantage rate limit reached. Try again in a minute.")

        quote = data.get("Global Quote", {})

        if not quote or "05. price" not in quote:
            raise HTTPException(status_code=502, detail="Failed to fetch stock data from Alpha Vantage")

        return {
            "symbol": quote.get("01. symbol", symbol),
            "price": safe_float(quote.get("05. price")),
            "change": safe_float(quote.get("09. change")),
            "change_percent": safe_float(quote.get("10. change percent")),
            "volume": safe_int(quote.get("06. volume")),
            "timestamp": quote.get("07. latest trading day", ""),
        }

async def fetch_time_series(symbol: str) -> List[dict]:
    async with httpx.AsyncClient(timeout=15.0) as client:
        url = (
            "https://www.alphavantage.co/query"
            f"?function=TIME_SERIES_DAILY&symbol={symbol}&outputsize=compact&apikey={ALPHA_VANTAGE_KEY}"
        )
        r = await client.get(url)
        data = r.json()

        if "Note" in data:
            raise HTTPException(status_code=429, detail="Alpha Vantage rate limit reached. Try again later.")

        series = data.get("Time Series (Daily)")
        if not series:
            raise HTTPException(status_code=502, detail="Failed to fetch historical data")

        result = []
        for date, values in list(series.items())[:60]:
            result.append({
                "date": date,
                "close": safe_float(values.get("4. close")),
                "volume": safe_int(values.get("5. volume")),
            })

        return sorted(result, key=lambda x: x["date"])

# ---------- Indicators & Prediction ----------

def calculate_sma(prices: List[float], period: int):
    if len(prices) < period:
        return None
    return sum(prices[-period:]) / period

def calculate_ema(prices: List[float], period: int):
    if len(prices) < period:
        return None
    multiplier = 2 / (period + 1)
    ema = sum(prices[:period]) / period
    for price in prices[period:]:
        ema = (price - ema) * multiplier + ema
    return ema

def calculate_rsi(prices: List[float], period: int = 14):
    if len(prices) < period + 1:
        return None
    gains, losses = [], []
    for i in range(1, len(prices)):
        diff = prices[i] - prices[i - 1]
        gains.append(max(diff, 0))
        losses.append(abs(min(diff, 0)))
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def predict_next_price(prices: List[float]):
    if len(prices) < 10:
        return {"predicted_price": prices[-1], "confidence": "low", "trend": "neutral"}

    X = np.arange(len(prices)).reshape(-1, 1)
    y = np.array(prices)

    model = LinearRegression()
    model.fit(X, y)

    next_price = model.predict([[len(prices)]])[0]

    recent = (prices[-1] - prices[-5]) / prices[-5] * 100 if len(prices) >= 5 else 0

    if recent > 1:
        trend, confidence = "bullish", "medium"
    elif recent < -1:
        trend, confidence = "bearish", "medium"
    else:
        trend, confidence = "neutral", "low"

    return {"predicted_price": float(next_price), "confidence": confidence, "trend": trend}

# ---------- Routes ----------

@api_router.get("/")
async def root():
    return {"message": "Stock Market Analyzer API"}

@api_router.get("/stocks/{symbol}", response_model=StockData)
async def get_stock(symbol: str):
    data = await fetch_stock_data(symbol.upper())
    return StockData(**data)

@api_router.get("/stocks/{symbol}/chart")
async def get_chart(symbol: str):
    data = await fetch_time_series(symbol.upper())
    return {"symbol": symbol.upper(), "data": data}

@api_router.get("/stocks/{symbol}/predict", response_model=StockPrediction)
async def predict(symbol: str):
    series = await fetch_time_series(symbol.upper())
    prices = [x["close"] for x in series]
    current = prices[-1]
    p = predict_next_price(prices)
    return StockPrediction(
        symbol=symbol.upper(),
        current_price=current,
        predicted_price=p["predicted_price"],
        confidence=p["confidence"],
        trend=p["trend"],
    )

@api_router.get("/stocks/{symbol}/indicators", response_model=TechnicalIndicators)
async def indicators(symbol: str):
    series = await fetch_time_series(symbol.upper())
    prices = [x["close"] for x in series]

    return TechnicalIndicators(
        symbol=symbol.upper(),
        sma_20=calculate_sma(prices, 20),
        sma_50=calculate_sma(prices, 50),
        ema_12=calculate_ema(prices, 12),
        ema_26=calculate_ema(prices, 26),
        rsi=calculate_rsi(prices, 14),
    )

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
