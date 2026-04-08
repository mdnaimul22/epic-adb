"""
API Routes - Flask Blueprints for adb-turbo
Standardized responses using Pydantic schema
"""

import logging
from flask import Blueprint, jsonify, request, send_from_directory
from src.helpers.responses import api_success, api_error
from src.providers import check_adb_available, execute_adb_command
from src.services import (
    get_connected_devices,
    get_device_manufacturer,
    get_device_location,
    get_comprehensive_device_info,
    get_command_state,
    profile_manager,
    dns_service
)
from src.core import get_categories_json, COMMAND_CATEGORIES
from src.config import settings

logger = logging.getLogger(__name__)
api_bp = Blueprint('api', __name__)


@api_bp.route('/check-adb', methods=['GET'])
def check_adb():
    """Check if ADB is installed and available"""
    available, message = check_adb_available()
    return api_success(data={'available': available, 'message': message})


@api_bp.route('/devices', methods=['GET'])
def get_devices():
    """Get list of connected ADB devices"""
    try:
        devices = get_connected_devices()
        return api_success(data={'devices': [d.model_dump() for d in devices]})
    except Exception as e:
        return api_error(f"Failed to get devices: {str(e)}", status=500)


@api_bp.route('/device-info/<device_id>', methods=['GET'])
def get_device_info(device_id):
    """Get device information and capabilities"""
    try:
        # Get comprehensive info from service
        info = get_comprehensive_device_info(device_id)
        return api_success(data=info.model_dump())
    except Exception as e:
        return api_error(f"Failed to get info: {str(e)}", status=500)


@api_bp.route('/categories', methods=['GET'])
def get_categories():
    """Get all command categories"""
    return api_success(data={'categories': get_categories_json()})


@api_bp.route('/command-states/<device_id>', methods=['GET'])
def get_command_states(device_id):
    """Get state of all commands"""
    states = {}
    for category in COMMAND_CATEGORIES:
        for cmd in category.commands:
            if cmd.get_cmd:
                states[cmd.name] = get_command_state(device_id, cmd.get_cmd)
    return api_success(data={'states': states})


@api_bp.route('/execute', methods=['POST'])
def execute_command():
    """Execute an ADB command"""
    data = request.json
    device_id = data.get('device_id')
    command = data.get('command')
    action = data.get('action', 'disable')
    
    if not device_id or not command:
        return api_error('Missing device_id or command', status=400)
    
    success, stdout, stderr = execute_adb_command(device_id, command)
    output = stdout or stderr or ("Success" if success else "Failed")
    
    if success:
        return api_success(data={'output': output, 'action': action})
    return api_error("Execution failed", details={'output': output})


# Profile Management
@api_bp.route('/profiles/backup', methods=['POST'])
def backup_profile():
    data = request.json
    device_id, manufacturer, model = data.get('device_id'), data.get('manufacturer'), data.get('model')
    
    if not all([device_id, manufacturer, model]):
        return api_error('Missing required fields', status=400)
        
    profile = profile_manager.backup_device_settings(device_id, manufacturer, model)
    return api_success(data={'profile': profile.model_dump()}, message="Backup successful")


@api_bp.route('/profiles/restore', methods=['POST'])
def restore_profile():
    data = request.json
    device_id, manufacturer, model = data.get('device_id'), data.get('manufacturer'), data.get('model')
    idx = data.get('backup_index', 0)
    
    if not all([device_id, manufacturer, model]):
        return api_error('Missing required fields', status=400)
        
    try:
        results = profile_manager.restore_device_settings(device_id, manufacturer, model, idx)
        return api_success(data={'results': results}, message="Restore completed")
    except Exception as e:
        return api_error(str(e))


@api_bp.route('/profiles/list', methods=['POST'])
def get_backups():
    data = request.json
    manufacturer, model = data.get('manufacturer'), data.get('model')
    if not manufacturer or not model:
        return api_error('Missing manufacturer or model')
        
    backups = profile_manager.get_backups_list(manufacturer, model)
    return api_success(data={'backups': backups})


@api_bp.route('/profiles/export', methods=['POST'])
def export_profile():
    data = request.json
    manufacturer, model = data.get('manufacturer'), data.get('model')
    idx = data.get('backup_index', 0)
    
    try:
        profile = profile_manager.export_backup(manufacturer, model, idx)
        return api_success(data={'profile': profile})
    except Exception as e:
        return api_error(str(e))


@api_bp.route('/profiles/import', methods=['POST'])
def import_profile():
    data = request.json
    profile, device_id = data.get('profile'), data.get('device_id')
    if not profile or not device_id:
        return api_error('Missing profile or device_id')
        
    try:
        # Import backup returns the data directly
        result = profile_manager.import_backup(profile, device_id)
        return api_success(data={'profile': result})
    except Exception as e:
        return api_error(str(e))


@api_bp.route('/profiles/apply-preset', methods=['POST'])
def apply_preset_route():
    data = request.json
    device_id, preset_name = data.get('device_id'), data.get('preset_name')
    if not device_id or not preset_name:
        return api_error('Missing device_id or preset_name')
        
    results = profile_manager.apply_preset(device_id, preset_name)
    return api_success(data={'results': results})


# DNS Management
@api_bp.route('/dns/test', methods=['GET'])
def dns_test():
    """Run DNS speed test across providers"""
    try:
        results = dns_service.run_speed_test()
        return api_success(data=results.model_dump())
    except Exception as e:
        return api_error(f"DNS test failed: {str(e)}")


@api_bp.route('/dns/apply', methods=['POST'])
def dns_apply():
    """Apply a selected DNS to a device"""
    data = request.json
    device_id = data.get('device_id')
    hostname = data.get('hostname')
    
    if not device_id or not hostname:
        return api_error('Missing device_id or hostname')
        
    success, msg = dns_service.apply_dns(device_id, hostname)
    if success:
        return api_success(message=msg)
    return api_error(msg)


@api_bp.route('/dns/reset', methods=['POST'])
def dns_reset():
    """Reset device DNS to automatic"""
    data = request.json
    device_id = data.get('device_id')

    if not device_id:
        return api_error('Missing device_id')

    success, msg = dns_service.reset_dns(device_id)
    if success:
        return api_success(message=msg)
    return api_error(msg)


@api_bp.route('/profiles/delete', methods=['POST'])
def profile_delete():
    """Delete a specific backup by index"""
    data = request.json
    manufacturer = data.get('manufacturer')
    model = data.get('model')
    backup_index = data.get('backup_index', 0)

    if not manufacturer or not model:
        return api_error('Missing manufacturer or model')

    try:
        profile_manager.delete_backup(manufacturer, model, backup_index)
        return api_success(message=f'Backup {backup_index + 1} deleted')
    except ValueError as e:
        return api_error(str(e), status_code=400)


@api_bp.route('/profiles/rename', methods=['POST'])
def profile_rename():
    """Rename a backup with a custom name"""
    data = request.json
    manufacturer = data.get('manufacturer')
    model = data.get('model')
    backup_index = data.get('backup_index', 0)
    new_name = data.get('new_name', '').strip()

    if not manufacturer or not model:
        return api_error('Missing manufacturer or model')
    if not new_name:
        return api_error('new_name cannot be empty')

    try:
        profile_manager.rename_backup(manufacturer, model, backup_index, new_name)
        return api_success(message=f'Backup renamed to "{new_name}"')
    except ValueError as e:
        return api_error(str(e), status_code=400)
