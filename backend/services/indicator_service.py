"""
==============================================================================
services/indicator_service.py
==============================================================================
Responsibility : Compute all technical indicators from OHLCV data.
                 Returns a clean dict of indicator values for the prediction
                 engine and the frontend display layer.

Indicators implemented:
  ─ Trend          : SMA-20, SMA-50, EMA-12, EMA-26
  ─ Momentum       : RSI-14, MACD, Signal Line
  ─ Volatility     : Bollinger Bands (20,2), ATR-14, Daily Volatility %
  ─ Volume         : OBV (On-Balance Volume), Volume SMA-20
  ─ Returns        : Daily returns, 7d / 14d / 30d cumulative returns
==============================================================================
"""

import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class IndicatorService:
    """
    Pure computation service — takes a DataFrame, returns a dict of indicators.
    No I/O; all methods are deterministic given the same input.
    """

    def compute_all(self, df: pd.DataFrame) -> dict:
        """
        Master method. Computes and returns all indicators as a serialisable dict.

        Args:
            df : DataFrame with at minimum [Close, High, Low, Volume] columns.

        Returns:
            Dict suitable for JSON serialisation (no NaN, no Timestamps).
        """
        close  = df["Close"]
        high   = df["High"]
        low    = df["Low"]
        volume = df["Volume"]

        # ── Moving Averages ───────────────────────────────────────────────
        sma20 = self._sma(close, 20)
        sma50 = self._sma(close, 50)
        ema12 = self._ema(close, 12)
        ema26 = self._ema(close, 26)

        # ── MACD ──────────────────────────────────────────────────────────
        macd_line, signal_line, histogram = self._macd(close)

        # ── RSI ───────────────────────────────────────────────────────────
        rsi14 = self._rsi(close, 14)

        # ── Bollinger Bands ───────────────────────────────────────────────
        bb_upper, bb_middle, bb_lower = self._bollinger(close, 20, 2)

        # ── ATR ───────────────────────────────────────────────────────────
        atr14 = self._atr(high, low, close, 14)

        # ── OBV ───────────────────────────────────────────────────────────
        obv = self._obv(close, volume)

        # ── Returns ───────────────────────────────────────────────────────
        daily_returns = close.pct_change().dropna()
        vol_pct       = round(float(daily_returns.std() * np.sqrt(252) * 100), 4)  # annualised %

        def _cum_ret(n):
            if len(close) < n + 1:
                return None
            return round(((float(close.iloc[-1]) - float(close.iloc[-n-1]))
                          / float(close.iloc[-n-1])) * 100, 4)

        # ── Serialise: return only the most recent scalar or short series ─
        def _last(series):
            """Return most-recent non-NaN value as float, or None."""
            s = series.dropna()
            return round(float(s.iloc[-1]), 4) if not s.empty else None

        def _series_tail(series, n=60):
            """Return last n values as a list for chart overlays."""
            s = series.dropna()
            vals = s.tail(n).tolist()
            return [round(float(v), 2) if not np.isnan(v) else None for v in vals]

        return {
            # ── Scalars (latest value) ─────────────────────────────────
            "sma20"          : _last(sma20),
            "sma50"          : _last(sma50),
            "ema12"          : _last(ema12),
            "ema26"          : _last(ema26),
            "macd"           : _last(macd_line),
            "macd_signal"    : _last(signal_line),
            "macd_hist"      : _last(histogram),
            "rsi14"          : _last(rsi14),
            "bb_upper"       : _last(bb_upper),
            "bb_middle"      : _last(bb_middle),
            "bb_lower"       : _last(bb_lower),
            "atr14"          : _last(atr14),
            "obv"            : _last(obv),
            "volatility_ann" : vol_pct,
            "return_7d"      : _cum_ret(7),
            "return_14d"     : _cum_ret(14),
            "return_30d"     : _cum_ret(30),

            # ── Series (for chart overlay rendering) ──────────────────
            "series": {
                "sma20"     : _series_tail(sma20),
                "sma50"     : _series_tail(sma50),
                "ema12"     : _series_tail(ema12),
                "ema26"     : _series_tail(ema26),
                "bb_upper"  : _series_tail(bb_upper),
                "bb_lower"  : _series_tail(bb_lower),
                "rsi14"     : _series_tail(rsi14),
                "macd"      : _series_tail(macd_line),
                "macd_signal": _series_tail(signal_line),
            }
        }

    # ═══════════════════════════════════════════════════════════════════════════
    #  INDICATOR IMPLEMENTATIONS
    # ═══════════════════════════════════════════════════════════════════════════

    @staticmethod
    def _sma(series: pd.Series, window: int) -> pd.Series:
        """Simple Moving Average."""
        return series.rolling(window=window).mean()

    @staticmethod
    def _ema(series: pd.Series, span: int) -> pd.Series:
        """Exponential Moving Average (com-based, adjust=False for compatibility)."""
        return series.ewm(span=span, adjust=False).mean()

    def _macd(self, series: pd.Series,
              fast: int = 12, slow: int = 26, signal: int = 9):
        """
        MACD (Moving Average Convergence Divergence).

        Formula:
            MACD Line   = EMA(fast) − EMA(slow)
            Signal Line = EMA(MACD Line, signal)
            Histogram   = MACD Line − Signal Line
        """
        ema_fast   = self._ema(series, fast)
        ema_slow   = self._ema(series, slow)
        macd_line  = ema_fast - ema_slow
        signal_ln  = self._ema(macd_line, signal)
        histogram  = macd_line - signal_ln
        return macd_line, signal_ln, histogram

    @staticmethod
    def _rsi(series: pd.Series, period: int = 14) -> pd.Series:
        """
        Relative Strength Index (Wilder smoothing).

        Overbought: RSI > 70  |  Oversold: RSI < 30
        """
        delta  = series.diff()
        gain   = delta.where(delta > 0, 0.0)
        loss   = (-delta).where(delta < 0, 0.0)

        avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
        avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()

        rs  = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        return rsi

    @staticmethod
    def _bollinger(series: pd.Series, window: int = 20,
                   num_std: float = 2.0):
        """
        Bollinger Bands.

        Upper = SMA + k*σ  |  Lower = SMA − k*σ  (k=2 by default)
        """
        sma    = series.rolling(window).mean()
        std    = series.rolling(window).std()
        upper  = sma + (num_std * std)
        lower  = sma - (num_std * std)
        return upper, sma, lower

    @staticmethod
    def _atr(high: pd.Series, low: pd.Series,
             close: pd.Series, period: int = 14) -> pd.Series:
        """
        Average True Range — measures market volatility.

        True Range = max(H-L, |H-Prev_C|, |L-Prev_C|)
        ATR = EMA(True Range, period)
        """
        prev_close = close.shift(1)
        tr = pd.concat([
            high - low,
            (high - prev_close).abs(),
            (low  - prev_close).abs()
        ], axis=1).max(axis=1)

        return tr.ewm(span=period, adjust=False).mean()

    @staticmethod
    def _obv(close: pd.Series, volume: pd.Series) -> pd.Series:
        """
        On-Balance Volume — cumulative volume driven by price direction.

        OBV[t] = OBV[t-1] + Volume  if Close[t] > Close[t-1]
               = OBV[t-1] − Volume  if Close[t] < Close[t-1]
               = OBV[t-1]           if Close[t] == Close[t-1]
        """
        direction = np.sign(close.diff().fillna(0))
        obv       = (direction * volume).cumsum()
        return obv