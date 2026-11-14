import json,mmap,sys,struct,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[2]/'docs/items/classic-raid-focus'))
import release
from catalog import changes

class CacheValidation(unittest.TestCase):
    def test_layout_and_unrelated_field_guard(self):
        release.m={'layout':{'size':24,'ID':0,'Worn':4,'Focus':12}}
        old_values=(-1,0,0,0,-1,0,0,0)
        release.stock={1:({},old_values,(-1,0,0,0,2343,6,0,0))}
        def cache(spell,kind):
            record=bytearray(24);struct.pack_into('<IiB',record,0,1,-1,0);struct.pack_into('<iB',record,12,spell,kind)
            return struct.pack('<IIIIII',44,2,1,1,0xffffffff,0)+record+b'\0'*4
        with tempfile.TemporaryDirectory() as temp:
            a,b=(Path(temp)/n for n in ('original','candidate'))
            a.write_bytes(cache(-1,0));b.write_bytes(cache(2343,6))
            self.assertEqual(release.cache_check(a,b)['changed'],1)
            buf=bytearray(b.read_bytes());buf[46]=23;b.write_bytes(buf)
            with self.assertRaises(AssertionError):release.cache_check(a,b)

if __name__=='__main__':unittest.main()
