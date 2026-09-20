import unittest,tempfile,hashlib
from pathlib import Path
from unittest.mock import patch
import client_ecommons_hub as hub
from client_ecommons_hub import recall_spell,recall_strings
from test_client_gameplay_assets import spell

class HubClient(unittest.TestCase):
 def template(self):
  f=spell(3134,f16=0,f17=0,f83=1,f86=83,f98=6).strip().split('^');f[87:98]=['254']*11
  return ('^'.join(f)+'\r\n').encode()
 def test_recall_preserves_original_and_is_native_teleport(self):
  old=self.template();a=dict(x=-190,y=-1725,z=3.75,heading=0);out=recall_spell(old,a)
  self.assertTrue(out.startswith(old));f=out.splitlines()[-1].decode().split('^')
  self.assertEqual(f[0:2],['42604','Ancient Attunement']);self.assertEqual(f[20:24],['-1725','-190','4','0']);self.assertEqual(f[13:16],['5000','1500','600000']);self.assertEqual(f[104:120],['255']*16);self.assertEqual(recall_spell(out,a),out)
  with self.assertRaises(ValueError):recall_spell(out.replace(b'42604^Ancient Attunement',b'42604^Other'),a)
 def test_strings_preserve_unrelated_type_and_reject_collision(self):
  old=b'22200^6^Warlord description^0\r\n9^1^Other^0\r\n';out=recall_strings(old)
  self.assertTrue(out.startswith(old));self.assertIn(b'22200^1^Ancient Attunement^0',out);self.assertEqual(recall_strings(out),out)
  with self.assertRaises(ValueError):recall_strings(old+b'22200^1^Collision^0\n')
 def test_import_map_and_pinned_archives(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);(root/'maps').mkdir();(root/'ecommons_chr.txt').write_bytes(b'1\ntar,tar_chr\n');(root/'dbstr_us.txt').write_bytes(b'22200^6^Keep^0\n');(root/'ecommons_assets.txt').write_bytes(b'existing_obj\n');(root/'maps/ecommons_3.txt').write_bytes(b'P 1, 2, 3, 0, 0, 0, 1, My_note\n')
   pins={name:hashlib.sha256(name.encode()).hexdigest() for name in hub.PINNED}
   for name in pins:(root/name).write_bytes(name.encode())
   with patch.object(hub,'PINNED',pins):
    files=hub.hub_files(root);self.assertTrue(files['maps/ecommons_3.txt'].startswith((root/'maps/ecommons_3.txt').read_bytes()));self.assertEqual(files['ecommons_assets.txt'],b'existing_obj\npoknowledge_obj\n')
    for name,data in files.items():(root/name).write_bytes(data)
    self.assertEqual(hub.hub_files(root),files)
    (root/'nektulos.s3d').write_bytes(b'wrong')
    with self.assertRaises(ValueError):hub.hub_files(root)
if __name__=='__main__':unittest.main()
