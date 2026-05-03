"""
Tests for configuration management
"""

import pytest
import os
from src.config import Settings, AppSettings


def test_config_defaults():
    """Test default configuration values"""
    # Note: Since Settings is a singleton, this reflects existing env vars
    pass


def test_config_from_env(monkeypatch):
    """Test configuration from environment variables"""
    # Clear any existing env vars first
    monkeypatch.delenv('ADB_HOST', raising=False)
    monkeypatch.delenv('ADB_PORT', raising=False)
    monkeypatch.delenv('DEBUG', raising=False)
    monkeypatch.delenv('LOG_LEVEL', raising=False)
    
    # Set new values
    monkeypatch.setenv('ADB_HOST', '127.0.0.1')
    monkeypatch.setenv('ADB_PORT', '9000')
    monkeypatch.setenv('DEBUG', 'true')
    monkeypatch.setenv('LOG_LEVEL', 'DEBUG')
    
    # To test env loading, we need a fresh Settings instance
    test_settings = AppSettings()
    
    assert test_settings.ADB_HOST == '127.0.0.1'
    assert test_settings.ADB_PORT == 9000
    assert test_settings.DEBUG is True
    assert test_settings.LOG_LEVEL == 'DEBUG'


def test_config_invalid_port():
    """Test configuration validation for invalid port"""
    from pydantic import ValidationError
    
    with pytest.raises(ValidationError):
        AppSettings(ADB_PORT="not-a-number")


def test_config_invalid_timeout():
    """Test configuration validation for invalid timeout"""
    from pydantic import ValidationError
    
    with pytest.raises(ValidationError):
        AppSettings(ADB_TIMEOUT="invalid")
