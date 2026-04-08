"""
Tests for ADB command execution and parsing
"""

import pytest
from unittest.mock import Mock, patch
from src.providers import execute_adb_command, check_adb_available
from src.services import get_command_state
from src.schema.models import ADBCommandModel as ADBCommand, ADBCategoryModel as ADBCategory


class TestExecuteADBCommand:
    """Tests for execute_adb_command function"""
    
    @patch('src.providers.adb_provider.subprocess.run')
    def test_execute_command_success(self, mock_run):
        """Test successful command execution"""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="success output",
            stderr=""
        )
        
        success, stdout, stderr = execute_adb_command("device123", "shell echo test")
        
        assert success is True
        assert stdout == "success output"
        assert stderr == ""
        
        # Verify command was called correctly (without shell=True)
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == "adb"
        assert "-s" in args
        assert "device123" in args
        assert "shell" in args
    
    @patch('src.providers.adb_provider.subprocess.run')
    def test_execute_command_failure(self, mock_run):
        """Test failed command execution"""
        mock_run.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="error: device not found"
        )
        
        success, stdout, stderr = execute_adb_command("invalid_device", "shell echo test")
        
        assert success is False
        assert stderr == "error: device not found"
    
    @patch('src.providers.adb_provider.subprocess.run')
    def test_execute_command_timeout(self, mock_run):
        """Test command timeout handling"""
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired("adb", 30)
        
        success, stdout, stderr = execute_adb_command("device123", "shell sleep 100")
        
        assert success is False
        assert "timed out" in stderr.lower()
    
    @patch('src.providers.adb_provider.subprocess.run')
    def test_execute_command_no_device(self, mock_run):
        """Test command execution without device ID"""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="devices list",
            stderr=""
        )
        
        success, stdout, stderr = execute_adb_command("", "devices")
        
        assert success is True
        # Verify -s flag not used when no device_id
        args = mock_run.call_args[0][0]
        assert "-s" not in args


class TestGetCommandState:
    """Tests for get_command_state function"""
    
    @patch('src.services.device_service.execute_adb_command')
    def test_parse_boolean_true(self, mock_execute):
        """Test parsing boolean true value"""
        mock_execute.return_value = (True, "1", "")
        
        state = get_command_state("device123", "shell settings get global test")
        assert state is True
        
        mock_execute.return_value = (True, "true", "")
        state = get_command_state("device123", "shell settings get global test")
        assert state is True
    
    @patch('src.services.device_service.execute_adb_command')
    def test_parse_boolean_false(self, mock_execute):
        """Test parsing boolean false value"""
        mock_execute.return_value = (True, "0", "")
        
        state = get_command_state("device123", "shell settings get global test")
        assert state is False
        
        mock_execute.return_value = (True, "false", "")
        state = get_command_state("device123", "shell settings get global test")
        assert state is False
    
    @patch('src.services.device_service.execute_adb_command')
    def test_parse_null_value(self, mock_execute):
        """Test parsing null/empty value"""
        mock_execute.return_value = (True, "null", "")
        
        state = get_command_state("device123", "shell settings get global test")
        assert state is None
        
        mock_execute.return_value = (True, "", "")
        state = get_command_state("device123", "shell settings get global test")
        assert state is None
    
    @patch('src.services.device_service.execute_adb_command')
    def test_parse_float_value(self, mock_execute):
        """Test parsing float value (animation scales)"""
        mock_execute.return_value = (True, "1.0", "")
        state = get_command_state("device123", "shell settings get global window_animation_scale")
        assert state is True
        
        mock_execute.return_value = (True, "0.0", "")
        state = get_command_state("device123", "shell settings get global window_animation_scale")
        assert state is False
    
    @patch('src.services.device_service.execute_adb_command')
    def test_parse_key_value_pair(self, mock_execute):
        """Test parsing key=value format"""
        mock_execute.return_value = (True, "mFixedPerformanceModeEnabled=true", "")
        state = get_command_state("device123", "shell dumpsys power")
        assert state is True
        
        mock_execute.return_value = (True, "mFixedPerformanceModeEnabled=false", "")
        state = get_command_state("device123", "shell dumpsys power")
        assert state is False


class TestCheckADBAvailable:
    """Tests for check_adb_available function"""
    
    @patch('src.providers.adb_provider.subprocess.run')
    def test_adb_available(self, mock_run):
        """Test when ADB is available"""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Android Debug Bridge version 1.0.41"
        )
        
        available, message = check_adb_available()
        assert available is True
        assert "version" in message.lower()
    
    @patch('adb_commands.subprocess.run')
    def test_adb_not_found(self, mock_run):
        """Test when ADB is not found"""
        mock_run.side_effect = FileNotFoundError()
        
        available, message = check_adb_available()
        assert available is False
        assert "not found" in message.lower()


class TestADBCommandClass:
    """Tests for ADBCommand class"""
    
    def test_command_creation(self):
        """Test creating an ADB command"""
        cmd = ADBCommand(
            name="Test Command",
            description="Test description",
            enable_cmd="shell settings put global test 1",
            disable_cmd="shell settings put global test 0",
            get_cmd="shell settings get global test",
            explanation="Test explanation",
            impact="high"
        )
        
        assert cmd.name == "Test Command"
        assert cmd.impact == "high"
        assert cmd.samsung_only is False
    
    def test_samsung_only_command(self):
        """Test Samsung-only command"""
        cmd = ADBCommand(
            name="Samsung Command",
            description="Samsung specific",
            enable_cmd="shell settings put secure gamesdk_version 1",
            disable_cmd="shell settings put secure gamesdk_version 0",
            explanation="Samsung only",
            samsung_only=True
        )
        
        assert cmd.samsung_only is True


class TestADBCategoryClass:
    """Tests for ADBCategory class"""
    
    def test_category_creation(self):
        """Test creating a category"""
        cmd1 = ADBCommand(
            name="Cmd1", description="Desc1",
            enable_cmd="enable", disable_cmd="disable",
            explanation="Exp1"
        )
        cmd2 = ADBCommand(
            name="Cmd2", description="Desc2",
            enable_cmd="enable", disable_cmd="disable",
            explanation="Exp2"
        )
        
        category = ADBCategory(
            id="test_category",
            name="Test Category",
            description="Test description",
            impact="medium",
            commands=[cmd1, cmd2]
        )
        
        assert category.id == "test_category"
        assert category.impact == "medium"
        assert len(category.commands) == 2

