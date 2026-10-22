"""Robe coverage regression against the actual Classic archives."""
import os
from collections import Counter
import json
from pathlib import Path
import struct
import sys
import unittest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from classic_model_archives import read_pfs
from classic_model_materials import _Wld
from helmet_wld_layout import registered_meshes
from helmet_wld_layout import reference_fields, mesh_block
from helmet_wld import decode_mesh
from build_winged_helmet_client import helmet_files
from build_classic_robes import robe_files, add_robes
from classic_robe_geometry import skeleton, labels, material_labels, skirt_warp, world_points

ROOT = Path(__file__).resolve().parents[2]
REFERENCE = Path('E:/EQ_Local_Dev/Client_RoF2_Dev/everquest_rof2')
TARGETS = ('BAM', 'BAF', 'ELM', 'ELF', 'HAM', 'HAF', 'DWM', 'DWF',
           'TRM', 'TRF', 'OGM', 'OGF', 'HOM', 'HOF')


class SkirtNormals(unittest.TestCase):
    def test_top_edge_uses_the_interior_one_sided_derivative(self):
        args = [np.array(v, dtype=float) for v in (
            (0, 0, 0), (1, 1, 1), (2, 3, 4), (.5, -.2, 1),
            (.5, .5, .5), (4, 1), (.2, .7), (.1, -.3))]
        point = np.array((.6, -.3, 1.0))
        a, b = np.array((1, 0, 0)), np.array((.3, -.7, -1))
        fitted, jacobian = skirt_warp(point, *args)
        normal = np.linalg.solve(jacobian.T, np.cross(a, b))
        epsilon = 1e-7
        for tangent in (a, b):
            inside, _ = skirt_warp(point + epsilon * tangent, *args)
            self.assertLess(abs(np.dot(normal, (inside - fitted) / epsilon)), 1e-5)

    def test_transported_normal_is_perpendicular_to_warped_tangents(self):
        args = [np.array(v, dtype=float) for v in (
            (0, 0, 0), (1, 1, 1), (2, 3, 4), (.5, -.2, 1),
            (.5, .5, .5), (4, 1), (.2, .7), (.1, -.3))]
        point = np.array((.6, -.3, .75))
        tangent_a, tangent_b = np.array((1, .2, .1)), np.array((.3, -.7, 1))
        normal = np.cross(tangent_a, tangent_b)
        _, jacobian = skirt_warp(point, *args)
        transported = np.linalg.solve(jacobian.T, normal)
        for tangent in (tangent_a, tangent_b):
            epsilon = 1e-6
            plus, _ = skirt_warp(point + epsilon * tangent, *args)
            minus, _ = skirt_warp(point - epsilon * tangent, *args)
            numeric = (plus - minus) / (2 * epsilon)
            self.assertLess(abs(np.dot(transported, numeric)), 1e-7)
        # The prior diagonal-only transport must not satisfy this fixture.
        self.assertGreater(abs(np.dot(normal / np.diag(jacobian), numeric)), .1)


class ClassicRobeCoverage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        helmet = json.loads((ROOT / 'assets/winged-helmet/helmet-game-mesh.json').read_bytes())
        cls.original, _ = helmet_files(REFERENCE, helmet)
        cls.generated, cls.audit = robe_files(cls.original)
        if 'NIGHTCAP_ROBE_CLIENT' in os.environ:
            client = Path(os.environ['NIGHTCAP_ROBE_CLIENT'])
            cls.generated = {name: (client / name).read_bytes() for name in cls.generated}

    def test_native_registry_contains_robe_bodies(self):
        for archive, codes in (('global_chr.s3d', TARGETS),
                               ('global4_chr.s3d', ('BAM', 'BAF'))):
            files = read_pfs(self.generated[archive])
            wld = _Wld(files[archive.replace('.s3d', '.wld')])
            for code in codes:
                with self.subTest(archive=archive, code=code):
                    self.assertIn(code + '01_DMSPRITEDEF', registered_meshes(wld, code))

    def test_original_fragments_survive_inverse_reference_relocation(self):
        for archive, codes in (('global_chr.s3d', TARGETS), ('global4_chr.s3d', ('BAM', 'BAF'))):
            name = archive.replace('.s3d', '.wld')
            old = _Wld(read_pfs(self.original[archive])[name])
            new = _Wld(read_pfs(self.generated[archive])[name])
            palettes, block_ends = set(), set()
            for code in codes:
                index = old.by_name[code + '_DMSPRITEDEF'][0]
                palettes.add(struct.unpack_from('<I', old.fragments[index - 1], 16)[0])
                block_ends.add(mesh_block(old, index)[1])
            dependency_count = len(new.fragments) - len(old.fragments) - len(codes)
            mapping, cursor = {}, 1
            for index in range(1, len(old.fragments) + 1):
                if index == min(palettes):
                    cursor += dependency_count
                mapping[index] = cursor
                cursor += 1 + (index in block_ends)
            inverse = {value: key for key, value in mapping.items()}
            for index, original in enumerate(old.fragments, 1):
                actual = bytearray(new.fragments[mapping[index] - 1])
                if index in palettes:
                    self.assertEqual(len(actual), len(original) + 20)
                    self.assertEqual(struct.unpack_from('<I', actual, 16)[0],
                                     struct.unpack_from('<I', original, 16)[0] + 5)
                    actual = actual[:len(original)]
                    actual[:4] = original[:4]
                    actual[16:20] = original[16:20]
                for offset in reference_fields(old, index):
                    ref = struct.unpack_from('<i', actual, offset)[0]
                    if ref > 0:
                        struct.pack_into('<i', actual, offset, inverse[ref])
                self.assertEqual(bytes(actual), original, (archive, index, old.names[index - 1]))
            self.assertTrue(new.strings.startswith(old.strings))
            self.assertEqual(new.trailer, old.trailer)

    def test_every_existing_texture_is_byte_identical(self):
        for archive in self.original:
            before, after = read_pfs(self.original[archive]), read_pfs(self.generated[archive])
            for name, data in before.items():
                if not name.endswith('.wld'):
                    self.assertEqual(after[name], data, (archive, name))

    def test_native_feet_survive_the_robe(self):
        before = _Wld(read_pfs(self.original['global_chr.s3d'])['global_chr.wld'])
        after = _Wld(read_pfs(self.generated['global_chr.s3d'])['global_chr.wld'])
        for code in TARGETS:
            original = decode_mesh(before.fragments[before.by_name[code + '_DMSPRITEDEF'][0] - 1])
            robe = decode_mesh(after.fragments[after.by_name[code + '01_DMSPRITEDEF'][0] - 1])
            # HOF has one combined foot texture, unlike the other actors'
            # ankle-wrap/foot split. It must retain all 46 native foot faces.
            foot = code + ('FT0001_MDF' if code == 'HOF' else 'FT0002_MDF')
            old_materials, new_materials = material_labels(before, original), material_labels(after, robe)
            with self.subTest(code=code):
                self.assertGreater(old_materials.count(foot), 0)
                self.assertEqual(new_materials.count(foot), old_materials.count(foot))

    def test_chest_and_skirt_share_a_closed_rigidly_bound_waist(self):
        # Compare serialized geometry and bone identity, not the fitter's audit.
        # Coincidence in one world pose alone can separate during animation.
        for archive, codes in (('global_chr.s3d', TARGETS), ('global4_chr.s3d', ('BAM', 'BAF'))):
            wld = _Wld(read_pfs(self.generated[archive])[archive.replace('.s3d', '.wld')])
            for code in codes:
                model = decode_mesh(wld.fragments[wld.by_name[code + '01_DMSPRITEDEF'][0] - 1])
                keys = [(bone, *point) for point, bone in zip(model['vertices'], labels(model))]
                edges = {'chest': Counter(), 'skirt': Counter()}
                directed = {'chest': set(), 'skirt': set()}
                for polygon, mat in zip(model['polygons'], material_labels(wld, model)):
                    part = 'skirt' if mat == 'CLK0405_MDF' else 'chest' if mat in ('CLK0401_MDF', 'CLK0402_MDF') else None
                    if part:
                        a, b, c = [keys[i] for i in polygon[1:]]
                        edges[part].update(tuple(sorted(edge)) for edge in ((a, b), (b, c), (c, a)))
                        directed[part].update(((a, b), (b, c), (c, a)))
                shared = set(edges['chest']) & set(edges['skirt'])
                with self.subTest(archive=archive, code=code):
                    self.assertEqual(len(shared), 8, 'Open waist: torso and skirt must share all eight native edges')
                    self.assertTrue(all(edges['chest'][edge] == edges['skirt'][edge] == 1 for edge in shared))
                    self.assertEqual(len({(b, a) for a, b in directed['chest']} & directed['skirt']), 8,
                                     'Joined surfaces must traverse waist edges in opposite directions')
                    degree = Counter(vertex for edge in shared for vertex in edge)
                    self.assertEqual(len(degree), 8)
                    self.assertTrue(all(count == 2 for count in degree.values()))
                    _, transforms = skeleton(wld, code, 'P01')
                    points = world_points(model, transforms, code)
                    seam_ids = [i for i, key in enumerate(keys) if key in degree]
                    center = points[seam_ids].mean(axis=0)
                    for polygon, mat in zip(model['polygons'], material_labels(wld, model)):
                        if mat != 'CLK0405_MDF' or not any(keys[i] in degree for i in polygon[1:]):
                            continue
                        a, b, c = points[list(polygon[1:])]
                        outward = -np.cross(b - a, c - a)
                        radial = ((a + b + c) / 3 - center)[:2]
                        self.assertGreater(float(np.dot(outward[:2], radial)), 1e-7,
                                           'Waist closure folded an adjacent skirt face inward')

    def test_cloth_material_chains_precede_their_consumers(self):
        for archive, codes in (('global_chr.s3d', TARGETS), ('global4_chr.s3d', ('BAM', 'BAF'))):
            files = read_pfs(self.generated[archive])
            wld = _Wld(files[archive.replace('.s3d', '.wld')])
            for code in codes:
                index = wld.by_name[code + '01_DMSPRITEDEF'][0]
                model = decode_mesh(wld.fragments[index - 1])
                palette = struct.unpack_from('<I', model['header'], 16)[0]
                first = wld.by_name[registered_meshes(wld, code)[0]][0]
                self.assertEqual(palette, struct.unpack_from('<I', wld.fragments[first - 1], 16)[0])
                self.assertLess(palette, index)
                refs = wld.references(palette)
                names = set(material_labels(wld, model))
                # Male Troll has no second chest panel. All five patterns must
                # be available, but only the native actor's panels are used.
                self.assertEqual([wld.names[ref - 1] for _, ref in refs[-5:]],
                                 [f'CLK04{part:02}_MDF' for part in range(1, 6)])
                self.assertTrue({f'CLK04{part:02}_MDF' for part in (1, 3, 4, 5)} <= names)
                for _, material in refs[-5:]:
                    self.assertLess(material, palette)
                    while wld.references(material):
                        parent = material
                        material = wld.references(material)[0][1]
                        self.assertLess(material, parent)

    def test_helmets_and_existing_body_variants_remain_registered(self):
        for archive in self.original:
            name = archive.replace('.s3d', '.wld')
            old = _Wld(read_pfs(self.original[archive])[name])
            new = _Wld(read_pfs(self.generated[archive])[name])
            for code in TARGETS:
                if code + '_HS_DEF' not in old.by_name:
                    continue
                self.assertEqual([n for n in registered_meshes(new, code) if n != code + '01_DMSPRITEDEF'],
                                 registered_meshes(old, code))
                self.assertIn(code + 'HE90_DMSPRITEDEF', registered_meshes(new, code))

    def test_robe_bones_use_unchanged_target_skeletons(self):
        for archive, codes in (('global_chr.s3d', TARGETS), ('global4_chr.s3d', ('BAM', 'BAF'))):
            wld = _Wld(read_pfs(self.generated[archive])[archive.replace('.s3d', '.wld')])
            for code in codes:
                names, transforms = skeleton(wld, code)
                model = decode_mesh(wld.fragments[wld.by_name[code + '01_DMSPRITEDEF'][0] - 1])
                self.assertTrue(all(0 <= bone < len(names) for bone in labels(model)))
                self.assertEqual(len(labels(model)), len(model['vertices']))
                self.assertGreater(len(model['polygons']), 200)

    def test_no_partial_or_double_application(self):
        with self.assertRaises(ValueError):
            robe_files({'global_chr.s3d': self.original['global_chr.s3d']})
        donor = read_pfs(self.generated['global_chr.s3d'])['global_chr.wld']
        with self.assertRaisesRegex(ValueError, 'already has a robe'):
            add_robes(donor, donor, ['HAM'])

    def test_generation_is_deterministic(self):
        again, report = robe_files(self.original)
        self.assertEqual(again, self.generated)
        self.assertEqual(report, self.audit)


if __name__ == '__main__':
    unittest.main()
