"""Native-archive preservation and malformed mesh regression checks."""
import json
import hashlib
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from classic_model_archives import read_pfs, wld_parts
from classic_model_materials import _Wld, validate_materials
from helmet_wld import decode_mesh
from build_winged_helmet_client import add_helmet, HEAD_MATERIAL
import build_winged_helmet_client as builder

ROOT = Path(__file__).resolve().parents[2]
CLIENT = Path(r'E:/EQ_Local_Dev/Client_RoF2_Dev/everquest_rof2')

class HelmetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = read_pfs((CLIENT/'global_chr.s3d').read_bytes())
        cls.source = cls.files['global_chr.wld']
        cls.game = json.loads((ROOT/'assets/winged-helmet/helmet-game-mesh.json').read_text())
        cls.output,cls.audit = add_helmet(cls.source,cls.game,['ELM'])

    def test_all_existing_fragments_and_strings_preserved(self):
        before,after = _Wld(self.source),_Wld(self.output)
        self.assertEqual(after.fragments[:len(before.fragments)],before.fragments)
        self.assertEqual(after.strings[:len(before.strings)],before.strings)

    def test_native_mesh_indices_groups_and_head_attachment(self):
        w = _Wld(self.output)
        name = f'ELMHE{HEAD_MATERIAL:02d}_DMSPRITEDEF'
        r = w.fragments[w.by_name[name][0]-1]
        m = decode_mesh(r)
        self.assertEqual(m['bones'],[(len(m['vertices']),17)])
        self.assertEqual(len(m['polygons']),53+len(self.game['triangles']))
        self.assertEqual(sum(n for n,_ in m['polygon_materials']),len(m['polygons']))
        self.assertEqual(len(m['uv']),len(m['vertices']))
        self.assertEqual(len(m['aux']),0)
        # This archive uses the native full-global loader. Its original player
        # palettes deliberately share other races' bitmaps; the per-actor import
        # prefix filter does not apply here. Verify typed dependency closure.
        palette=struct.unpack_from('<I',r,16)[0]
        seen=set()
        def visit(index):
            if index in seen:return
            seen.add(index)
            for _,target in w.references(index):visit(target)
        visit(palette)
        self.assertEqual(len(w.references(palette)),20)
        for _,material in w.references(palette)[-3:]:
            self.assertTrue(w.names[material-1].startswith('ELM_WING_'))

    def test_reserved_head_collision_fails_closed(self):
        with self.assertRaisesRegex(ValueError,'already exists'):
            add_helmet(self.output,self.game,['ELM'])

    def test_every_classic_race_and_gender_has_explicit_mapping(self):
        self.assertEqual(set(builder.CLASSIC_RACES), set(range(1,13)))
        self.assertEqual(builder.CLASSIC_RACES[5], ('HIM','HIF'))
        self.assertEqual(builder.CLASSIC_RACES[4], ('ELM','ELF'))
        self.assertEqual(len({c for pair in builder.CLASSIC_RACES.values() for c in pair}),24)

    def test_all_race_meshes_preserve_originals_and_bind_to_valid_bones(self):
        for archive,codes in builder.CLASSIC_ARCHIVES.items():
            raw=(CLIENT/archive).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(),builder.SOURCE_DIGESTS[archive])
            source=read_pfs(raw)[archive[:-4]+'.wld']
            output,audit=add_helmet(source,self.game,codes)
            before,after=_Wld(source),_Wld(output)
            self.assertEqual(after.fragments[:len(before.fragments)],before.fragments)
            for entry in audit:
                code=entry['code']
                mesh=decode_mesh(after.fragments[after.by_name[code+'HE90_DMSPRITEDEF'][0]-1])
                skeleton=before.fragments[before.by_name[code+'_HS_DEF'][0]-1]
                bone_count=struct.unpack_from('<I',skeleton,16)[0]
                self.assertTrue(all(0<=bone<bone_count for _,bone in mesh['bones']),code)
                self.assertEqual(sum(n for n,_ in mesh['bones']),len(mesh['vertices']))
                self.assertLess(len(mesh['polygons']),4096)
                self.assertGreater(entry['stock_face_triangles'],0)

    def test_small_race_fits_rotate_front_to_native_positive_x(self):
        self.assertEqual(builder.to_native_axes('DWM',(0,-1,0)),(1,0,0))
        self.assertEqual(builder.to_native_axes('HIM',(0,-1,0)),(0,-1,0))

    def test_reusable_archive_generation_matches_reviewed_candidate(self):
        files, audit = builder.helmet_files(CLIENT, self.game)
        candidate = json.loads((ROOT/'assets/winged-helmet/candidate.json').read_bytes())
        self.assertEqual(set(files), {'global_chr.s3d', 'global4_chr.s3d'})
        for name, raw in files.items():
            self.assertEqual(hashlib.sha256(raw).hexdigest(),
                             candidate['archives'][name]['output_sha256'])
            self.assertEqual(audit[name]['output_sha256'],
                             candidate['archives'][name]['output_sha256'])

    def test_nonfinite_attributes_rejected(self):
        broken=dict(self.game);broken['uv']=[list(v) for v in broken['uv']]
        broken['uv'][0][0]=float('nan')
        with self.assertRaisesRegex(ValueError,'Nonfinite'):
            add_helmet(self.source,broken,['HIM'])

    def test_broken_geometry_rejected(self):
        broken=dict(self.game);broken['triangles']=[[0,0,1,65535]]
        with self.assertRaisesRegex(ValueError,'index'):
            add_helmet(self.source,broken,['ELM'])

    def test_native_mesh_truncation_rejected(self):
        w=_Wld(self.source);r=w.fragments[w.by_name['ELMHE00_DMSPRITEDEF'][0]-1]
        with self.assertRaises(ValueError):decode_mesh(r[:-20])

if __name__=='__main__':unittest.main()
