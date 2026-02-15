from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import httpx
import numpy as np
from sklearn.linear_model import LinearRegression

# Load env
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

# Alpha Vantage API key
ALPHA_VANTAGE_KEY = os.environ.get("ALPHA_VANTAGE_KEY", "")

# Setup app
app = FastAPI()
api_router = APIRouter(prefix="/api")

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------- Models --------------------

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

# -------------------- Helpers --------------------

def safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(str(value).replace("%", "").strip())
    except:
        return default

def safe_int(value, default=0):
    try:
        if value is None:
            return default
        return int(float(value))
    except:
        return default

# -------------------- Alpha Vantage --------------------

async def fetch_stock_data(symbol: str) -> dict:
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": symbol,
        "apikey": ALPHA_VANTAGE_KEY,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(url, params=params)
        data = r.json()

    logger.info(f"AlphaVantage GLOBAL_QUOTE response for {symbol}: {data}")

    if "Note" in data:
        raise HTTPException(status_code=429, detail="Alpha Vantage rate limit reached")

    if "Global Quote" not in data or not data["Global Quote"]:
        raise HTTPException(status_code=404, detail=f"Stock symbol '{symbol}' not found")

    quote = data["Global Quote"]

    return {
        "symbol": quote.get("01. symbol", symbol),
        "price": safe_float(quote.get("05. price")),
        "change": safe_float(quote.get("09. change")),
        "change_percent": safe_float(quote.get("10. change percent")),
        "volume": safe_int(quote.get("06. volume")),
        "timestamp": quote.get("07. latest trading day", ""),
    }

async def fetch_time_series(symbol: str) -> List[dict]:
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "outputsize": "compact",
        "apikey": ALPHA_VANTAGE_KEY,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(url, params=params)
        data = r.json()

    logger.info(f"AlphaVantage TIME_SERIES response for {symbol}: keys={list(data.keys())}")

    if "Note" in data:
        raise HTTPException(status_code=429, detail="Alpha Vantage rate limit reached")

    if "Time Series (Daily)" not in data:
        raise HTTPException(status_code=404, detail="Failed to fetch historical data")

    ts = data["Time Series (Daily)"]

    result = []
    for date, values in list(ts.items())[:60]:
        result.append({
            "date": date,
            "close": safe_float(values.get("4. close")),
            "volume": safe_int(values.get("5. volume")),
        })

    return sorted(result, key=lambda x: x["date"])

# -------------------- Indicators & Prediction --------------------

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

def predict_next_price(prices: List[float]) -> dict:
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
        "trend": trend,
    }

# -------------------- Routes --------------------

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
    current_price = prices[-1]

    p = predict_next_price(prices)

    return StockPrediction(
        symbol=symbol.upper(),
        current_price=current_price,
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

# -------------------- App Setup --------------------

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
