"""
==============================================================================
AI-Based Stock Market Analyzer — Flask Backend Entry Point
==============================================================================
Author      : B.Tech Major Project Team
Version     : 2.0.0
Description : Production-grade REST API for stock data fetching, technical
              analysis, and AI-inspired price prediction for Indian & global
              equities. Designed with modular service architecture.
==============================================================================
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
import traceback

# Internal service modules
from services.stock_service import StockService
from services.indicator_service import IndicatorService
from services.prediction_service import PredictionService
from utils.validators import validate_ticker, validate_period
from utils.response_builder import success_response, error_response

# ─── Application Bootstrap ────────────────────────────────────────────────────

app = Flask(__name__)
CORS(app)
# ─── Logging Configuration ────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/app.log", mode="a")
    ]
)
logger = logging.getLogger(__name__)

# ─── Service Instantiation ────────────────────────────────────────────────────

stock_svc     = StockService()
indicator_svc = IndicatorService()
prediction_svc = PredictionService()


# ═══════════════════════════════════════════════════════════════════════════════
#  ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/api/health", methods=["GET"])
def health_check():
    """Liveness probe — used by deployment orchestration."""
    return jsonify({"status": "ok", "version": "2.0.0"}), 200


# ─── /api/predict ──────────────────────────────────────────────────────────────

@app.route("/api/predict", methods=["GET"])
def predict():
    """
    Full prediction pipeline for a single ticker.

    Query params:
        ticker (str)  : Stock symbol, e.g. RELIANCE.NS
        period (str)  : Historical window — '1mo' | '3mo' | '6mo' | '1y' (default: '3mo')

    Returns:
        JSON with current price, predicted price, trend, confidence,
        technical indicators, and OHLCV history for charting.
    """
    ticker = request.args.get("ticker", "").upper().strip()
    period = request.args.get("period", "3mo").strip()

    # ── Input validation ──────────────────────────────────────────────────────
    ticker_err = validate_ticker(ticker)
    if ticker_err:
        return error_response(ticker_err, 400)

    period_err = validate_period(period)
    if period_err:
        return error_response(period_err, 400)

    try:
        logger.info(f"[predict] ticker={ticker}, period={period}")

        # Step 1 — Fetch raw OHLCV data from Yahoo Finance
        raw_data = stock_svc.fetch_history(ticker, period)
        if raw_data is None or raw_data.empty:
            return error_response(f"No data found for ticker '{ticker}'. "
                                  "Ensure suffix (.NS/.BO) is correct.", 404)

        # Step 2 — Compute technical indicators
        indicators = indicator_svc.compute_all(raw_data)

        # Step 3 — Run prediction engine
        prediction = prediction_svc.predict(raw_data, indicators)

        # Step 4 — Fetch meta (company name, sector, market cap)
        meta = stock_svc.fetch_meta(ticker)

        # Step 5 — Serialize OHLCV for frontend chart
        chart_data = stock_svc.serialize_ohlcv(raw_data)

        payload = {
            "ticker"    : ticker,
            "meta"      : meta,
            "current"   : round(float(raw_data["Close"].iloc[-1]), 2),
            "predicted" : prediction["predicted_price"],
            "trend"     : prediction["trend"],
            "confidence": prediction["confidence"],
            "change_pct": prediction["change_pct"],
            "indicators": indicators,
            "chart"     : chart_data,
            "signals"   : prediction["signals"],
        }

        return success_response(payload)

    except Exception as exc:
        logger.error(f"[predict] Unhandled exception for {ticker}: {exc}\n"
                     + traceback.format_exc())
        return error_response("Internal server error. Please try again.", 500)


# ─── /api/stocks/trending ──────────────────────────────────────────────────────

@app.route("/api/stocks/trending", methods=["GET"])
def trending_stocks():
    """
    Returns snapshot data for a curated list of high-volume Indian stocks.
    Used to populate the "Trending Stocks" dashboard section.
    """
    TRENDING = [
        "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS",
        "ICICIBANK.NS", "WIPRO.NS", "SBIN.NS", "AXISBANK.NS"
    ]
    return _bulk_snapshot(TRENDING, "trending")


# ─── /api/stocks/top ──────────────────────────────────────────────────────────

@app.route("/api/stocks/top", methods=["GET"])
def top_stocks():
    """
    Returns snapshot data for stocks identified as top performers
    based on recent 30-day returns.
    """
    TOP = [
        "BAJFINANCE.NS", "ASIANPAINT.NS", "MARUTI.NS", "TITAN.NS",
        "HINDUNILVR.NS", "LTIM.NS", "NESTLEIND.NS", "ADANIENT.NS"
    ]
    return _bulk_snapshot(TOP, "top")


# ─── /api/stocks/search ───────────────────────────────────────────────────────

@app.route("/api/stocks/search", methods=["GET"])
def search_stock():
    """
    Quick lookup — returns current price + 1-day change for any ticker.
    Used by the frontend search bar to validate and preview before full load.
    """
    ticker = request.args.get("q", "").upper().strip()
    ticker_err = validate_ticker(ticker)
    if ticker_err:
        return error_response(ticker_err, 400)

    try:
        info = stock_svc.quick_quote(ticker)
        if info is None:
            return error_response(f"Ticker '{ticker}' not found.", 404)
        return success_response(info)
    except Exception as exc:
        logger.error(f"[search] {ticker}: {exc}")
        return error_response("Could not fetch quote.", 500)


# ═══════════════════════════════════════════════════════════════════════════════
#  PRIVATE HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _bulk_snapshot(tickers: list, label: str):
    """
    Fetch lightweight snapshot (price, change, sparkline) for multiple tickers.
    Failures on individual tickers are swallowed so the list still loads.
    """
    results = []
    for t in tickers:
        try:
            snap = stock_svc.quick_quote(t)
            if snap:
                results.append(snap)
        except Exception as e:
            logger.warning(f"[{label}] Skipping {t}: {e}")

    return success_response({"stocks": results, "category": label})


# ═══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import os
    os.makedirs("logs", exist_ok=True)
    app.run(debug=True, host="0.0.0.0", port=5000)