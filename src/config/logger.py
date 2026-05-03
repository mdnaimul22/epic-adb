import logging
import sys
import threading
from logging.handlers import RotatingFileHandler
from pathlib import Path

_NOISY_LOGGERS: tuple[str, ...] = ("httpx", "openai", "anthropic", "httpcore","urllib3", "asyncio", "multipart",)

_lock              = threading.Lock()
_registry: dict[str, logging.Logger] = {}
_system_configured = False

def _build_formatter() -> logging.Formatter:
    return logging.Formatter(
        fmt     = "%(asctime)s  %(levelname)-8s  %(name)-35s  %(message)s",
        datefmt = "%Y-%m-%d %H:%M:%S",
    )

def _configure_system(log_dir: Path, is_production: bool) -> None:
    global _system_configured
    if _system_configured:
        return

    root = logging.getLogger()
    root.setLevel(logging.INFO if is_production else logging.DEBUG)

    for name in _NOISY_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)

    log_dir.mkdir(parents=True, exist_ok=True)
    _system_configured = True


def setup_logger(log_file_path: Path, name: str) -> logging.Logger:
    """
    Return a fully configured Logger.
    
    Usage:
        logger = setup_logger(Settings.LOG_DIR / "service.log", name="epic_adb.services.device")
    """
    if name in _registry:
        return _registry[name]

    with _lock:
        if name in _registry:
            return _registry[name]

        from .settings import Settings

        is_prod  : bool = Settings.is_production
        log_dir  : Path = Settings.LOG_DIR

        _configure_system(log_dir, is_prod)

        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        logger.propagate = False

        if logger.handlers:
            _registry[name] = logger
            return logger

        fmt = _build_formatter()

        # Ensure parent directory of log file exists
        log_file_path.parent.mkdir(parents=True, exist_ok=True)

        fh = RotatingFileHandler(
            log_file_path,
            maxBytes    = 5 * 1024 * 1024,
            backupCount = 3,
            encoding    = "utf-8",
        )
        fh.setLevel(logging.INFO if is_prod else logging.DEBUG)
        fh.setFormatter(fmt)
        logger.addHandler(fh)

        sh = logging.StreamHandler(sys.stdout)
        sh.setLevel(logging.WARNING if is_prod else logging.DEBUG)
        sh.setFormatter(fmt)
        logger.addHandler(sh)

        _registry[name] = logger
        return logger
