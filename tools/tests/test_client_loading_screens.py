import hashlib
import tempfile
import unittest
from pathlib import Path
import sys

from PIL import Image, ImageChops, ImageStat

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from client_loading_screens import ART, SOURCES, generate


class LoadingScreens(unittest.TestCase):
    def test_all_native_slots_use_approved_art_and_preserve_full_frame(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'gallery'
            audit = generate(root)
            expected = {'resources/loadscreen.jpg'} | {
                f'uifiles/default/loadscreens/loadscreen{i:02}.jpg' for i in range(1, 56)}
            self.assertEqual(set(audit['files']), expected)
            self.assertEqual(set(f['source'] for f in audit['files'].values()), set(SOURCES))
            seen = set()
            for name, record in audit['files'].items():
                raw = (root/name).read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(), record['sha256'])
                self.assertEqual(len(raw), record['size'])
                with Image.open(root/name) as actual, Image.open(ART/record['source']) as source:
                    actual.load()
                    self.assertEqual((actual.format, actual.mode, actual.size), ('JPEG', 'RGB', source.size))
                    self.assertFalse(actual.info.get('progressive', False))
                    # Whole-frame pixel comparison catches cropping, stretch, missing art or bad mapping.
                    error = ImageStat.Stat(ImageChops.difference(actual, source.convert('RGB'))).mean
                    self.assertLess(max(error), 3)
                seen.add(record['sha256'])
            self.assertEqual(len(seen), 10)
            self.assertEqual(audit['files']['resources/loadscreen.jpg']['source'], SOURCES[-1])
            with self.assertRaises(ValueError):
                generate(root)


if __name__ == '__main__':
    unittest.main()
