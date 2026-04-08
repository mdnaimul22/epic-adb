"""
Models for adb-turbo using Pydantic V2
Ensures type safety, easy serialization, and validation
"""

from typing import List, Optional, Dict, Union, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, timezone


class ADBCommandModel(BaseModel):
    """Model for a single ADB command with metadata"""
    model_config = ConfigDict(from_attributes=True)
    
    name: str
    description: str
    enable_cmd: str
    disable_cmd: str
    explanation: str
    impact: str = "medium"
    get_cmd: Optional[str] = None
    device_check: Optional[str] = None
    samsung_only: bool = False


class ADBCategoryModel(BaseModel):
    """Model for a category of ADB commands"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    name: str
    description: str
    impact: str
    commands: List[ADBCommandModel] = Field(default_factory=list)


class DeviceModel(BaseModel):
    """Model for a connected ADB device"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    model: str = "Unknown"
    status: str = "connected"


class DeviceDetailsModel(BaseModel):
    """Detailed hardware information for the dashboard"""
    battery: Optional[Dict[str, str]] = None
    network: Optional[Dict[str, str]] = None
    display: Optional[Dict[str, str]] = None
    memory: Optional[Dict[str, str]] = None
    cpu: Optional[Dict[str, str]] = None
    storage: Optional[Dict[str, str]] = None
    uptime: Optional[str] = None
    current_app: Optional[str] = None


class DeviceInfoModel(BaseModel):
    """Comprehensive device information model"""
    model_config = ConfigDict(from_attributes=True)
    
    # Basic info
    manufacturer: str = "Unknown"
    model: str = "Unknown"
    sdk_version: str = "Unknown"
    android_version: str = "Unknown"
    is_samsung: bool = False
    location: Optional[Dict[str, Any]] = None
    details: Optional[DeviceDetailsModel] = None


class SettingStateModel(BaseModel):
    """Model for a single setting's state in a profile"""
    model_config = ConfigDict(from_attributes=True)
    
    state: Optional[Union[bool, str, float]] = None
    category: str = ""
    enable_cmd: str = ""
    disable_cmd: str = ""
    get_cmd: Optional[str] = None


class ProfileModel(BaseModel):
    """Model for a device settings profile/backup"""
    model_config = ConfigDict(from_attributes=True)
    
    device_id: str
    manufacturer: str
    model: str
    settings: Dict[str, SettingStateModel]
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    backup_type: str = "automatic"
    original_timestamp: Optional[str] = None


class DeviceBackupsModel(BaseModel):
    """Model for storing all backups of a device"""
    model_config = ConfigDict(from_attributes=True)
    
    device_info: Dict[str, str]
    backups: List[ProfileModel] = Field(default_factory=list)


class APIResponseModel(BaseModel):
    """Standardized API response model"""
    model_config = ConfigDict(from_attributes=True)
    
    success: bool
    data: Optional[Any] = None
    message: Optional[str] = None
    error: Optional[str] = None
    details: Optional[Dict] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class DnsProviderModel(BaseModel):
    """Model for a DNS provider"""
    name: str
    hostname: str
    address: str


class DnsLatencyResultModel(BaseModel):
    """Latencies for a specific DNS"""
    name: str
    hostname: str
    latency_ms: float


class DnsTestResponseModel(BaseModel):
    """DNS speed test results with prediction"""
    results: List[DnsLatencyResultModel]
    recommended: Optional[DnsLatencyResultModel] = None
