"""
Configuration Management for adb-turbo
Pattern: os.getenv('', '') as requested
"""

import os
import logging
from typing import Optional, List, Union
from pydantic import Field, field_validator, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Load .env file explicitly
load_dotenv()


class Settings(BaseSettings):
    """
    Application configuration with environment variable support.
    Follows os.getenv('', '') pattern for explicit control.
    """
    model_config = SettingsConfigDict(
        env_prefix='',
        extra='ignore'
    )
    
    # Server Configuration
    ADB_HOST: str = os.getenv('ADB_HOST', '0.0.0.0')
    ADB_PORT: int = int(os.getenv('ADB_PORT', '8765'))
    DEBUG: bool = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE: Optional[str] = os.getenv('LOG_FILE', None)
    
    # ADB Configuration
    ADB_TIMEOUT: int = int(os.getenv('ADB_TIMEOUT', '30'))
    
    # Paths (Auto-calculated)
    @computed_field
    @property
    def BASE_DIR(self) -> str:
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    @computed_field
    @property
    def DATA_DIR(self) -> str:
        return os.path.join(self.BASE_DIR, 'profiles_data')
    
    @computed_field
    @property
    def STATIC_DIR(self) -> str:
        return os.path.join(self.BASE_DIR, 'static')
    
    # CORS Configuration
    CORS_ORIGINS: Union[str, List[str]] = os.getenv('CORS_ORIGINS', '*')

    @field_validator('LOG_LEVEL')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}")
        return v.upper()

    @computed_field
    @property
    def url(self) -> str:
        """Get the server URL"""
        host = 'localhost' if self.ADB_HOST == '0.0.0.0' else self.ADB_HOST
        return f"http://{host}:{self.ADB_PORT}"

    def ensure_dirs(self):
        """Ensure required directories exist"""
        os.makedirs(self.DATA_DIR, exist_ok=True)
        if self.LOG_FILE:
            log_dir = os.path.dirname(os.path.abspath(self.LOG_FILE))
            os.makedirs(log_dir, exist_ok=True)


# Create global settings instance
settings = Settings()
settings.ensure_dirs()
