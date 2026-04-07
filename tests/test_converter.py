import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Mock dependencies before importing
sys.modules['OpenImageIO'] = MagicMock()
sys.modules['PyOpenColorIO'] = MagicMock()
sys.modules['numpy'] = MagicMock()
sys.modules['PIL'] = MagicMock()

# Mock LOCALAPPDATA
os.environ['LOCALAPPDATA'] = '/mock/localappdata'

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import converter

class TestConverterConvertMp4ToJpgSequence(unittest.TestCase):
    @patch('converter.os.path.exists')
    @patch('converter.os.makedirs')
    @patch('converter.subprocess.run')
    def test_convert_mp4_to_jpg_sequence_quality_100(self, mock_subprocess_run, mock_makedirs, mock_exists):
        # Setup mocks to allow the function to proceed
        mock_exists.return_value = True

        # We need to explicitly check if it's FFMPEG_EXE or video_path
        def side_effect_exists(path):
            return True
        mock_exists.side_effect = side_effect_exists

        video_path = '/mock/video/test_video.mp4'
        result = converter.convert_mp4_to_jpg_sequence(video_path, quality=100)

        self.assertTrue(result)

        # Check that FFMPEG command was called correctly
        self.assertTrue(mock_subprocess_run.called)

        # Verify arguments passed to subprocess.run
        # The command is the first argument to subprocess.run
        command = mock_subprocess_run.call_args[0][0]

        self.assertIn('-q:v', command)
        q_index = command.index('-q:v')

        # For quality=100, the ffmpeg_q_value should be 2
        # ffmpeg_q_value = max(2, min(31, 2 + (100 - 100) * 29 // 99)) = max(2, min(31, 2)) = 2
        self.assertEqual(command[q_index + 1], '2')

    @patch('converter.os.path.exists')
    @patch('converter.os.makedirs')
    @patch('converter.subprocess.run')
    def test_convert_mp4_to_jpg_sequence_quality_0(self, mock_subprocess_run, mock_makedirs, mock_exists):
        # Setup mocks to allow the function to proceed
        mock_exists.return_value = True

        def side_effect_exists(path):
            return True
        mock_exists.side_effect = side_effect_exists

        video_path = '/mock/video/test_video.mp4'
        result = converter.convert_mp4_to_jpg_sequence(video_path, quality=0)

        self.assertTrue(result)

        # Check that FFMPEG command was called correctly
        self.assertTrue(mock_subprocess_run.called)

        # Verify arguments passed to subprocess.run
        command = mock_subprocess_run.call_args[0][0]

        self.assertIn('-q:v', command)
        q_index = command.index('-q:v')

        # For quality=0, the ffmpeg_q_value should be 31
        # ffmpeg_q_value = max(2, min(31, 2 + (100 - 0) * 29 // 99)) = max(2, min(31, 2 + 29)) = max(2, min(31, 31)) = 31
        self.assertEqual(command[q_index + 1], '31')

if __name__ == '__main__':
    unittest.main()
