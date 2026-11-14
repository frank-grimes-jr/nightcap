import struct
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from cache import TARGETS, compare
from stage import unused_inverse

LAYOUT = [1332,440,552,592,612,808,1004,1088]

class ReleaseChecks(unittest.TestCase):
    def test_exact_changes_and_unrelated_mutation(self):
        with TemporaryDirectory() as temp:
            root=Path(temp)
            left,right=root/'left',root/'right'
            left.mkdir()
            right.mkdir()
            size,ident,cast1,charges,cast2,click,label,spell_size=LAYOUT
            keys=max(TARGETS)+1
            ids=[100,*TARGETS]
            slots=bytearray(b'\xff'*(4*keys))
            records=bytearray(size*len(ids))
            for ix,key in enumerate(ids):
                struct.pack_into('<I',slots,4*key,ix)
                struct.pack_into('<I',records,ix*size+ident,key)
                struct.pack_into('<i',records,ix*size+click,-1)
            header=struct.pack('<4I',12+4*keys+len(records),keys,len(ids),len(ids))
            def items():return header+slots+records+bytes(4)
            (left/'items').write_bytes(items())
            for ix,key in enumerate(ids[1:],start=1):
                sid,title=TARGETS[key]
                start=ix*size
                for fmt,where,value in [('i',cast1,2000),('h',charges,-1),('I',cast2,2000)]:
                    struct.pack_into('<'+fmt,records,start+where,value)
                struct.pack_into('<i3B',records,start+click,sid,4,1,1)
                records[start+label:start+label+len(title)]=title.encode()
            (right/'items').write_bytes(items())
            count=max(s[0] for s in TARGETS.values())+1
            spells=bytearray(struct.pack('<II',4+count*spell_size,count))+bytearray(count*spell_size+4)
            (left/'spells').write_bytes(spells)
            for sid,title in TARGETS.values():
                start=8+sid*spell_size
                struct.pack_into('<I',spells,start,sid)
                spells[start+4:start+4+len(title)]=title.encode()
            (right/'spells').write_bytes(spells)
            self.assertEqual(compare(left,right,LAYOUT)['items']['unchanged'],1)
            records[0]=1
            (right/'items').write_bytes(items())
            with self.assertRaisesRegex(AssertionError,'Unrelated item'):
                compare(left,right,LAYOUT)

    def test_exact_inverse_refuses_saved_buffs(self):
        inverse=unused_inverse().decode()
        self.assertIn('FROM character_buffs WHERE ((`spell_id` IN (44379,44380))) THEN',inverse.replace(')) THEN',') THEN'))
        self.assertNotIn('NOT EXISTS (SELECT 1 FROM spells_new s WHERE s.id=character_buffs',inverse)
        self.assertIn('ROLLBACK; RESIGNAL;',inverse)
        self.assertIn('DELETE FROM db_str WHERE id IN (44379,44380) AND type=6;',inverse)

if __name__=='__main__':
    unittest.main()
