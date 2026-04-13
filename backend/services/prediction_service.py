"""
==============================================================================
services/prediction_service.py
==============================================================================
Responsibility : AI-inspired hybrid price prediction engine.

Architecture:
  The predictor is a multi-signal ensemble model implemented without external
  ML libraries. It mirrors the conceptual architecture of an ML pipeline:

    1. Feature Engineering   — extracts normalised signals from indicators
    2. Signal Scoring        — each signal votes (+/-) with a weight
    3. Weighted Aggregation  — computes a net directional bias
    4. Price Projection      — translates bias to a predicted price delta
    5. Confidence Estimation — derived from signal agreement & volatility

  This approach produces interpretable, defensible predictions and can be
  trivially replaced with a trained LSTM or XGBoost model by swapping the
  `_ensemble_score` method.

Signal sources (8 independent signals):
  ─ SMA crossover (price vs SMA20, SMA50)
  ─ EMA crossover (EMA12 vs EMA26 — momentum direction)
  ─ MACD crossover (MACD vs Signal)
  ─ RSI regime     (oversold / overbought / neutral)
  ─ Bollinger Band position (near upper/lower band)
  ─ Volatility-adjusted momentum
  ─ Short-term return momentum (7d)
  ─ Volume trend (OBV direction)
==============================================================================
"""

import numpy as np
import pandas as pd
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


class PredictionService:
    """
    Weighted multi-signal ensemble predictor.

    Weights are calibrated based on empirical backtesting intuition;
    a production upgrade would tune these via gradient descent or
    Bayesian optimisation over a labelled dataset.
    """

    # Signal weights — must sum to 1.0
    WEIGHTS = {
        "sma_cross"      : 0.18,
        "ema_cross"      : 0.16,
        "macd_cross"     : 0.20,  # MACD gets highest weight (proven momentum)
        "rsi_regime"     : 0.15,
        "bollinger_pos"  : 0.10,
        "vol_momentum"   : 0.08,
        "return_momentum": 0.08,
        "obv_trend"      : 0.05,
    }

    # Projection horizon (trading days ahead)
    HORIZON = 5

    # ─── Public API ──────────────────────────────────────────────────────────

    def predict(self, df: pd.DataFrame, indicators: dict) -> dict:
        """
        Run the prediction pipeline and return a structured result.

        Args:
            df         : Full OHLCV DataFrame.
            indicators : Output of IndicatorService.compute_all().

        Returns:
            {
                predicted_price : float,
                trend           : "BULLISH" | "BEARISH" | "NEUTRAL",
                confidence      : float (0–100),
                change_pct      : float,
                signals         : list[dict] — individual signal breakdown
            }
        """
        current_price = float(df["Close"].iloc[-1])

        # ── Compute individual signal scores ─────────────────────────────
        scores, signal_details = self._score_all_signals(df, indicators)

        # ── Weighted ensemble ─────────────────────────────────────────────
        net_score = sum(
            scores[k] * self.WEIGHTS[k]
            for k in self.WEIGHTS
        )  # net_score ∈ [-1, +1]

        # ── Translate score to price projection ───────────────────────────
        volatility        = indicators.get("volatility_ann", 20) or 20
        daily_vol         = volatility / 100 / np.sqrt(252)

        # Expected move = net_score × horizon × daily_volatility × scaling_factor
        # Scaling factor (1.2) gives slight amplification to weak signals.
        expected_move_pct = net_score * self.HORIZON * daily_vol * 1.2 * 100
        predicted_price   = round(current_price * (1 + expected_move_pct / 100), 2)

        # ── Trend classification ──────────────────────────────────────────
        if net_score > 0.12:
            trend = "BULLISH"
        elif net_score < -0.12:
            trend = "BEARISH"
        else:
            trend = "NEUTRAL"

        # ── Confidence score ──────────────────────────────────────────────
        # Confidence = signal agreement × volatility penalty × RSI quality
        confidence = self._compute_confidence(scores, indicators, volatility)

        change_pct = round(
            ((predicted_price - current_price) / current_price) * 100, 2
        )

        return {
            "predicted_price" : predicted_price,
            "trend"           : trend,
            "confidence"      : confidence,
            "change_pct"      : change_pct,
            "signals"         : signal_details,
        }

    # ═══════════════════════════════════════════════════════════════════════════
    #  SIGNAL SCORING
    # ═══════════════════════════════════════════════════════════════════════════

    def _score_all_signals(self, df: pd.DataFrame,
                           ind: dict) -> Tuple[dict, list]:
        """
        Compute each signal score in [-1, +1] and build a human-readable
        breakdown list for the frontend.

        Returns:
            scores  : {signal_name: float}
            details : [{"name": str, "score": float, "label": str, "desc": str}]
        """
        close = df["Close"]
        scores  = {}
        details = []

        # ── 1. SMA Crossover ─────────────────────────────────────────────
        # Price above SMA20 (bullish) / below (bearish)
        sma20 = ind.get("sma20") or float(close.rolling(20).mean().iloc[-1])
        sma50 = ind.get("sma50") or float(close.rolling(50).mean().iloc[-1])
        cp    = float(close.iloc[-1])

        sma_score = 0.0
        if sma20 and sma50:
            if cp > sma20 and sma20 > sma50:
                sma_score = 1.0   # golden cross alignment
            elif cp > sma20:
                sma_score = 0.5
            elif cp < sma20 and sma20 < sma50:
                sma_score = -1.0  # death cross alignment
            elif cp < sma20:
                sma_score = -0.5

        scores["sma_cross"] = sma_score
        details.append(self._signal_detail(
            "SMA Crossover", sma_score,
            f"Price {'above' if cp > sma20 else 'below'} SMA20 ({sma20:.1f}). "
            f"SMA20 {'>' if sma20 > sma50 else '<'} SMA50 ({sma50:.1f})."
        ))

        # ── 2. EMA Crossover ─────────────────────────────────────────────
        # EMA12 > EMA26 → bullish momentum
        ema12 = ind.get("ema12")
        ema26 = ind.get("ema26")
        ema_score = 0.0
        if ema12 and ema26:
            diff_ratio = (ema12 - ema26) / ema26
            ema_score  = np.clip(diff_ratio * 50, -1, 1)  # normalise

        scores["ema_cross"] = ema_score
        details.append(self._signal_detail(
            "EMA Crossover", ema_score,
            f"EMA12={ema12:.1f} vs EMA26={ema26:.1f}. "
            f"{'Bullish' if ema_score > 0 else 'Bearish'} momentum alignment."
        ))

        # ── 3. MACD Crossover ─────────────────────────────────────────────
        macd   = ind.get("macd", 0) or 0
        signal = ind.get("macd_signal", 0) or 0
        hist   = ind.get("macd_hist", 0) or 0

        # Histogram direction + magnitude
        macd_score = np.clip(hist / (abs(macd) + 1e-6), -1, 1) if macd else 0.0
        scores["macd_cross"] = macd_score
        details.append(self._signal_detail(
            "MACD", macd_score,
            f"MACD={macd:.3f}, Signal={signal:.3f}, Histogram={hist:.3f}. "
            f"{'Positive' if hist > 0 else 'Negative'} histogram — "
            f"{'bullish' if hist > 0 else 'bearish'} momentum."
        ))

        # ── 4. RSI Regime ─────────────────────────────────────────────────
        rsi = ind.get("rsi14", 50) or 50
        if rsi < 30:
            rsi_score = 0.8   # oversold — potential reversal up
            rsi_label = "Oversold"
        elif rsi > 70:
            rsi_score = -0.8  # overbought — potential reversal down
            rsi_label = "Overbought"
        elif 40 <= rsi <= 60:
            rsi_score = 0.0   # neutral zone
            rsi_label = "Neutral"
        elif rsi > 60:
            rsi_score = 0.4
            rsi_label = "Mildly Overbought"
        else:
            rsi_score = -0.4
            rsi_label = "Mildly Oversold"

        scores["rsi_regime"] = rsi_score
        details.append(self._signal_detail(
            "RSI (14)", rsi_score,
            f"RSI={rsi:.1f} — {rsi_label}. "
            f"{'Buying pressure likely.' if rsi_score > 0 else 'Selling pressure likely.'}"
        ))

        # ── 5. Bollinger Band Position ────────────────────────────────────
        bb_upper = ind.get("bb_upper")
        bb_lower = ind.get("bb_lower")
        bb_mid   = ind.get("bb_middle")
        bb_score = 0.0

        if bb_upper and bb_lower and bb_mid:
            band_range = bb_upper - bb_lower
            if band_range > 0:
                # Normalise position within bands: -1 (at lower) to +1 (at upper)
                rel_pos  = (cp - bb_mid) / (band_range / 2)
                # Counter-trend: near upper → slightly bearish, near lower → bullish
                bb_score = np.clip(-rel_pos * 0.6, -1, 1)

        scores["bollinger_pos"] = bb_score
        details.append(self._signal_detail(
            "Bollinger Bands", bb_score,
            f"Price at {cp:.1f}. Bands: [{bb_lower:.1f} — {bb_upper:.1f}]. "
            f"{'Price near upper band (overbought zone).' if bb_score < 0 else 'Price near lower band (support zone).'}"
        ))

        # ── 6. Volatility-Adjusted Momentum ──────────────────────────────
        vol_ann    = ind.get("volatility_ann", 20) or 20
        ret_7d     = ind.get("return_7d", 0) or 0
        # Strong recent returns with high volatility = mean-reversion risk
        vol_score  = np.clip(ret_7d / (vol_ann + 1e-6) * 2, -1, 1)

        scores["vol_momentum"] = vol_score
        details.append(self._signal_detail(
            "Vol-Adj Momentum", vol_score,
            f"7-day return={ret_7d:.2f}%, Annualised vol={vol_ann:.2f}%. "
            f"Momentum {'strong' if abs(vol_score) > 0.5 else 'moderate'} relative to volatility."
        ))

        # ── 7. Return Momentum ────────────────────────────────────────────
        ret_30d      = ind.get("return_30d", 0) or 0
        ret_momentum = np.clip(ret_30d / 15, -1, 1)  # normalise at ±15% threshold

        scores["return_momentum"] = ret_momentum
        details.append(self._signal_detail(
            "30-Day Return", ret_momentum,
            f"30-day cumulative return={ret_30d:.2f}%. "
            f"{'Positive' if ret_30d > 0 else 'Negative'} trend continuation bias."
        ))

        # ── 8. OBV Trend ──────────────────────────────────────────────────
        obv    = float(ind.get("obv", 0) or 0)
        closes = df["Close"]
        obv_sma = self._compute_obv_trend(df)
        obv_score = np.clip(obv_sma / (abs(obv) + 1), -1, 1) if obv else 0.0

        scores["obv_trend"] = obv_score
        details.append(self._signal_detail(
            "OBV Trend", obv_score,
            f"On-Balance Volume trend is {'rising (accumulation)' if obv_score > 0 else 'falling (distribution)'}. "
            f"Volume confirms {'price rise' if obv_score > 0 else 'price fall'}."
        ))

        return scores, details

    # ═══════════════════════════════════════════════════════════════════════════
    #  CONFIDENCE SCORING
    # ═══════════════════════════════════════════════════════════════════════════

    def _compute_confidence(self, scores: dict, ind: dict,
                            volatility: float) -> float:
        """
        Confidence is a function of:
          1. Signal agreement ratio — what fraction of signals agree on direction
          2. Volatility penalty    — high volatility lowers confidence
          3. RSI quality           — extreme RSI boosts or dampens confidence

        Returns: float in [0, 100], rounded to 1 decimal.
        """
        score_values = list(scores.values())

        # Agreement ratio: signals with same sign as mean
        mean_dir = np.sign(np.mean(score_values))
        agreeing = sum(1 for s in score_values if np.sign(s) == mean_dir)
        agreement_ratio = agreeing / len(score_values)

        # Base confidence from agreement (0.5 → 50%, 1.0 → 90%)
        base = 50 + (agreement_ratio - 0.5) * 80  # maps [0.5,1.0] → [50,90]

        # Volatility penalty: high vol → less confident
        vol_penalty = min(volatility / 80, 0.3) * 100  # up to -30 pts

        # RSI modifier
        rsi = ind.get("rsi14", 50) or 50
        rsi_boost = 5 if (rsi < 35 or rsi > 65) else 0

        confidence = round(base - vol_penalty + rsi_boost, 1)
        return float(np.clip(confidence, 20, 92))  # floor=20, ceiling=92

    # ═══════════════════════════════════════════════════════════════════════════
    #  HELPERS
    # ═══════════════════════════════════════════════════════════════════════════

    @staticmethod
    def _signal_detail(name: str, score: float, desc: str) -> dict:
        """Build a signal breakdown dict for the API response."""
        label = ("STRONG BUY" if score > 0.7 else
                 "BUY"         if score > 0.2 else
                 "NEUTRAL"     if score > -0.2 else
                 "SELL"        if score > -0.7 else "STRONG SELL")
        return {
            "name" : name,
            "score": round(score, 4),
            "label": label,
            "desc" : desc,
        }

    @staticmethod
    def _compute_obv_trend(df: pd.DataFrame) -> float:
        """
        Return the slope of OBV relative to its 10-day EMA.
        Positive = OBV rising above its average (accumulation).
        """
        close  = df["Close"].values
        volume = df["Volume"].values
        obv    = np.zeros(len(close))

        for i in range(1, len(close)):
            if close[i] > close[i-1]:
                obv[i] = obv[i-1] + volume[i]
            elif close[i] < close[i-1]:
                obv[i] = obv[i-1] - volume[i]
            else:
                obv[i] = obv[i-1]

        if len(obv) < 10:
            return 0.0

        obv_series = pd.Series(obv)
        obv_ema    = obv_series.ewm(span=10, adjust=False).mean()
        return float(obv_series.iloc[-1] - obv_ema.iloc[-1])