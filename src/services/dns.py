"""
DNS Service - Handles DNS speed testing and configuration via ADB
Supports Private DNS (hostname mode) for Android 9+
"""

import socket
import time
import logging
from typing import List, Optional, Tuple
from src.providers import execute_adb_command
from src.schema import DnsProviderModel, DnsLatencyResultModel, DnsTestResponseModel

logger = logging.getLogger(__name__)

# List of popular DNS providers (DoH Hostnames)
DNS_PROVIDERS = [
    DnsProviderModel(name="Cloudflare", hostname="1dot1dot1dot1.cloudflare-dns.com", address="1.1.1.1"),
    DnsProviderModel(name="Google", hostname="dns.google", address="8.8.8.8"),
    DnsProviderModel(name="AdGuard", hostname="dns.adguard.com", address="94.140.14.14"),
    DnsProviderModel(name="Quad9", hostname="dns.quad9.net", address="9.9.9.9"),
    DnsProviderModel(name="OpenDNS", hostname="dns.opendns.com", address="208.67.222.222")
]

class DnsService:
    """Service to handle DNS latency testing and ADB application"""

    def test_latency(self, provider: DnsProviderModel, port: int = 853, timeout: float = 2.0) -> Optional[float]:
        """
        Measure TCP latency to a provider.
        Default port 853 is for DNS-over-TLS (Private DNS).
        Returns latency in milliseconds or None if failed.
        """
        start_time = time.time()
        try:
            # Create a socket connection to measure handshake time
            with socket.create_connection((provider.address, port), timeout=timeout):
                latency = (time.time() - start_time) * 1000
                return round(latency, 2)
        except (socket.timeout, ConnectionRefusedError, OSError):
            logger.warning(f"Failed to connect to DNS provider {provider.name} at {provider.address}")
            return None

    def run_speed_test(self) -> DnsTestResponseModel:
        """Run latency tests for all providers and find the best one"""
        results = []
        for provider in DNS_PROVIDERS:
            latency = self.test_latency(provider)
            if latency is not None:
                results.append(DnsLatencyResultModel(
                    name=provider.name,
                    hostname=provider.hostname,
                    latency_ms=latency
                ))
        
        # Sort results by latency (lowest first)
        results.sort(key=lambda x: x.latency_ms)
        
        recommended = results[0] if results else None
        
        return DnsTestResponseModel(
            results=results,
            recommended=recommended
        )

    def apply_dns(self, device_id: str, hostname: str) -> Tuple[bool, str]:
        """Apply a private DNS hostname to a device via ADB"""
        # Set mode to hostname
        success1, _, err1 = execute_adb_command(device_id, "shell settings put global private_dns_mode hostname")
        if not success1:
            return False, f"Failed to set DNS mode: {err1}"
            
        # Set the specifier (hostname)
        success2, _, err2 = execute_adb_command(device_id, f"shell settings put global private_dns_specifier {hostname}")
        if not success2:
            return False, f"Failed to set DNS hostname: {err2}"
            
        return True, f"Successfully applied DNS: {hostname}"

    def reset_dns(self, device_id: str) -> Tuple[bool, str]:
        """Reset private DNS to automatic mode"""
        success, _, err = execute_adb_command(device_id, "shell settings put global private_dns_mode automatic")
        if success:
            return True, "Private DNS reset to Automatic"
        return False, f"Failed to reset DNS: {err}"

dns_service = DnsService()
