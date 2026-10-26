"""Prove executable bytes, mapping and ELF identity cannot hide behind section metadata."""
import importlib.util,struct,tempfile,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('elf',Path(__file__).resolve().parents[1]/'elf_runtime_identity.py')
e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
def fixture():
 b=bytearray(0x300);ident=b'\x7fELF\x02\x01\x01'+bytes(9)
 struct.pack_into('<16sHHIQQQIHHHHHH',b,0,ident,2,62,1,0x400100,64,0x200,0,64,56,1,64,3,2)
 struct.pack_into('<IIQQQQQQ',b,64,1,5,0,0x400000,0x400000,0x180,0x180,0x1000)
 b[0x100:0x104]=b'CODE';b[0x190:0x1a1]=b'\0.text\0.shstrtab\0\0'
 struct.pack_into('<IIQQQQIIQQ',b,0x240,1,1,6,0x400100,0x100,4,0,0,16,0)
 struct.pack_into('<IIQQQQIIQQ',b,0x280,7,3,0,0,0x190,17,0,0,1,0)
 return b
class ELFIdentityTests(unittest.TestCase):
 def verify(self,b):
  with tempfile.TemporaryDirectory() as d:
   a=Path(d)/'a';c=Path(d)/'b';a.write_bytes(fixture());c.write_bytes(b);return e.verify(a,c)
 def test_exact_and_nonruntime_debug_changes_pass(self):
  b=fixture();self.verify(b);b[0x1c0]=1;self.verify(b)
 def test_mapped_section_redirection_cannot_hide_changed_code(self):
  b=fixture();b[0x100:0x104]=b'EVIL';b.extend(b'CODE');struct.pack_into('<Q',b,0x240+24,0x300)
  with self.assertRaises(AssertionError):self.verify(b)
 def test_mapped_padding_outside_sections_is_verified(self):
  b=fixture();b[0x120]=1
  with self.assertRaises(AssertionError):self.verify(b)
 def test_entry_protection_ident_and_segment_bounds_rejected(self):
  for offset,fmt,value in [(24,'Q',0x400101),(68,'I',7),(7,'B',3),(96,'Q',0x1000)]:
   b=fixture();struct.pack_into('<'+fmt,b,offset,value)
   with self.subTest(offset=offset),self.assertRaises(AssertionError):self.verify(b)
if __name__=='__main__':unittest.main(verbosity=2)
