"""
Device Service - Business logic for device interactions
Uses providers and returns schema-validated data
"""

import re
import logging
from typing import List, Dict, Optional, Tuple
from src.providers import execute_adb_command, get_raw_connected_devices
from src.schema import DeviceModel, DeviceInfoModel, DeviceDetailsModel

logger = logging.getLogger(__name__)


def get_connected_devices() -> List[DeviceModel]:
    """Get list of connected ADB devices with model info"""
    device_ids = get_raw_connected_devices()
    devices = []
    
    for device_id in device_ids:
        # Get model info
        success, stdout, _ = execute_adb_command(device_id, "shell getprop ro.product.model")
        model = stdout.strip() if success else "Unknown"
        
        devices.append(DeviceModel(id=device_id, model=model))
        
    return devices


def get_device_manufacturer(device_id: str) -> str:
    """Get device manufacturer"""
    success, stdout, _ = execute_adb_command(device_id, "shell getprop ro.product.manufacturer")
    if success:
        return stdout.strip().lower()
    return "unknown"


def get_device_location(device_id: str) -> Tuple[Optional[float], Optional[float]]:
    """Get device's last known location"""
    try:
        success, stdout, _ = execute_adb_command(device_id, "shell dumpsys location")
        if not success or not stdout:
            return None, None
            
        pattern = r'\[fused\s+([-\d.]+),([-\d.]+)'
        for line in stdout.split('\n'):
            if 'last location' in line.lower() and 'fused' in line.lower():
                match = re.search(pattern, line)
                if match:
                    return float(match.group(1)), float(match.group(2))
        return None, None
    except Exception as e:
        logger.error(f"Error getting location: {e}")
        return None, None


def get_command_state(device_id: str, get_cmd: str) -> Optional[bool]:
    """Read the current state of a command"""
    if not get_cmd:
        return None
    
    success, stdout, _ = execute_adb_command(device_id, get_cmd)
    if not success:
        return None
    
    value = stdout.strip()
    if value in ['null', '']:
        return None
    
    if value == '1' or value.lower() == 'true':
        return True
    elif value == '0' or value.lower() == 'false':
        return False
    
    if '=' in value:
        parts = value.split('=')
        if len(parts) >= 2:
            extracted = parts[-1].strip().lower()
            if extracted == 'true': return True
            if extracted == 'false': return False
            
    try:
        return float(value) > 0
    except ValueError:
        pass
        
    return True if value and value != 'off' else None


def get_comprehensive_device_info(device_id: str) -> DeviceInfoModel:
    """Get comprehensive device information for the dashboard"""
    # Basic Info
    success, manufacturer_raw, _ = execute_adb_command(device_id, "shell getprop ro.product.manufacturer")
    manufacturer = manufacturer_raw.strip() if success else "Unknown"
    
    success, model_raw, _ = execute_adb_command(device_id, "shell getprop ro.product.model")
    model = model_raw.strip() if success else "Unknown"
    
    success, sdk_raw, _ = execute_adb_command(device_id, "shell getprop ro.build.version.sdk")
    sdk_version = sdk_raw.strip() if success else "Unknown"
    
    success, rel_raw, _ = execute_adb_command(device_id, "shell getprop ro.build.version.release")
    android_version = rel_raw.strip() if success else "Unknown"
    
    is_samsung = "samsung" in manufacturer.lower()
    
    lat, lon = get_device_location(device_id)
    location = {
        'latitude': lat,
        'longitude': lon,
        'available': lat is not None and lon is not None
    }

    # Detailed Info Collection
    details = {}

    # Battery
    success, stdout, _ = execute_adb_command(device_id, "shell dumpsys battery")
    if success:
        b_info = {}
        for line in stdout.split('\n'):
            if 'level:' in line: b_info['level'] = line.split(':')[1].strip()
            elif 'temperature:' in line: 
                temp = int(line.split(':')[1].strip())
                b_info['temperature'] = f"{temp / 10}°C"
            elif 'health:' in line:
                healths = {1: 'Unknown', 2: 'Good', 3: 'Overheat', 4: 'Dead', 5: 'Over Voltage', 6: 'Failure'}
                val_raw = line.split(':')[1].strip()
                try:
                    val = int(val_raw)
                    b_info['health'] = healths.get(val, 'Unknown')
                except ValueError:
                    b_info['health'] = 'Unknown'
            elif 'status:' in line:
                statuses = {1: 'Unknown', 2: 'Charging', 3: 'Discharging', 4: 'Not Charging', 5: 'Full'}
                val_raw = line.split(':')[1].strip()
                try:
                    val = int(val_raw)
                    b_info['status'] = statuses.get(val, 'Unknown')
                except ValueError:
                    b_info['status'] = 'Unknown'
        details['battery'] = b_info

    # Network
    success, stdout, _ = execute_adb_command(device_id, "shell ip addr show wlan0")
    if success:
        match = re.search(r'inet\s+([\d.]+)', stdout)
        if match:
            details['network'] = {'ip_addresses': match.group(1)}

    # Display
    success, stdout, _ = execute_adb_command(device_id, "shell wm size")
    if success:
        size = stdout.replace("Physical size: ", "").strip()
        success2, stdout2, _ = execute_adb_command(device_id, "shell wm density")
        density = stdout2.replace("Physical density: ", "").strip() if success2 else ""
        details['display'] = {'resolution': size, 'density': density}

    # Memory
    success, stdout, _ = execute_adb_command(device_id, "shell cat /proc/meminfo")
    if success:
        m_info = {}
        for line in stdout.split('\n'):
            if 'MemTotal:' in line: 
                parts = line.split()
                if len(parts) >= 2:
                    m_info['total'] = f"{int(parts[1])/1024/1024:.1f} GB"
            if 'MemAvailable:' in line: 
                parts = line.split()
                if len(parts) >= 2:
                    m_info['available'] = f"{int(parts[1])/1024/1024:.1f} GB"
        details['memory'] = m_info

    # CPU
    success, stdout, _ = execute_adb_command(device_id, "shell getprop ro.board.platform")
    if success:
        hw = stdout.strip()
        success2, stdout2, _ = execute_adb_command(device_id, "shell nproc")
        cores = stdout2.strip() if success2 else ""
        details['cpu'] = {'hardware': hw.upper(), 'cores': cores}

    # Storage
    success, stdout, _ = execute_adb_command(device_id, "shell df -h /data")
    if success:
        lines = stdout.strip().split('\n')
        if len(lines) > 1:
            parts = lines[-1].split() 
            if len(parts) >= 4:
                details['storage'] = {'total': parts[1], 'used': parts[2], 'available': parts[3]}

    # App & Uptime
    success, stdout, _ = execute_adb_command(device_id, "shell uptime")
    if success:
        details['uptime'] = stdout.split('up')[1].split(',')[0].strip() if 'up' in stdout else stdout.strip()

    success, stdout, _ = execute_adb_command(device_id, "shell dumpsys window | grep mCurrentFocus")
    if success:
        match = re.search(r'\{.*?\s+(.*?)/', stdout)
        if match:
            details['current_app'] = match.group(1)

    return DeviceInfoModel(
        manufacturer=manufacturer,
        model=model,
        sdk_version=sdk_version,
        android_version=android_version,
        is_samsung=is_samsung,
        location=location,
        details=DeviceDetailsModel(**details)
    )
