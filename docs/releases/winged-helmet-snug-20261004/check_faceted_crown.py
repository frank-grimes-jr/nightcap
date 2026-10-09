"""Read-only geometric audit of all 26 snug helmet fits.

Checks actual triangular crown half-spaces, not the fitting ellipsoid.
Writes only the explicitly supplied JSON evidence path; never edits archives.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import sys


def sub(a, b):
    return tuple(x-y for x, y in zip(a, b))


def dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def planes(vertices, triangles):
    result = []
    for a, b, c in triangles:
        p, q, r = [vertices[i] for i in (a, b, c)]
        normal = cross(sub(q, p), sub(r, p))
        length = math.sqrt(dot(normal, normal))
        if length < 1e-12:
            continue
        normal = tuple(v/length for v in normal)
        if dot(normal, sub(p, (0, 0, .238))) < 0:
            normal = tuple(-v for v in normal)
        result.append((normal, dot(normal, p)))
    return result


def clip_crown(points):
    """Clip a convex face triangle against the crown's base z=.238."""
    output = []
    previous = points[-1]
    for point in points:
        was_in, is_in = previous[2] >= .238, point[2] >= .238
        if was_in != is_in:
            t = (.238-previous[2])/(point[2]-previous[2])
            output.append(tuple(previous[k]+t*(point[k]-previous[k]) for k in range(3)))
        if is_in:
            output.append(point)
        previous = point
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--client', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--result', type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.repo/'tools'))
    from classic_model_archives import read_pfs
    from classic_model_materials import _Wld
    from helmet_wld import decode_mesh
    from build_winged_helmet_client import bare_face, from_native_axes
    mesh_bytes = (args.repo/'assets/winged-helmet/helmet-game-mesh.json').read_bytes()
    game = json.loads(mesh_bytes)
    audit = json.loads((args.candidate/'helmet-audit.json').read_bytes())
    assert hashlib.sha256(mesh_bytes).hexdigest() == audit['mesh_sha256']
    dome = []
    for material, a, b, c in game['triangles']:
        points = [game['vertices'][i] for i in (a, b, c)]
        if material == 0 and all(p[2] >= .238-1e-7 and
                abs((p[0]/.175)**2+(p[1]/.19)**2+((p[2]-.238)/.165)**2-1) < 1e-5
                for p in points):
            dome.append((a, b, c))
    source_planes = planes(game['vertices'], dome)
    assert len(source_planes) > 700, 'Unexpected source crown topology'
    result = dict(mesh_sha256=audit['mesh_sha256'], crown_planes=len(source_planes),
                  tolerance_source_units=1e-5, models=[], limitations=[
                      'Checks retained head-bone HE0001 face triangles above crown base.',
                      'Does not check ears, animated jaw, feathers or other armor intersections.',
                      'Geometric containment does not replace native visual acceptance.'])
    for archive, record in audit['archives'].items():
        stock_bytes = (args.client/archive).read_bytes()
        candidate_bytes = (args.candidate/archive).read_bytes()
        assert hashlib.sha256(stock_bytes).hexdigest() == record['source_sha256']
        assert hashlib.sha256(candidate_bytes).hexdigest() == record['output_sha256']
        wld_name = archive[:-4]+'.wld'
        stock = _Wld(read_pfs(stock_bytes)[wld_name])
        candidate = _Wld(read_pfs(candidate_bytes)[wld_name])
        for fit in record['models']:
            code = fit['code']
            face = bare_face(stock, code)
            head = decode_mesh(candidate.fragments[candidate.by_name[code+'HE90_DMSPRITEDEF'][0]-1])
            start = len(face['vertices'])
            assert len(head['vertices']) == start+len(game['vertices'])
            def local(point):
                p = from_native_axes(code, point)
                return tuple((p[k]-fit['fit_shift'][k])/fit['fit_scale'][k] for k in range(3))
            actual_vertices = [local(p) for p in head['vertices']]
            actual_planes = planes(actual_vertices[start:], dome)
            refs = stock.references(struct.unpack_from('<I', face['header'], 16)[0])
            labels = [bone for n, bone in face['bones'] for _ in range(n)]
            triangles = []
            offset = 0
            for count, material in face['polygon_materials']:
                if stock.names[refs[material][1]-1] == code+'HE0001_MDF':
                    triangles.extend(p[1:] for p in face['polygons'][offset:offset+count]
                                     if all(labels[v] == fit['head_bone'] for v in p[1:]))
                offset += count
            checks = {}
            for name, vertices, boundaries in (
                    ('unquantized_fit', [local(p) for p in face['vertices']], source_planes),
                    ('encoded_candidate', actual_vertices, actual_planes)):
                points = [p for tri in triangles for p in clip_crown([vertices[i] for i in tri])]
                assert points, 'No crown-level face surface: '+code
                maximum = max(dot(normal, p)-distance for p in points for normal, distance in boundaries)
                checks[name] = dict(clipped_vertices=len(points), maximum_signed_plane_distance=maximum,
                                    passed=maximum <= 1e-5)
            result['models'].append(dict(archive=archive, code=code, checks=checks))
    result['passed'] = all(c['passed'] for row in result['models'] for c in row['checks'].values())
    assert len(result['models']) == 26
    args.result.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(passed=result['passed'], models=len(result['models']),
                         crown_planes=len(source_planes), result=str(args.result))))
    if not result['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
