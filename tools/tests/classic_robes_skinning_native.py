"""Exercise real 32-bit d3dx9_30 bone influences from JSON fixtures; no renderer.

Input: {"models":[{"name": str, "vertex_count": int, "bone_count": int,
"runs": [[count,bone],...], "expected_by_bone": {str(bone): [indices...]},
"expect_match": bool, "seam_chest_indices": [indices...]}]}.
Omit expect_match for normal positive regression fixtures. All file operations
are limited to reading the fixture/library and writing an explicitly given report.
"""
import argparse
import ctypes as c
import hashlib
import json
from pathlib import Path


def run(fixtures):
    if c.sizeof(c.c_void_p) != 4:
        raise RuntimeError('Use 32-bit Python: this regression tests RoF2 x86 DirectX')
    system = c.WinDLL('kernel32', use_last_error=True)
    folder = c.create_unicode_buffer(32768)
    if not system.GetSystemDirectoryW(folder, len(folder)):
        raise c.WinError(c.get_last_error())
    library = Path(folder.value) / 'd3dx9_30.dll'
    dll = c.WinDLL(str(library))
    create = dll.D3DXCreateSkinInfoFVF
    create.argtypes = [c.c_uint, c.c_uint, c.c_uint, c.POINTER(c.c_void_p)]
    create.restype = c.c_long
    results = []
    for fixture in fixtures['models']:
        vertices = fixture['vertex_count']
        bones = fixture['bone_count']
        expected = {int(k): list(v) for k, v in fixture['expected_by_bone'].items()}
        if sum(n for n, _ in fixture['runs']) != vertices:
            raise ValueError('Run counts do not cover all vertices: ' + fixture['name'])
        if any(n <= 0 or b < 0 or b >= bones for n, b in fixture['runs']):
            raise ValueError('Invalid run: ' + fixture['name'])
        intended = [v for ids in expected.values() for v in ids]
        if sorted(intended) != list(range(vertices)):
            raise ValueError('Expected assignments must cover every vertex exactly once')
        if any(b < 0 or b >= bones for b in expected):
            raise ValueError('Expected bone index out of bounds')
        obj = c.c_void_p()
        hr = create(vertices, 0x112, bones, c.byref(obj))
        if hr:
            raise RuntimeError('D3DXCreateSkinInfoFVF failed: %#x' % (hr & 0xffffffff))
        vt = c.cast(obj, c.POINTER(c.POINTER(c.c_void_p))).contents
        set_bone = c.WINFUNCTYPE(c.c_long, c.c_void_p, c.c_uint, c.c_uint,
                                 c.POINTER(c.c_uint), c.POINTER(c.c_float))(vt[3])
        get_count = c.WINFUNCTYPE(c.c_uint, c.c_void_p, c.c_uint)(vt[5])
        get_bone = c.WINFUNCTYPE(c.c_long, c.c_void_p, c.c_uint,
                                 c.POINTER(c.c_uint), c.POINTER(c.c_float))(vt[6])
        release = c.WINFUNCTYPE(c.c_uint, c.c_void_p)(vt[2])
        actual = {}
        try:
            cursor = 0
            for n, bone in fixture['runs']:
                ids = (c.c_uint * n)(*range(cursor, cursor + n))
                weights = (c.c_float * n)(*([1.0] * n))
                hr = set_bone(obj, bone, n, ids, weights)
                if hr:
                    raise RuntimeError('SetBoneInfluence failed: %#x' % (hr & 0xffffffff))
                cursor += n
            for bone in range(bones):
                n = get_count(obj, bone)
                if not n:
                    continue
                ids = (c.c_uint * n)()
                weights = (c.c_float * n)()
                hr = get_bone(obj, bone, ids, weights)
                if hr:
                    raise RuntimeError('GetBoneInfluence failed: %#x' % (hr & 0xffffffff))
                if any(w != 1.0 for w in weights):
                    raise AssertionError('Native unit weights changed')
                actual[bone] = sorted(ids)
        finally:
            release(obj)
        expected = {b: sorted(ids) for b, ids in expected.items() if ids}
        lost = {b: sorted(set(ids) - set(actual.get(b, []))) for b, ids in expected.items()}
        lost = {b: ids for b, ids in lost.items() if ids}
        missing = sorted(v for ids in lost.values() for v in ids)
        matches = actual == expected
        expected_match = fixture.get('expect_match', True)
        results.append(dict(name=fixture['name'], matches=matches,
            expectation_satisfied=matches == expected_match,
            lost_vertex_count=len(missing), lost_by_bone=lost,
            lost_chest_seam_vertices=sorted(set(fixture.get('seam_chest_indices', [])) & set(missing)),
            actual_by_bone=actual))
    return dict(library=str(library), library_sha256=hashlib.sha256(library.read_bytes()).hexdigest(),
                pointer_size=c.sizeof(c.c_void_p), models=results,
                satisfied=all(r['expectation_satisfied'] for r in results))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('fixtures',type=Path)
    parser.add_argument('--report',type=Path)
    args=parser.parse_args()
    report=run(json.loads(args.fixtures.read_text()))
    if args.report:
        args.report.write_text(json.dumps(report,indent=2)+'\n')
    for model in report['models']:
        print('%s matches=%s lost=%d lost_chest_seam=%d expected=%s' % (
            model['name'],model['matches'],model['lost_vertex_count'],len(model['lost_chest_seam_vertices']),model['expectation_satisfied']))
    print('PASS' if report['satisfied'] else 'FAIL')
    return 0 if report['satisfied'] else 1


if __name__=='__main__':
    raise SystemExit(main())
