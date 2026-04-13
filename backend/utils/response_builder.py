"""
utils/response_builder.py
Standardised JSON response envelopes for all API endpoints.
"""

from flask import jsonify
from datetime import datetime


def success_response(data: dict, status: int = 200):
    """
    Standard success envelope.

    {
        "status"    : "success",
        "timestamp" : "ISO8601",
        "data"      : {...}
    }
    """
    return jsonify({
        "status"   : "success",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "data"     : data,
    }), status


def error_response(message: str, status: int = 400):
    """
    Standard error envelope.

    {
        "status"  : "error",
        "message" : "...",
        "code"    : 400
    }
    """
    return jsonify({
        "status" : "error",
        "message": message,
        "code"   : status,
    }), status