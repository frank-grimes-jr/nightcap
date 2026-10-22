"""Model delivery must supply geometry in both classic and modern modes."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from classic_model_archives import write_pfs
from client_classic_models import global_model_files, PLAN


class WaypointModelTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.client = Path(self.temp.name)
        self.raw = write_pfs({'crs.mod': b'EQGMfixture', 'crs.lay': b'fixture'})
        (self.client / 'crs.eqg').write_bytes(self.raw)
        self.models = [{'code': 'crs', 'archive': 'crs.eqg',
                        'sha256': hashlib.sha256(self.raw).hexdigest()}]
        self.native = b'2\nliz,liz_chr\nskn,skn_chr\n'
        (self.client / 'native_chr.txt').write_bytes(self.native)
        self.modern = {'source': 'native_chr.txt',
                       'sha256': hashlib.sha256(self.native).hexdigest()}

    def build(self):
        return global_model_files(self.client, self.models, self.modern)

    def test_additive_import_and_lossless_asset(self):
        files = self.build()
        self.assertEqual(files, {'crs.eqg': self.raw,
                                'nightcap_modern_chr.txt': b'3\nliz,liz_chr\nskn,skn_chr\ncrs,crs\n'})
        self.assertEqual((self.client / 'crs.eqg').read_bytes(), self.raw)
        self.assertEqual((self.client / 'native_chr.txt').read_bytes(), self.native)
        self.assertEqual(len(list(self.client.iterdir())), 2)

    def test_corrupt_asset_refused_before_packaging(self):
        (self.client / 'crs.eqg').write_bytes(self.raw + b'changed')
        with self.assertRaisesRegex(ValueError, 'Unsupported global model'):
            self.build()

    def test_missing_asset_refused(self):
        (self.client / 'crs.eqg').unlink()
        with self.assertRaises(FileNotFoundError):
            self.build()

    def test_wrong_model_refused_even_with_matching_hash(self):
        raw = write_pfs({'other.mod': b'EQGMfixture'})
        (self.client / 'crs.eqg').write_bytes(raw)
        self.models[0]['sha256'] = hashlib.sha256(raw).hexdigest()
        with self.assertRaisesRegex(ValueError, 'Missing global model geometry'):
            self.build()

    def test_duplicate_codes_refused(self):
        with self.assertRaisesRegex(ValueError, 'Duplicate global model'):
            global_model_files(self.client, self.models * 2, self.modern)

    def test_native_import_drift_is_not_silently_dropped(self):
        (self.client / 'native_chr.txt').write_bytes(self.native + b'custom,custom_chr\n')
        with self.assertRaisesRegex(ValueError, 'Unsupported modern import list'):
            self.build()

    def test_wrong_native_count_refused(self):
        raw = b'3\nliz,liz_chr\n'
        (self.client / 'native_chr.txt').write_bytes(raw)
        self.modern['sha256'] = hashlib.sha256(raw).hexdigest()
        with self.assertRaisesRegex(ValueError, 'Invalid modern import count'):
            self.build()

    def test_reviewed_plan_uses_exact_crystal(self):
        self.assertEqual(json.loads(PLAN.read_bytes())['global_models'], [{
            'code': 'crs', 'archive': 'crs.eqg',
            'sha256': '0a06d4b41d49843b40518105b50057a50d1abb07147e10fb3769135ee1223f6b'}])


if __name__ == '__main__':
    unittest.main()
