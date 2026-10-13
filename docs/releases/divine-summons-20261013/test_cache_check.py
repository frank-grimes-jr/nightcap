import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('cache_check',Path(__file__).with_name('cache_check.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)

class CacheTests(unittest.TestCase):
    def fixture(self,folder,enabled,corrupt=None):
        ids=sorted(c.OWNED | {1001});size=1332;count=max(ids)+1
        raw=bytearray(20+4*count+size*len(ids));struct.pack_into('<IIII',raw,0,len(raw)-8,count,len(ids),len(ids))
        for index,ident in enumerate(ids):
            struct.pack_into('<I',raw,16+ident*4,index);start=16+4*count+index*size
            struct.pack_into('<I',raw,start+440,ident)
            for off in (500,504):struct.pack_into('<I',raw,start+off,0 if enabled and ident in c.OWNED else 1000)
            if corrupt==ident:raw[start+700]=1
        if corrupt=='lookup':struct.pack_into('<I',raw,16+2000*4,1)
        if corrupt=='trailer':raw[-1]=1
        path=folder/('new' if enabled else 'old');path.write_bytes(raw)
        return c.verify(path,ids,{'item_size':size,'offsets':{'ID':440,'Price':500,'FixedSellPrice':504}},enabled)
    def test_only_prices_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            a=self.fixture(Path(tmp),False);b=self.fixture(Path(tmp),True)
            self.assertEqual(a['preserved_fields_sha256'],b['preserved_fields_sha256'])
            self.assertNotEqual(a['cache_sha256'],b['cache_sha256'])
            self.assertEqual(b['weapons_checked'],44)
    def test_combat_and_unrelated_corruption_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            a=self.fixture(Path(tmp),False)
            for ident in (6307,1001,'lookup','trailer'):
                b=self.fixture(Path(tmp),True,ident)
                self.assertNotEqual(a['preserved_fields_sha256'],b['preserved_fields_sha256'])

if __name__=='__main__':unittest.main(verbosity=2)
