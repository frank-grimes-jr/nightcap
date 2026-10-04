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
from helmet_wld_layout import reference_fields, registered_meshes, reorder
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

    def assert_originals_preserved(self,before,after):
        added=set()
        for i,name in enumerate(after.names,1):
            if '_WING_' in name or 'HE90_DMSPRITE' in name:
                added.add(i)
                if after.kind(i)==0x30:
                    ref=after.references(i)[0][1]
                    added.add(ref)
                    added.add(after.references(ref)[0][1])
        kept=[i for i in range(1,len(after.fragments)+1) if i not in added]
        self.assertEqual(len(kept),len(before.fragments))
        inverse={new:old for old,new in enumerate(kept,1)}
        for old,new in enumerate(kept,1):
            fragment=bytearray(after.fragments[new-1])
            original=before.fragments[old-1]
            if before.kind(old)==0x31 and len(fragment)!=len(original):
                self.assertEqual(len(fragment),len(original)+12)
                self.assertEqual(struct.unpack_from('<I',fragment,16)[0],
                                 struct.unpack_from('<I',original,16)[0]+3)
                self.assertTrue(all(ref in added for ref in struct.unpack_from('<3I',fragment,len(original))))
                fragment=fragment[:len(original)]
                fragment[0:4]=original[0:4]
                fragment[16:20]=original[16:20]
            for offset in reference_fields(before,old):
                ref=struct.unpack_from('<i',fragment,offset)[0]
                if ref>0:struct.pack_into('<i',fragment,offset,inverse[ref])
            self.assertEqual(bytes(fragment),before.fragments[old-1],f'original fragment {old}')

    def test_all_existing_fragments_and_strings_preserved(self):
        before,after = _Wld(self.source),_Wld(self.output)
        self.assert_originals_preserved(before,after)
        self.assertEqual(after.strings[:len(before.strings)],before.strings)

    def test_native_loader_discovers_head_from_skeleton(self):
        before,after=_Wld(self.source),_Wld(self.output)
        self.assertNotIn('ELMHE90_DMSPRITEDEF',registered_meshes(before,'ELM'))
        self.assertIn('ELMHE90_DMSPRITEDEF',registered_meshes(after,'ELM'))
        self.assertEqual([n for n in registered_meshes(after,'ELM') if 'HE90_' not in n],
                         registered_meshes(before,'ELM'))

    def test_helmet_materials_are_in_the_native_actor_palette(self):
        w=_Wld(self.output)
        first=w.by_name[registered_meshes(w,'ELM')[0]][0]
        head=w.by_name['ELMHE90_DMSPRITEDEF'][0]
        actor_palette=struct.unpack_from('<I',w.fragments[first-1],16)[0]
        head_palette=struct.unpack_from('<I',w.fragments[head-1],16)[0]
        self.assertEqual(head_palette,actor_palette)
        count=len(w.references(actor_palette))
        mesh=decode_mesh(w.fragments[head-1])
        self.assertTrue(all(0<=mat<count for _,mat in mesh['polygon_materials']))

    def test_appended_head_reproduces_original_registration_failure(self):
        w=_Wld(self.output)
        head=w.by_name['ELMHE90_DMSPRITEDEF'][0]
        order=[i for i in range(1,len(w.fragments)+1) if i!=head]+[head]
        broken=_Wld(reorder(self.output,order))
        self.assertIn('ELMHE90_DMSPRITEDEF',broken.by_name)
        self.assertNotIn('ELMHE90_DMSPRITEDEF',registered_meshes(broken,'ELM'))

    def test_fragment_relocation_rejects_unknown_kinds(self):
        raw=bytearray(self.source)
        _,parts=wld_parts(raw)
        struct.pack_into('<I',raw,parts[0][0]+4,0x777)
        with self.assertRaisesRegex(ValueError,'Unsupported WLD fragment'):
            reorder(bytes(raw),list(range(1,len(parts)+1)))

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
            self.assert_originals_preserved(before,after)
            for entry in audit:
                code=entry['code']
                self.assertIn(code+'HE90_DMSPRITEDEF',registered_meshes(after,code))
                raw_mesh=after.fragments[after.by_name[code+'HE90_DMSPRITEDEF'][0]-1]
                mesh=decode_mesh(raw_mesh)
                first=after.by_name[registered_meshes(after,code)[0]][0]
                actor_palette=struct.unpack_from('<I',after.fragments[first-1],16)[0]
                self.assertEqual(struct.unpack_from('<I',raw_mesh,16)[0],actor_palette)
                self.assertTrue(all(mat<len(after.references(actor_palette)) for _,mat in mesh['polygon_materials']))
                skeleton=before.fragments[before.by_name[code+'_HS_DEF'][0]-1]
                bone_count=struct.unpack_from('<I',skeleton,16)[0]
                self.assertTrue(all(0<=bone<bone_count for _,bone in mesh['bones']),code)
                self.assertEqual(sum(n for n,_ in mesh['bones']),len(mesh['vertices']))
                self.assertLess(len(mesh['polygons']),4096)
                self.assertGreater(entry['stock_face_triangles'],0)
                # Fit refinement must preserve the face and leave measured
                # clearance, including races whose forward axis is native +X.
                face=builder.bare_face(before,code)
                for actual,stock in zip(mesh['vertices'],face['vertices']):
                    for a,b in zip(actual,stock):
                        self.assertAlmostEqual(a,b,delta=2**(-mesh['scale']-1))
                fit=entry['lateral_fit']
                self.assertGreaterEqual(fit['shell_width'],fit['face_width']*1.08-1e-9)
                self.assertGreater(fit['width_reduction'],0)
                self.assertLessEqual(fit['width_reduction'],.25+1e-9)

    def test_camil_width_matches_classic_face_without_lowering_brow(self):
        _,audit=add_helmet(self.source,self.game,['HIM'])
        fit=audit[0]
        self.assertTrue(.22<fit['lateral_fit']['width_reduction']<.24)
        self.assertEqual(fit['fit_scale'][1:],[2.3,2.3])
        self.assertEqual(fit['fit_shift'][2],-.19)
        self.assertTrue(-.065<fit['fit_shift'][1]<-.055)
        # This retained temple vertex broke through the first narrow candidate.
        x,y,z=(-.179443359375,-.375244140625,.4755859375)
        sx,sy,sz=fit['fit_scale'];dx,dy,dz=fit['fit_shift']
        radius=((x-dx)/(.175*sx))**2+((y-dy)/(.19*sy))**2+((z-dz-.238*sz)/(.165*sz))**2
        self.assertLess(radius,.961)

    def test_missing_face_fit_material_fails_closed(self):
        w=_Wld(self.source);face=builder.bare_face(w,'HIM')
        face['polygon_materials']=[]
        with self.assertRaisesRegex(ValueError,'Missing facial fit surface'):
            builder.snug_fit(w,'HIM',face,17,[2.3]*3,[0,0,0])

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
