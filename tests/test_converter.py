import unittest
import os
import sys
import unittest.mock
from PIL import Image
import tempfile
import shutil

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

sys.modules['win32com'] = unittest.mock.MagicMock()
sys.modules['win32com.client'] = unittest.mock.MagicMock()
sys.modules['pythoncom'] = unittest.mock.MagicMock()
sys.modules['win32gui'] = unittest.mock.MagicMock()

with unittest.mock.patch.dict('os.environ', {'LOCALAPPDATA': 'C:\\MockedAppData'}):
    import converter

class TestConverter(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.image_paths = []
        for i in range(3):
            path = os.path.join(self.temp_dir, f"test_img_{i}.jpg")
            img = Image.new('RGB', (100, 100), color=(255, 0, 0))
            img.save(path)
            self.image_paths.append(path)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_create_contact_sheet_negative_padding(self):
        result = converter.create_contact_sheet(self.image_paths, padding=-1000)
        self.assertFalse(result)

    def test_create_contact_sheet_zero_padding(self):
        result = converter.create_contact_sheet(self.image_paths, output_filename=os.path.join(self.temp_dir, "contact_sheet_zero.jpg"), padding=0)
        self.assertTrue(result)
        out_path = os.path.join(self.temp_dir, "contact_sheet_zero.jpg")
        self.assertTrue(os.path.exists(out_path))

    def test_create_contact_sheet_large_padding(self):
        result = converter.create_contact_sheet(self.image_paths, output_filename=os.path.join(self.temp_dir, "contact_sheet_large.jpg"), padding=1000)
        self.assertTrue(result)
        out_path = os.path.join(self.temp_dir, "contact_sheet_large.jpg")
        self.assertTrue(os.path.exists(out_path))

if __name__ == '__main__':
    unittest.main()
