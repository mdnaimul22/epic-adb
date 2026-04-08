"""
Date & Time Utilities - Global Helpers
Standardized ISO 8601 timestamps (UTC)
"""

from datetime import datetime, timezone

def get_now_iso() -> str:
    """Get current UTC timestamp in ISO 8601 format"""
    return datetime.now(timezone.utc).isoformat()

def format_iso(dt: datetime) -> str:
    """Format a datetime object to ISO 8601 string"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()
