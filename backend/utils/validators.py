"""
utils/validators.py
Input validation helpers for API request parameters.
"""

import re

VALID_PERIODS = {"1mo", "3mo", "6mo", "1y", "2y", "5y"}

# Regex: 1-12 uppercase letters, optionally followed by .NS or .BO
TICKER_PATTERN = re.compile(r"^[A-Z0-9]{1,20}(\.NS|\.BO|\.BSE)?$")


def validate_ticker(ticker: str) -> str | None:
    """
    Validate a stock ticker symbol.
    Returns an error message string if invalid, else None.
    """
    if not ticker:
        return "Missing required parameter: 'ticker'."
    if len(ticker) > 25:
        return "Ticker symbol too long (max 25 chars)."
    if not TICKER_PATTERN.match(ticker):
        return (
            f"Invalid ticker format: '{ticker}'. "
            "Use formats like RELIANCE.NS, TCS.BO, or AAPL."
        )
    return None


def validate_period(period: str) -> str | None:
    """
    Validate a period string.
    Returns an error message string if invalid, else None.
    """
    if period not in VALID_PERIODS:
        return (
            f"Invalid period '{period}'. "
            f"Accepted values: {', '.join(sorted(VALID_PERIODS))}."
        )
    return None