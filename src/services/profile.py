"""
Profile Service - Profile management business logic
Handles backup, restore, and presets with detailed background rules
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional
from pathlib import Path
from src.config import settings
from src.schema import ProfileModel, SettingStateModel
from src.providers import execute_adb_command
from src.core import COMMAND_CATEGORIES
from .device import get_command_state

logger = logging.getLogger(__name__)

# Profile storage directory
PROFILES_DIR = Path(settings.DATA_DIR)
PROFILES_DIR.mkdir(exist_ok=True)
PROFILES_FILE = PROFILES_DIR / "profiles.json"


class ProfileManager:
    """Manages device profiles with backup/restore functionality"""
    
    def __init__(self):
        self.profiles = self._load_profiles()
    
    def _load_profiles(self) -> Dict:
        """Load profiles from disk"""
        if PROFILES_FILE.exists():
            try:
                with open(PROFILES_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading profiles: {e}")
                return {}
        return {}
    
    def _save_profiles(self):
        """Save profiles to disk"""
        try:
            with open(PROFILES_FILE, 'w') as f:
                json.dump(self.profiles, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving profiles: {e}")
            raise
    
    def get_device_key(self, manufacturer: str, model: str) -> str:
        """Generate unique key for device (consistent across sessions)"""
        return f"{manufacturer}_{model}".replace(" ", "_").lower()
    
    def backup_device_settings(self, device_id: str, manufacturer: str, model: str) -> ProfileModel:
        """Backup all current device settings"""
        device_key = self.get_device_key(manufacturer, model)
        
        settings_data = {}
        for category in COMMAND_CATEGORIES:
            for cmd in category.commands:
                if cmd.get_cmd:
                    state = get_command_state(device_id, cmd.get_cmd)
                    settings_data[cmd.name] = SettingStateModel(
                        state=state,
                        category=category.id,
                        enable_cmd=cmd.enable_cmd,
                        disable_cmd=cmd.disable_cmd,
                        get_cmd=cmd.get_cmd
                    )
        
        profile = ProfileModel(
            device_id=device_id,
            manufacturer=manufacturer,
            model=model,
            settings=settings_data,
            timestamp=datetime.now(timezone.utc).isoformat(),
            backup_type='automatic'
        )
        
        if device_key not in self.profiles:
            self.profiles[device_key] = {
                'device_info': {'manufacturer': manufacturer, 'model': model},
                'backups': []
            }
        
        # Add to backups list (keep last 10)
        backups = self.profiles[device_key]['backups']
        backups.insert(0, profile.model_dump())
        self.profiles[device_key]['backups'] = backups[:10]
        
        self._save_profiles()
        return profile
    
    def restore_device_settings(self, device_id: str, manufacturer: str, model: str,
                                backup_index: int = 0) -> Dict:
        """Restore device settings from a saved backup"""
        device_key = self.get_device_key(manufacturer, model)

        backups = self.profiles.get(device_key, {}).get('backups', [])
        if not backups:
            raise ValueError("No backups found for this device. Create a backup first.")
        if backup_index >= len(backups):
            raise ValueError(f"Backup #{backup_index} not found. Only {len(backups)} backup(s) exist.")

        backup_data = backups[backup_index]
        backup = ProfileModel(**backup_data)
        results: Dict = {'success': [], 'failed': [], 'skipped': []}

        for name, data in backup.settings.items():
            if data.state is None:
                results['skipped'].append(name)
                continue
            cmd = data.enable_cmd if data.state else data.disable_cmd
            if not cmd:
                results['skipped'].append(name)
                continue
            success, stdout, stderr = execute_adb_command(device_id, cmd)
            if success:
                results['success'].append(name)
            else:
                results['failed'].append({'name': name, 'error': stderr or 'Unknown error'})

        return results

    def _find_command(self, category_id: str, command_name: str):
        """Find a command object by category and name in the global list"""
        for category in COMMAND_CATEGORIES:
            if category.id == category_id:
                for cmd in category.commands:
                    if cmd.name == command_name:
                        return cmd
        return None

    def _get_presets(self) -> Dict:
        """Define preset configurations replicated from backup metadata"""
        return {
            'high_performance': {
                'name': 'High Performance',
                'description': 'Maximum speed and responsiveness (no thermal throttling)',
                'settings': [
                    {'category': 'animation_settings', 'command': 'Window Animation Scale', 'action': 'disable'},
                    {'category': 'animation_settings', 'command': 'Transition Animation Scale', 'action': 'disable'},
                    {'category': 'animation_settings', 'command': 'Animator Duration Scale', 'action': 'disable'},
                    {'category': 'fixed_performance', 'command': 'Fixed Performance Mode', 'action': 'disable'},
                    {'category': 'ram_plus', 'command': 'ZRAM (Virtual RAM)', 'action': 'disable'},
                    {'category': 'ram_plus', 'command': 'RAM Expansion', 'action': 'disable'},
                    {'category': 'refresh_rate', 'command': 'Peak Refresh Rate', 'action': 'enable'},
                    {'category': 'refresh_rate', 'command': 'Minimum Refresh Rate', 'action': 'enable'},
                    {'category': 'refresh_rate', 'command': 'Window Blur Effects', 'action': 'disable'},
                    {'category': 'refresh_rate', 'command': 'Reduce Transparency', 'action': 'disable'},
                    {'category': 'network_performance', 'command': 'WiFi Power Save', 'action': 'disable'},
                    {'category': 'touchscreen_latency', 'command': 'Long Press Timeout', 'action': 'disable'},
                    {'category': 'touchscreen_latency', 'command': 'Multi-Press Timeout', 'action': 'disable'},
                ]
            },
            'max_battery': {
                'name': 'Max Battery',
                'description': 'Extended battery life settings',
                'settings': [
                    {'category': 'animation_settings', 'command': 'Window Animation Scale', 'action': 'disable'},
                    {'category': 'animation_settings', 'command': 'Transition Animation Scale', 'action': 'disable'},
                    {'category': 'animation_settings', 'command': 'Animator Duration Scale', 'action': 'disable'},
                    {'category': 'fixed_performance', 'command': 'Fixed Performance Mode', 'action': 'disable'},
                    {'category': 'ram_plus', 'command': 'ZRAM (Virtual RAM)', 'action': 'enable'},
                    {'category': 'refresh_rate', 'command': 'Peak Refresh Rate', 'action': 'disable'},
                    {'category': 'refresh_rate', 'command': 'Minimum Refresh Rate', 'action': 'disable'},
                    {'category': 'refresh_rate', 'command': 'Window Blur Effects', 'action': 'disable'},
                    {'category': 'network_performance', 'command': 'WiFi Power Save', 'action': 'enable'},
                    {'category': 'network_performance', 'command': 'BLE Scan Always Enabled', 'action': 'disable'},
                    {'category': 'network_performance', 'command': 'Mobile Data Always On', 'action': 'disable'},
                ]
            },
            'max_quality': {
                'name': 'Max Quality',
                'description': 'Best visual quality and audio fidelity',
                'settings': [
                    {'category': 'animation_settings', 'command': 'Window Animation Scale', 'action': 'enable'},
                    {'category': 'animation_settings', 'command': 'Transition Animation Scale', 'action': 'enable'},
                    {'category': 'animation_settings', 'command': 'Animator Duration Scale', 'action': 'enable'},
                    {'category': 'refresh_rate', 'command': 'Peak Refresh Rate', 'action': 'enable'},
                    {'category': 'refresh_rate', 'command': 'Minimum Refresh Rate', 'action': 'enable'},
                    {'category': 'refresh_rate', 'command': 'Window Blur Effects', 'action': 'enable'},
                    {'category': 'refresh_rate', 'command': 'Reduce Transparency', 'action': 'enable'},
                    {'category': 'audio_quality', 'command': 'K2HD Audio Effect', 'action': 'enable'},
                    {'category': 'audio_quality', 'command': 'Tube Amp Effect', 'action': 'enable'},
                    {'category': 'network_performance', 'command': 'WiFi Power Save', 'action': 'disable'},
                    {'category': 'network_performance', 'command': 'Mobile Data Always On', 'action': 'enable'},
                ]
            },
            'recommended': {
                'name': 'Recommended',
                'description': 'Balanced performance for general usage',
                'settings': [
                    {'category': 'animation_settings', 'command': 'Window Animation Scale', 'action': 'enable'},
                    {'category': 'animation_settings', 'command': 'Transition Animation Scale', 'action': 'enable'},
                    {'category': 'animation_settings', 'command': 'Animator Duration Scale', 'action': 'enable'},
                    {'category': 'ram_plus', 'command': 'ZRAM (Virtual RAM)', 'action': 'disable'},
                    {'category': 'refresh_rate', 'command': 'Peak Refresh Rate', 'action': 'enable'},
                    {'category': 'refresh_rate', 'command': 'Minimum Refresh Rate', 'action': 'disable'},
                    {'category': 'network_performance', 'command': 'BLE Scan Always Enabled', 'action': 'disable'},
                    {'category': 'touchscreen_latency', 'command': 'Long Press Timeout', 'action': 'disable'},
                ]
            }
        }

    def apply_preset(self, device_id: str, preset_name: str) -> Dict:
        """Apply a pre-defined set of optimizations with precise rules"""
        presets = self._get_presets()
        if preset_name not in presets:
            raise ValueError(f"Unknown preset: {preset_name}")
            
        preset = presets[preset_name]
        results = {'success': [], 'failed': [], 'skipped': []}
        
        for item in preset['settings']:
            category_id = item['category']
            cmd_name = item['command']
            action = item['action']
            
            cmd_obj = self._find_command(category_id, cmd_name)
            if not cmd_obj:
                results['skipped'].append(cmd_name)
                continue
                
            action_cmd = cmd_obj.enable_cmd if action == 'enable' else cmd_obj.disable_cmd
            if not action_cmd:
                results['skipped'].append(cmd_name)
                continue
                
            success, _, stderr = execute_adb_command(device_id, action_cmd)
            if success:
                results['success'].append(cmd_name)
            else:
                results['failed'].append({'name': cmd_name, 'error': stderr or 'Command execution failed'})
                
        return results

    def get_preset_info(self) -> List[Dict]:
        """Get all available presets for UI list"""
        presets = self._get_presets()
        return [
            {
                'id': key,
                'name': preset['name'],
                'description': preset['description'],
                'settings_count': len(preset['settings'])
            }
            for key, preset in presets.items()
        ]

    def get_backups_list(self, manufacturer: str, model: str) -> List[Dict]:
        """Get list of backups available for a device"""
        device_key = self.get_device_key(manufacturer, model)
        return self.profiles.get(device_key, {}).get('backups', [])

    def export_backup(self, manufacturer: str, model: str, backup_index: int) -> Dict:
        """Export a profile entry for external use"""
        backups = self.get_backups_list(manufacturer, model)
        if not backups:
            raise ValueError("No backups found for this device. Create a backup first.")
        if backup_index >= len(backups):
            raise ValueError(f"Backup #{backup_index} not found. Only {len(backups)} backup(s) exist.")
        return backups[backup_index]

    def delete_backup(self, manufacturer: str, model: str, backup_index: int) -> None:
        """Delete a specific backup by index"""
        device_key = self.get_device_key(manufacturer, model)
        backups = self.profiles.get(device_key, {}).get('backups', [])
        if not backups:
            raise ValueError("No backups found for this device.")
        if backup_index >= len(backups):
            raise ValueError(f"Backup #{backup_index} not found. Only {len(backups)} backup(s) exist.")
        self.profiles[device_key]['backups'].pop(backup_index)
        self._save_profiles()
        logger.info(f"Deleted backup #{backup_index} for {device_key}")

    def rename_backup(self, manufacturer: str, model: str, backup_index: int, new_name: str) -> None:
        """Set a custom display name for a backup"""
        device_key = self.get_device_key(manufacturer, model)
        backups = self.profiles.get(device_key, {}).get('backups', [])
        if not backups:
            raise ValueError("No backups found for this device.")
        if backup_index >= len(backups):
            raise ValueError(f"Backup #{backup_index} not found. Only {len(backups)} backup(s) exist.")
        self.profiles[device_key]['backups'][backup_index]['custom_name'] = new_name
        self._save_profiles()
        logger.info(f"Renamed backup #{backup_index} to '{new_name}' for {device_key}")


    def import_backup(self, profile_data: Dict, device_id: str) -> Dict:
        """Import external profile data and store it"""
        if not all(k in profile_data for k in ['manufacturer', 'model', 'settings']):
            raise ValueError("Invalid profile structure")
            
        manufacturer = profile_data['manufacturer']
        model = profile_data['model']
        device_key = self.get_device_key(manufacturer, model)
        
        if device_key not in self.profiles:
            self.profiles[device_key] = {
                'device_info': {'manufacturer': manufacturer, 'model': model},
                'backups': []
            }
            
        profile_data['device_id'] = device_id
        profile_data['backup_type'] = 'imported'
        profile_data['timestamp'] = datetime.now(timezone.utc).isoformat()
        
        self.profiles[device_key]['backups'].insert(0, profile_data)
        self.profiles[device_key]['backups'] = self.profiles[device_key]['backups'][:10]
        self._save_profiles()
        return profile_data


profile_manager = ProfileManager()
