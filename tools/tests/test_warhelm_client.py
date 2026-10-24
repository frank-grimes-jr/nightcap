"""Check the staged HE91 package through independent archive and graph readers."""
import struct
import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from classic_model_archives import read_pfs
from classic_model_materials import _Wld
from helmet_wld_layout import registered_meshes,reference_fields
from helmet_wld import decode_mesh
from build_winged_helmet_client import CLASSIC_ARCHIVES
from test_classic_model_pfs import read_with_native_block_capacity

ROOT=Path(__file__).resolve().parents[2]
CANDIDATE=ROOT.parent/'warhelm-client-candidate-03'

class WarhelmClient(unittest.TestCase):
    def test_preservation_registration_animation_and_native_block_capacity(self):
        for archive,codes in CLASSIC_ARCHIVES.items():
            original=read_pfs((Path('E:/Nightcap')/archive).read_bytes())
            packed=(CANDIDATE/archive).read_bytes()
            files=read_with_native_block_capacity(packed)
            self.assertEqual(files,read_pfs(packed))
            name=archive[:-4]+'.wld'
            for n,b in original.items():
                if n!=name:self.assertEqual(files[n],b,n)
            before,after=_Wld(original[name]),_Wld(files[name])
            added=set()
            def mark(index):
                if index in added:return
                added.add(index)
                for _,child in after.references(index):mark(child)
            for i,n in enumerate(after.names,1):
                if '_HE91_' in n:mark(i)
                if 'HE91_DMSPRITE' in n:added.add(i)
            kept=[i for i in range(1,len(after.fragments)+1) if i not in added]
            self.assertEqual(len(kept),len(before.fragments))
            inverse={new:old for old,new in enumerate(kept,1)}
            for old,new in enumerate(kept,1):
                raw=bytearray(after.fragments[new-1]);previous=before.fragments[old-1]
                if before.kind(old)==0x31 and len(raw)!=len(previous):
                    self.assertEqual(len(raw),len(previous)+8)
                    self.assertEqual(struct.unpack_from('<I',raw,16)[0],struct.unpack_from('<I',previous,16)[0]+2)
                    self.assertTrue(all(i in added for i in struct.unpack_from('<2I',raw,len(previous))))
                    raw=raw[:len(previous)];raw[:4]=previous[:4];raw[16:20]=previous[16:20]
                for offset in reference_fields(before,old):
                    ref=struct.unpack_from('<i',raw,offset)[0]
                    if ref>0:struct.pack_into('<i',raw,offset,inverse[ref])
                self.assertEqual(bytes(raw),previous,f'{archive} original fragment {old}')
            self.assertEqual(after.strings[:len(before.strings)],before.strings)
            for code in codes:
                heads=registered_meshes(after,code)
                self.assertIn(code+'HE90_DMSPRITEDEF',heads)
                self.assertIn(code+'HE91_DMSPRITEDEF',heads)
                mesh=decode_mesh(after.fragments[after.by_name[code+'HE91_DMSPRITEDEF'][0]-1])
                self.assertLess(len(mesh['polygons']),4096)
                skeleton=after.fragments[after.by_name[code+'_HS_DEF'][0]-1]
                self.assertTrue(all(0<=b<struct.unpack_from('<I',skeleton,16)[0] for _,b in mesh['bones']))
                material=after.by_name[code+'_HE91_M1'][0]
                reference=after.references(material)[0][1]
                animation=after.references(reference)[0][1]
                self.assertEqual(struct.unpack_from('<3I',after.fragments[animation-1],12),(8,24,150))
                self.assertEqual(len(after.references(animation)),24)

if __name__=='__main__':unittest.main()
