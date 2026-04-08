"""
ADB Provider - Low-level ADB interactions
Executes shell commands and manages connectivity
"""

import subprocess
import shlex
import logging
from typing import List, Optional, Tuple
from src.config import settings

logger = logging.getLogger(__name__)


def execute_adb_command(device_id: Optional[str], command: str, timeout: int = None) -> Tuple[bool, str, str]:
    """
    Execute an ADB command on a specific device.
    Automatically uses shell=True when command contains shell pipes (|).
    Returns: (success, stdout, stderr)
    """
    _timeout = timeout or settings.ADB_TIMEOUT
    try:
        # Build the adb prefix
        prefix = f'adb -s {device_id}' if device_id else 'adb'

        # If command contains a shell-level pipe operator, we must use shell=True
        # to let the OS shell handle the pipe properly
        if ' | ' in command:
            full_cmd = f'{prefix} {command}'
            result = subprocess.run(
                full_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=_timeout
            )
        else:
            cmd_parts = prefix.split() + shlex.split(command)
            result = subprocess.run(
                cmd_parts,
                shell=False,
                capture_output=True,
                text=True,
                timeout=_timeout
            )

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        # Real failure: non-zero exit, or stderr starts with 'error:', or Java exception
        real_error = (
            result.returncode != 0
            or stderr.lower().startswith('error:')
            or 'exception' in stderr.lower()
        )

        if real_error:
            logger.debug(f"ADB failed [{result.returncode}]: {command} | stderr: {stderr}")
            return False, stdout, stderr or "Command failed"

        return True, stdout, stderr

    except subprocess.TimeoutExpired:
        logger.warning(f"Command timed out ({_timeout}s) for device {device_id}: {command}")
        return False, "", f"Timed out after {_timeout}s"
    except Exception as e:
        logger.error(f"Error executing command on device {device_id}: {command}", exc_info=True)
        return False, "", f"Execution error: {str(e)}"


def check_adb_available() -> Tuple[bool, str]:
    """Check if ADB is installed and available"""
    try:
        result = subprocess.run(
            ["adb", "version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return True, result.stdout
        return False, "ADB not responding correctly"
    except FileNotFoundError:
        return False, "ADB not found in PATH"
    except Exception as e:
        return False, f"Error checking ADB: {str(e)}"


def get_raw_connected_devices() -> List[str]:
    """Get raw list of device IDs from ADB"""
    try:
        result = subprocess.run(
            ["adb", "devices"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            return []
        
        device_ids = []
        lines = result.stdout.strip().split('\n')[1:]  # Skip header
        
        for line in lines:
            if line.strip() and 'device' in line:
                parts = line.split()
                if len(parts) >= 1:
                    device_ids.append(parts[0])
        
        return device_ids
        
    except Exception as e:
        logger.error(f"Error getting raw devices: {e}", exc_info=True)
        return []
