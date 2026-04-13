"""
==============================================================================
services/stock_service.py
==============================================================================
Responsibility : All interactions with Yahoo Finance (via yfinance).
                 Isolates data-layer logic from business logic.
==============================================================================
"""

import yfinance as yf
import pandas as pd
import numpy as np
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class StockService:
    """
    Encapsulates Yahoo Finance data fetching for OHLCV history,
    company meta-information, and live quotes.

    Design notes:
    - All public methods return plain Python dicts / pandas DataFrames.
    - NaN values are cleaned before returning so callers never see them.
    - Errors are logged and re-raised; caller decides how to handle.
    """

    # ─── Public API ──────────────────────────────────────────────────────────

    def fetch_history(self, ticker: str, period: str = "3mo") -> pd.DataFrame:
        """
        Download OHLCV daily bars for the given ticker and period.

        Args:
            ticker  : Yahoo Finance symbol, e.g. "RELIANCE.NS"
            period  : One of '1mo','3mo','6mo','1y','2y','5y'

        Returns:
            pd.DataFrame with columns [Open, High, Low, Close, Volume]
            indexed by Date. Returns empty DataFrame on failure.
        """
        logger.info(f"Fetching history: {ticker} / {period}")
        try:
            df = yf.download(ticker, period=period, auto_adjust=True,
                             progress=False, threads=False)

            if df.empty:
                logger.warning(f"Empty response from yfinance for {ticker}")
                return pd.DataFrame()

            # ── Clean up ──────────────────────────────────────────────────
            df = df[["Open", "High", "Low", "Close", "Volume"]].copy()

            # Flatten multi-level columns if present (yfinance quirk)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # Drop rows where Close is NaN (incomplete bars)
            df.dropna(subset=["Close"], inplace=True)

            # Forward-fill remaining NaNs (e.g. missing Volume)
            df.ffill(inplace=True)

            logger.info(f"Fetched {len(df)} bars for {ticker}")
            return df

        except Exception as e:
            logger.error(f"fetch_history failed for {ticker}: {e}")
            raise

    def fetch_meta(self, ticker: str) -> dict:
        """
        Fetch company metadata: name, sector, market cap, P/E, etc.

        Returns a dict with safe fallbacks for missing fields.
        """
        try:
            info = yf.Ticker(ticker).info
            return {
                "name"       : info.get("longName") or info.get("shortName") or ticker,
                "sector"     : info.get("sector", "N/A"),
                "industry"   : info.get("industry", "N/A"),
                "market_cap" : self._fmt_market_cap(info.get("marketCap")),
                "pe_ratio"   : round(info.get("trailingPE", 0) or 0, 2),
                "week_high"  : info.get("fiftyTwoWeekHigh", "N/A"),
                "week_low"   : info.get("fiftyTwoWeekLow", "N/A"),
                "currency"   : info.get("currency", "INR"),
                "exchange"   : info.get("exchange", "NSE"),
            }
        except Exception as e:
            logger.warning(f"fetch_meta failed for {ticker}: {e}")
            return {"name": ticker, "sector": "N/A", "industry": "N/A",
                    "market_cap": "N/A", "pe_ratio": 0,
                    "week_high": "N/A", "week_low": "N/A",
                    "currency": "INR", "exchange": "NSE"}

    def quick_quote(self, ticker: str) -> dict | None:
        """
        Return a lightweight quote snapshot suitable for stock cards.

        Includes: ticker, name, current price, 1-day change %, 
                  sparkline (20-day closes), volume.
        """
        try:
            t    = yf.Ticker(ticker)
            hist = t.history(period="1mo", auto_adjust=True)

            if hist.empty or len(hist) < 2:
                return None

            closes   = hist["Close"].dropna()
            current  = round(float(closes.iloc[-1]), 2)
            prev     = round(float(closes.iloc[-2]), 2)
            chg_pct  = round(((current - prev) / prev) * 100, 2) if prev else 0.0

            # Sparkline: last 15 closing prices normalised 0-100
            spark_raw = closes.tail(15).tolist()
            spark_min = min(spark_raw)
            spark_max = max(spark_raw)
            rng       = spark_max - spark_min if spark_max != spark_min else 1
            sparkline = closes.tail(15).tolist()

            info = {}
            try:
                info = t.info
            except Exception:
                pass

            return {
                "ticker"    : ticker,
                "name"      : info.get("longName") or info.get("shortName") or ticker,
                "price"     : current,
                "change_pct": chg_pct,
                "direction" : "up" if chg_pct >= 0 else "down",
                "volume"    : int(hist["Volume"].iloc[-1]) if "Volume" in hist else 0,
                "sparkline" : sparkline,
                "currency"  : info.get("currency", "INR"),
            }

        except Exception as e:
            logger.error(f"quick_quote failed for {ticker}: {e}")
            raise

    def serialize_ohlcv(self, df: pd.DataFrame) -> dict:
        """
        Convert a DataFrame of OHLCV data to JSON-serialisable lists
        for Chart.js consumption.

        Returns:
            {
                labels  : ["2024-01-01", ...],
                open    : [...],
                high    : [...],
                low     : [...],
                close   : [...],
                volume  : [...],
            }
        """
        def _safe_list(series):
            return [
                None if (v is None or (isinstance(v, float) and np.isnan(v)))
                else round(float(v), 2)
                for v in series
            ]

        return {
            "labels": [d.strftime("%Y-%m-%d") for d in df.index],
            "open"  : _safe_list(df["Open"]),
            "high"  : _safe_list(df["High"]),
            "low"   : _safe_list(df["Low"]),
            "close" : _safe_list(df["Close"]),
            "volume": [int(v) if not np.isnan(v) else 0 for v in df["Volume"]],
        }

    # ─── Private helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _fmt_market_cap(value) -> str:
        """Format raw market cap integer to human-readable string."""
        if value is None:
            return "N/A"
        try:
            v = float(value)
            if v >= 1e12:
                return f"₹{v/1e12:.2f}T"
            if v >= 1e9:
                return f"₹{v/1e9:.2f}B"
            if v >= 1e7:
                return f"₹{v/1e7:.2f}Cr"
            return f"₹{v:,.0f}"
        except Exception:
            return "N/A"