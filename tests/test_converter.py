import unittest
from unittest.mock import patch, MagicMock
import os
import subprocess
import io
import sys

# Mock sys.modules before importing the module under test
import sys
sys.modules['PyOpenColorIO'] = MagicMock()
sys.modules['OpenImageIO'] = MagicMock()

# Setup os.environ before importing src.converter
os.environ['LOCALAPPDATA'] = r"C:\Users\TestUser\AppData\Local"

# Add the 'src' directory to sys.path so we can import modules from it
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from src import converter

class TestConverter(unittest.TestCase):
    @patch('src.converter.subprocess.run')
    @patch('src.converter.utils.find_sequence_files')
    @patch('src.converter.os.path.exists')
    def test_convert_sequence_to_mp4_called_process_error(self, mock_exists, mock_find_sequence, mock_subprocess_run):
        # Arrange
        # We need mock_exists to return True for the FFMPEG_EXE check,
        # but the function doesn't check output path existence inside the try block
        # We also need it to let other checks pass, so just returning True is fine.
        mock_exists.return_value = True

        mock_find_sequence.return_value = (['mock_file1.png'], 1, 'mock_file%d.png')

        # Create a mock CalledProcessError
        cmd = [
            converter.FFMPEG_EXE,
            '-framerate', '25',
            '-start_number', '1',
            '-i', 'mock_file%d.png',
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-y',
            os.path.join(os.path.dirname('mock_input/file1.png'), 'mock_file.mp4')
        ]

        error = subprocess.CalledProcessError(
            returncode=1,
            cmd=cmd,
            output="Mocked stdout error",
            stderr="Mocked stderr error"
        )
        mock_subprocess_run.side_effect = error

        # Capture print statements
        captured_output = io.StringIO()
        original_stdout = sys.stdout
        sys.stdout = captured_output

        try:
            # Act
            result = converter.convert_sequence_to_mp4('mock_input/file1.png', framerate=25)

            # Assert
            self.assertFalse(result)
            output = captured_output.getvalue()

            self.assertIn("Error during FFmpeg execution:", output)
            self.assertIn(f"Command: {' '.join(cmd)}", output)
            self.assertIn("Return Code: 1", output)
            self.assertIn("Output: Mocked stdout error", output)
        finally:
            # Restore stdout
            sys.stdout = original_stdout

if __name__ == '__main__':
    unittest.main()
