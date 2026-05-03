from pathlib import Path
from typing import Optional, List, Union
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from .paths import PROJECT_ROOT

class AppSettings(BaseSettings):
    # Base Config
    PROJECT_NAME: str = "epic-adb"
    VERSION: str = "1.0.0"
    ENV: str = Field(default="development", validation_alias="APP_ENV")
    LOG_LEVEL: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    
    # Server Configuration
    ADB_HOST: str = Field(default="0.0.0.0", validation_alias="ADB_HOST")
    ADB_PORT: int = Field(default=8765, validation_alias="ADB_PORT")
    DEBUG: bool = Field(default=False, validation_alias="DEBUG")
    
    # ADB Configuration
    ADB_TIMEOUT: int = Field(default=30, validation_alias="ADB_TIMEOUT")
    
    # CORS Configuration
    CORS_ORIGINS: Union[str, List[str]] = Field(default="*", validation_alias="CORS_ORIGINS")
    
    # Internal Path Settings
    LOG_DIR_STR: str = Field(default="logs", validation_alias="LOG_DIR")
    DATA_DIR_STR: str = Field(default="profiles_data", validation_alias="DATA_DIR")
    STATIC_DIR_STR: str = Field(default="static", validation_alias="STATIC_DIR")

    def _resolve(self, val: str) -> Path:
        p = Path(val).expanduser()
        return p if p.is_absolute() else PROJECT_ROOT / p

    @property
    def LOG_DIR(self) -> Path: return self._resolve(self.LOG_DIR_STR)
    
    @property
    def DATA_DIR(self) -> Path: return self._resolve(self.DATA_DIR_STR)
    
    @property
    def STATIC_DIR(self) -> Path: return self._resolve(self.STATIC_DIR_STR)
    
    @property
    def is_production(self) -> bool: return self.ENV.lower() == "production"
    
    @property
    def is_development(self) -> bool: return self.ENV.lower() == "development"

    @property
    def url(self) -> str:
        host = "localhost" if self.ADB_HOST == "0.0.0.0" else self.ADB_HOST
        return f"http://{host}:{self.ADB_PORT}"

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

# Singleton instance
Settings = AppSettings()
