"""
API Response Utilities - Global Helpers
Standardized JSON responses for Flask routes.
"""

from flask import jsonify
from typing import Any, Optional, Tuple
from src.schema.models import APIResponseModel
from src.helpers.date_utils import get_now_iso
from src.config import Settings, setup_logger

logger = setup_logger(Settings.LOG_DIR / "helper.log", name="epic_adb.helpers.responses")

def api_success(data: Any = None, message: str = None, status: int = 200) -> Tuple[Any, int]:
    """Standardized success response"""
    response = APIResponseModel(
        success=True,
        data=data,
        message=message,
        timestamp=get_now_iso()
    )
    return jsonify(response.model_dump()), status

def api_error(error: str, status: int = 400, details: Any = None) -> Tuple[Any, int]:
    """Standardized error response"""
    response = APIResponseModel(
        success=False,
        error=error,
        details=details,
        timestamp=get_now_iso()
    )
    logger.error(f"API Error ({status}): {error}")
    return jsonify(response.model_dump()), status
