"""
Tests for configuration management
"""

import pytest
import os
from src.config import Config


def test_config_defaults():
    """Test default configuration values"""
    config = Config()
    assert config.HOST == '0.0.0.0'
    assert config.PORT == 8765
    assert config.DEBUG is False
    assert config.LOG_LEVEL == 'INFO'
    assert config.ADB_TIMEOUT == 30


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
    
    # Create config after setting env vars
    from importlib import reload
    import src.config as config_module
    reload(config_module)
    test_config = config_module.Config()
    
    assert test_config.HOST == '127.0.0.1'
    assert test_config.PORT == 9000
    assert test_config.DEBUG is True
    assert test_config.LOG_LEVEL == 'DEBUG'


def test_config_invalid_port():
    """Test configuration validation for invalid port"""
    with pytest.raises(ValueError, match="Invalid port number"):
        Config(PORT=70000)


def test_config_invalid_timeout():
    """Test configuration validation for invalid timeout"""
    with pytest.raises(ValueError, match="Invalid timeout"):
        Config(ADB_TIMEOUT=0)


def test_config_invalid_log_level():
    """Test configuration validation for invalid log level"""
    with pytest.raises(ValueError, match="Invalid log level"):
        Config(LOG_LEVEL='INVALID')


def test_config_url():
    """Test URL generation"""
    config = Config()
    assert config.url == 'http://localhost:8765'
    
    config = Config(HOST='192.168.1.1', PORT=8080)
    assert config.url == 'http://192.168.1.1:8080'

