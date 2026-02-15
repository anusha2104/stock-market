from fastapi import FastAPI, APIRouter, HTTPException
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import httpx
import numpy as np
from sklearn.linear_model import LinearRegression

# Create the main app
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# ------------------ Models ------------------

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

# ------------------ Yahoo Finance Helpers ------------------

async def fetch_stock_data(symbol: str) -> dict:
    url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbol}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(url)
        data = r.json()

    try:
        result = data["quoteResponse"]["result"][0]
    except:
        raise HTTPException(status_code=404, detail="Stock symbol not found")

    return {
        "symbol": symbol.upper(),
        "price": float(result.get("regularMarketPrice", 0)),
        "change": float(result.get("regularMarketChange", 0)),
        "change_percent": float(result.get("regularMarketChangePercent", 0)),
        "volume": int(result.get("regularMarketVolume", 0) or 0),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

async def fetch_time_series(symbol: str) -> List[dict]:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=3mo&interval=1d"
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(url)
        data = r.json()

    try:
        timestamps = data["chart"]["result"][0]["timestamp"]
        closes = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
        volumes = data["chart"]["result"][0]["indicators"]["quote"][0]["volume"]
    except:
        raise HTTPException(status_code=404, detail="Failed to fetch historical data")

    result = []
    for t, c, v in zip(timestamps, closes, volumes):
        if c is None:
            continue
        date = datetime.fromtimestamp(t).strftime("%Y-%m-%d")
        result.append({
            "date": date,
            "close": float(c),
            "volume": int(v or 0)
        })

    return result

# ------------------ Indicators & Prediction ------------------

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
        diff = prices[i] - prices[i-1]
        if diff > 0:
            gains.append(diff)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(diff))

    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def predict_next_price(prices: List[float]):
    if len(prices) < 10:
        return {"predicted_price": prices[-1], "confidence": "low", "trend": "neutral"}

    X = np.array(range(len(prices))).reshape(-1, 1)
    y = np.array(prices)

    model = LinearRegression()
    model.fit(X, y)

    next_day = np.array([[len(prices)]])
    predicted_price = float(model.predict(next_day)[0])

    recent_trend = (prices[-1] - prices[-5]) / prices[-5] * 100 if len(prices) >= 5 else 0

    if recent_trend > 1:
        trend = "bullish"
        confidence = "medium"
    elif recent_trend < -1:
        trend = "bearish"
        confidence = "medium"
    else:
        trend = "neutral"
        confidence = "low"

    return {
        "predicted_price": predicted_price,
        "confidence": confidence,
        "trend": trend
    }

# ------------------ API Routes ------------------

@api_router.get("/")
async def root():
    return {"message": "Stock Market Analyzer API"}

@api_router.get("/stocks/{symbol}", response_model=StockData)
async def get_stock_data(symbol: str):
    data = await fetch_stock_data(symbol.upper())
    return StockData(**data)

@api_router.get("/stocks/{symbol}/chart")
async def get_stock_chart(symbol: str):
    data = await fetch_time_series(symbol.upper())
    return {"symbol": symbol.upper(), "data": data}

@api_router.get("/stocks/{symbol}/predict", response_model=StockPrediction)
async def predict_stock_price(symbol: str):
    series = await fetch_time_series(symbol.upper())
    prices = [x["close"] for x in series]

    current_price = prices[-1]
    pred = predict_next_price(prices)

    return StockPrediction(
        symbol=symbol.upper(),
        current_price=current_price,
        predicted_price=pred["predicted_price"],
        confidence=pred["confidence"],
        trend=pred["trend"]
    )

@api_router.get("/stocks/{symbol}/indicators", response_model=TechnicalIndicators)
async def get_indicators(symbol: str):
    series = await fetch_time_series(symbol.upper())
    prices = [x["close"] for x in series]

    return TechnicalIndicators(
        symbol=symbol.upper(),
        sma_20=calculate_sma(prices, 20),
        sma_50=calculate_sma(prices, 50),
        ema_12=calculate_ema(prices, 12),
        ema_26=calculate_ema(prices, 26),
        rsi=calculate_rsi(prices, 14)
    )

# ------------------ App Setup ------------------

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
