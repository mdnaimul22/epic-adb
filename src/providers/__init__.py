"""
Providers Module - External API / System integrations
Exposed as per Project Structure Rule
"""

from .adb import (
    execute_adb_command,
    check_adb_available,
    get_raw_connected_devices
)
