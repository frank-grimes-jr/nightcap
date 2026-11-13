import struct
import tempfile
import unittest
from pathlib import Path
import release

class ATKCache(unittest.TestCase):
    def test_exact_attack_delta_only(self):
        def put(path,rows):
            count=6;size=12;buf=bytearray(20+4*count+size*len(rows))
            struct.pack_into('<IIII',buf,0,len(buf)-8,count,len(rows),len(rows))
            for i in range(count):struct.pack_into('<I',buf,16+i*4,0xffffffff)
            for idx,(i,atk,extra) in enumerate(rows):
                struct.pack_into('<I',buf,16+i*4,idx);struct.pack_into('<Iii',buf,16+count*4+size*idx,i,atk,extra)
            path.write_bytes(buf)
        layout={'size':12,'ID':0,'Attack':4}
        with tempfile.TemporaryDirectory() as tmp:
            a,b=Path(tmp)/'a',Path(tmp)/'b';put(a,[(1,0,1),(4,50,0),(5,8,1)])
            put(b,[(4,53,0),(1,0,1),(5,8,1)])
            self.assertEqual(release.compare(a,b,layout,{4:(50,53)})['byte_identical'],2)
            for bad in ([(1,0,1),(4,52,0),(5,8,1)],[(1,0,1),(4,53,1),(5,8,1)],[(1,1,1),(4,53,0),(5,8,1)],[(1,0,1),(3,53,0),(5,8,1)]):
                put(b,bad)
                with self.assertRaises(AssertionError):release.compare(a,b,layout,{4:(50,53)})
if __name__=='__main__':unittest.main()
