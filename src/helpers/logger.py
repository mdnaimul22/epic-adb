"""
Logging Utilities - Global Helpers
Configures system-wide logging with both console and file handlers.
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.config.settings import Settings

def setup_logging(settings_obj: 'Settings') -> None:
    """
    Configure application-wide logging based on settings.
    """
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format))
    handlers.append(console_handler)
    
    # File handler (optional)
    if settings_obj.LOG_FILE:
        file_handler = logging.FileHandler(settings_obj.LOG_FILE)
        file_handler.setFormatter(logging.Formatter(log_format))
        handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, settings_obj.LOG_LEVEL),
        format=log_format,
        handlers=handlers
    )
    
    # Set Flask/Werkzeug logger level to warning
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
