import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import subprocess

# Mock PyOpenColorIO and OpenImageIO and other heavy dependencies to prevent ImportError when importing converter
sys.modules['PyOpenColorIO'] = MagicMock()
sys.modules['OpenImageIO'] = MagicMock()
sys.modules['numpy'] = MagicMock()
sys.modules['PIL'] = MagicMock()
sys.modules['PIL.Image'] = MagicMock()

# Add src to sys.path to import converter
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

# Mock os.environ BEFORE importing converter to avoid errors
with patch.dict(os.environ, {'LOCALAPPDATA': 'mock_local_appdata'}):
    import converter

class TestConvertVidResize(unittest.TestCase):

    @patch('converter.os.path.exists')
    @patch('converter.subprocess.run')
    def test_convert_vid_resize_success(self, mock_subprocess_run, mock_path_exists):
        # Setup mocks
        # First call is for video_path, second is for FFMPEG_EXE
        mock_path_exists.side_effect = lambda path: path in ['test_video.mp4', converter.FFMPEG_EXE]

        # Call function
        result = converter.convert_vid_resize('test_video.mp4', 800)

        # Assertions
        self.assertTrue(result)
        mock_subprocess_run.assert_called_once()
        called_args = mock_subprocess_run.call_args[0][0]
        self.assertIn(converter.FFMPEG_EXE, called_args)
        self.assertIn('-i', called_args)
        self.assertIn('test_video.mp4', called_args)
        self.assertIn('-vf', called_args)
        self.assertIn('scale=800:-2', called_args)
        self.assertIn('test_video_resized_800px.mp4', called_args)

    @patch('converter.os.path.exists')
    def test_convert_vid_resize_file_not_found(self, mock_path_exists):
        mock_path_exists.return_value = False

        result = converter.convert_vid_resize('missing_video.mp4', 800)

        self.assertFalse(result)
        mock_path_exists.assert_called_once_with('missing_video.mp4')

    @patch('converter.os.path.exists')
    def test_convert_vid_resize_invalid_width(self, mock_path_exists):
        mock_path_exists.return_value = True # Video file exists

        # Test negative width
        result_neg = converter.convert_vid_resize('test_video.mp4', -100)
        self.assertFalse(result_neg)

        # Test zero width
        result_zero = converter.convert_vid_resize('test_video.mp4', 0)
        self.assertFalse(result_zero)

    @patch('converter.os.path.exists')
    def test_convert_vid_resize_ffmpeg_missing(self, mock_path_exists):
        # Video file exists, but FFMPEG doesn't
        mock_path_exists.side_effect = lambda path: path == 'test_video.mp4'

        result = converter.convert_vid_resize('test_video.mp4', 800)

        self.assertFalse(result)

    @patch('converter.os.path.exists')
    @patch('converter.subprocess.run')
    def test_convert_vid_resize_subprocess_error(self, mock_subprocess_run, mock_path_exists):
        mock_path_exists.side_effect = lambda path: path in ['test_video.mp4', converter.FFMPEG_EXE]
        # Setup mock to raise CalledProcessError
        mock_subprocess_run.side_effect = subprocess.CalledProcessError(1, 'cmd', output='error', stderr='error details')

        result = converter.convert_vid_resize('test_video.mp4', 800)

        self.assertFalse(result)

    @patch('converter.os.path.exists')
    @patch('converter.subprocess.run')
    def test_convert_vid_resize_general_exception(self, mock_subprocess_run, mock_path_exists):
        mock_path_exists.side_effect = lambda path: path in ['test_video.mp4', converter.FFMPEG_EXE]
        # Setup mock to raise generic Exception
        mock_subprocess_run.side_effect = Exception("Unexpected failure")

        result = converter.convert_vid_resize('test_video.mp4', 800)

        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
