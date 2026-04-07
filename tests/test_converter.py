import unittest
from unittest.mock import patch
import os
import sys

# Mock LOCALAPPDATA
os.environ['LOCALAPPDATA'] = 'dummy_path'

# Add src to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

# Mock OIIO and OCIO before importing converter
sys.modules['OpenImageIO'] = unittest.mock.MagicMock()
sys.modules['PyOpenColorIO'] = unittest.mock.MagicMock()

import converter

class TestConverter(unittest.TestCase):
    @patch('converter.os.path.exists')
    def test_upscale_image_realesrgan_exe_not_found(self, mock_exists):
        # Mock os.path.exists to return False specifically for the executable path
        def side_effect(path):
            if path == converter.REALESRGAN_EXE:
                return False
            return True
        mock_exists.side_effect = side_effect

        # Call the function
        result = converter.upscale_image_realesrgan(["dummy_image.png"])

        # Verify the result is False
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
