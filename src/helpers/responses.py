"""
API Response Utilities - Global Helpers
Standardized JSON responses for Flask routes.
"""

import logging
from flask import jsonify
from typing import Any, Optional, Tuple
from src.schema.models import APIResponseModel
from src.helpers.date_utils import get_now_iso

logger = logging.getLogger(__name__)

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
