from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
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

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

# MongoDB connection (optional, only used for /contact)
mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
db_name = os.environ.get("DB_NAME", "test")
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

# Alpha Vantage API key
ALPHA_VANTAGE_KEY = os.environ.get("ALPHA_VANTAGE_KEY", "")

# Create app
app = FastAPI()
api_router = APIRouter(prefix="/api")

# ------------------------
# Helpers
# ------------------------

def safe_float(value, default=0.0):
    try:
        if value is None or value == "":
            return default
        return float(str(value).replace("%", ""))
    except:
        return default

def safe_int(value, default=0):
    try:
        if value is None or value == "":
            return default
        return int(value)
    except:
        return default

# ------------------------
# Models
# ------------------------

class ContactMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: EmailStr
    message: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ContactMessageCreate(BaseModel):
    name: str
    email: EmailStr
    message: str

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

# ------------------------
# Alpha Vantage Services
# ------------------------

async def fetch_stock_data(symbol: str) -> dict:
    async with httpx.AsyncClient(timeout=10.0) as client:
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={ALPHA_VANTAGE_KEY}"
        response = await client.get(url)
        data = response.json()

        if "Note" in data:
            raise HTTPException(status_code=429, detail="API rate limit reached. Try again later.")

        if "Error Message" in data:
            raise HTTPException(status_code=404, detail=f"Stock symbol '{symbol}' not found")

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
    async with httpx.AsyncClient(timeout=10.0) as client:
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&outputsize=compact&apikey={ALPHA_VANTAGE_KEY}"
        response = await client.get(url)
        data = response.json()

        if "Note" in data:
            raise HTTPException(status_code=429, detail="API rate limit reached. Try again later.")

        if "Error Message" in data:
            raise HTTPException(status_code=404, detail=f"Stock symbol '{symbol}' not found")

        if "Time Series (Daily)" not in data:
            return []

        time_series = data["Time Series (Daily)"]
        result = []

        for date, values in list(time_series.items())[:60]:
            result.append({
                "date": date,
                "close": safe_float(values.get("4. close")),
                "volume": safe_int(values.get("5. volume")),
            })

        return sorted(result, key=lambda x: x["date"])

# ------------------------
# Indicators & Prediction
# ------------------------

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
        change = prices[i] - prices[i - 1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))
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
    predicted_price = model.predict(next_day)[0]

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
        "predicted_price": float(predicted_price),
        "confidence": confidence,
        "trend": trend,
    }

# ------------------------
# API Routes
# ------------------------

@api_router.get("/")
async def root():
    return {"message": "Stock Market Analyzer API"}

@api_router.get("/stocks/{symbol}", response_model=StockData)
async def get_stock_data(symbol: str):
    try:
        data = await fetch_stock_data(symbol.upper())
        return StockData(**data)
    except HTTPException:
        raise
    except Exception as e:
        print("Error in /stocks:", e)
        raise HTTPException(status_code=500, detail="Internal server error")

@api_router.get("/stocks/{symbol}/chart")
async def get_stock_chart(symbol: str):
    data = await fetch_time_series(symbol.upper())
    return {"symbol": symbol.upper(), "data": data}

@api_router.get("/stocks/{symbol}/predict", response_model=StockPrediction)
async def predict_stock_price(symbol: str):
    time_series = await fetch_time_series(symbol.upper())
    if not time_series:
        raise HTTPException(status_code=404, detail="Insufficient data for prediction")

    prices = [item["close"] for item in time_series]
    current_price = prices[-1]
    prediction = predict_next_price(prices)

    return StockPrediction(
        symbol=symbol.upper(),
        current_price=current_price,
        predicted_price=prediction["predicted_price"],
        confidence=prediction["confidence"],
        trend=prediction["trend"],
    )

@api_router.get("/stocks/{symbol}/indicators", response_model=TechnicalIndicators)
async def get_technical_indicators(symbol: str):
    time_series = await fetch_time_series(symbol.upper())
    if not time_series:
        raise HTTPException(status_code=404, detail="Insufficient data for indicators")

    prices = [item["close"] for item in time_series]

    return TechnicalIndicators(
        symbol=symbol.upper(),
        sma_20=calculate_sma(prices, 20),
        sma_50=calculate_sma(prices, 50),
        ema_12=calculate_ema(prices, 12),
        ema_26=calculate_ema(prices, 26),
        rsi=calculate_rsi(prices, 14),
    )

@api_router.post("/contact", response_model=ContactMessage)
async def create_contact_message(input: ContactMessageCreate):
    contact_obj = ContactMessage(**input.model_dump())
    doc = contact_obj.model_dump()
    doc["timestamp"] = doc["timestamp"].isoformat()
    await db.contact_messages.insert_one(doc)
    return contact_obj

# ------------------------
# App setup
# ------------------------

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
