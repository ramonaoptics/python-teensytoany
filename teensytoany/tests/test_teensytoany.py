import pytest
from unittest.mock import Mock, patch, MagicMock
from teensytoany import TeensyToAny


def test_project_import():
    """Test that the package can be imported correctly."""
    import teensytoany
    assert teensytoany.__version__
    assert teensytoany.TeensyToAny


class TestTeensyToAny:
    """Test class for TeensyToAny functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_serial = Mock()
        self.mock_serial.read_until.return_value = b"0\n"
        self.mock_serial.timeout = 0.205

    @patch('teensytoany.teensytoany.Serial')
    @patch('teensytoany.teensytoany.TeensyToAny.device_serial_number_pairs')
    def test_nop_command(self, mock_device_pairs, mock_serial_class):
        """Test that the nop command works correctly."""
        mock_device_pairs.return_value = [('/dev/ttyACM0', '123456')]
        mock_serial_class.return_value = self.mock_serial
        
        teensy = TeensyToAny(open=False)
        teensy._serial = self.mock_serial
        teensy._version = "0.0.1"
        
        teensy.nop()
        
        self.mock_serial.write.assert_called_with(b"nop\n")
        self.mock_serial.read_until.assert_called_once()

    @patch('teensytoany.teensytoany.Serial')
    @patch('teensytoany.teensytoany.TeensyToAny.device_serial_number_pairs')
    def test_oversized_input_handling(self, mock_device_pairs, mock_serial_class):
        """Test that oversized input (>2k bytes) is handled correctly by the firmware."""
        mock_device_pairs.return_value = [('/dev/ttyACM0', '123456')]
        mock_serial_class.return_value = self.mock_serial
        
        teensy = TeensyToAny(open=False)
        teensy._serial = self.mock_serial
        teensy._version = "0.0.1"
        
        # Create a command that exceeds the 2k buffer limit
        oversized_command = "nop " + "x" * 2500
        
        # Mock the serial response to simulate ENOMEM error (12)
        self.mock_serial.read_until.return_value = b"12\n"
        
        # The firmware should return ENOMEM (12) for oversized input
        with pytest.raises(RuntimeError, match="Responded with Error Code 12"):
            teensy._ask(oversized_command)
        
        # Verify the command was written to serial
        self.mock_serial.write.assert_called_with((oversized_command + '\n').encode('utf-8'))

    @patch('teensytoany.teensytoany.Serial')
    @patch('teensytoany.teensytoany.TeensyToAny.device_serial_number_pairs')
    def test_normal_command_works(self, mock_device_pairs, mock_serial_class):
        """Test that normal commands work correctly."""
        mock_device_pairs.return_value = [('/dev/ttyACM0', '123456')]
        mock_serial_class.return_value = self.mock_serial
        
        teensy = TeensyToAny(open=False)
        teensy._serial = self.mock_serial
        teensy._version = "0.0.1"
        
        # Mock successful response
        self.mock_serial.read_until.return_value = b"0\n"
        
        result = teensy._ask("nop")
        assert result is None
        
        self.mock_serial.write.assert_called_with(b"nop\n")

    @patch('teensytoany.teensytoany.Serial')
    @patch('teensytoany.teensytoany.TeensyToAny.device_serial_number_pairs')
    def test_buffer_size_limits(self, mock_device_pairs, mock_serial_class):
        """Test that commands near the buffer limit are handled correctly."""
        mock_device_pairs.return_value = [('/dev/ttyACM0', '123456')]
        mock_serial_class.return_value = self.mock_serial
        
        teensy = TeensyToAny(open=False)
        teensy._serial = self.mock_serial
        teensy._version = "0.0.1"
        
        # Test with command just under the limit (2048 bytes - some overhead)
        large_command = "nop " + "x" * 2000
        self.mock_serial.read_until.return_value = b"0\n"
        
        result = teensy._ask(large_command)
        assert result is None
        
        # Test with command at the limit
        limit_command = "nop " + "x" * 2040
        self.mock_serial.read_until.return_value = b"0\n"
        
        result = teensy._ask(limit_command)
        assert result is None
