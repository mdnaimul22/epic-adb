"""
Services Module - Business Logic
Exposed as per Project Structure Rule
"""

from .device import (
    get_connected_devices,
    get_device_manufacturer,
    get_device_location,
    get_comprehensive_device_info,
    get_command_state
)
from .profile import profile_manager
from .dns import dns_service
