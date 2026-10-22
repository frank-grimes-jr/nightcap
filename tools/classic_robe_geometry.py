"""Fit Classic robe skirts to native bodies without changing their skeletons.

Uses numpy for bind-pose transforms. Vertices remain rigidly bound to the target
actor's original named bones, just like the native Classic robe meshes.
"""
import copy
import math
import struct
from collections import defaultdict

import numpy as np

from build_winged_helmet_client import from_native_axes, to_native_axes, runs
from helmet_wld import decode_mesh


ANIMATION_FAMILIES = {
    'HUM': 'ELM', 'HUF': 'ELF', 'BAM': 'ELM', 'BAF': 'ELF',
    'HAM': 'ELM', 'HAF': 'ELF', 'TRM': 'OGF', 'TRF': 'OGF',
    'OGM': 'OGF', 'HOM': 'DWM', 'HOF': 'DWF', 'GNM': 'DWM', 'GNF': 'DWF',
}


def skeleton(wld, code, animation=None, frame=0, animation_wld=None):
    raw = wld.fragments[wld.by_name[code + '_HS_DEF'][0] - 1]
    flags, count, _ = struct.unpack_from('<III', raw, 12)
    pos = 24 + 12 * bool(flags & 1) + 4 * bool(flags & 2)
    bones = []
    for _ in range(count):
        name, _, track, _, n = struct.unpack_from('<i4I', raw, pos)
        children = struct.unpack_from('<' + 'I' * n, raw, pos + 20)
        pos += 20 + 4 * n
        track_wld = wld
        if animation:
            suffix = wld.string(name)[3:].removesuffix('_DAG')
            for actor in (code, ANIMATION_FAMILIES.get(code, code)):
                key = animation + actor + suffix + '_TRACK'
                source = wld if key in wld.by_name else animation_wld
                if source is not None and key in source.by_name:
                    track_wld = source
                    track = source.by_name[key][0]
                    break
        ref = struct.unpack_from('<I', track_wld.fragments[track - 1], 12)[0]
        track_data = track_wld.fragments[ref - 1]
        frames = struct.unpack_from('<I', track_data, 16)[0]
        rw, rx, ry, rz, x, y, z, scale = struct.unpack_from('<8h', track_data, 20 + 16 * (frame % frames))
        norm = math.sqrt(rw * rw + rx * rx + ry * ry + rz * rz)
        if not norm or not scale:
            raise ValueError('Invalid native bind transform')
        qw, qx, qy, qz = (v / norm for v in (rw, rx, ry, rz))
        matrix = np.eye(4)
        matrix[:3, :3] = np.array([
            [1 - 2 * (qy*qy + qz*qz), 2 * (qx*qy - qz*qw), 2 * (qx*qz + qy*qw)],
            [2 * (qx*qy + qz*qw), 1 - 2 * (qx*qx + qz*qz), 2 * (qy*qz - qx*qw)],
            [2 * (qx*qz - qy*qw), 2 * (qy*qz + qx*qw), 1 - 2 * (qx*qx + qy*qy)]
        ]) * (scale / 256)
        matrix[:3, 3] = (x / 256, y / 256, z / 256)
        bones.append((wld.string(name)[3:].removesuffix('_DAG'), matrix, children))
    transforms = {}
    def visit(index, parent):
        if index in transforms or not 0 <= index < count:
            raise ValueError('Invalid skeleton tree')
        transforms[index] = parent @ bones[index][1]
        for child in bones[index][2]:
            visit(child, transforms[index])
    visit(0, np.eye(4))
    if len(transforms) != count:
        raise ValueError('Disconnected skeleton')
    names = [b[0] for b in bones]
    if len(set(names)) != count:
        raise ValueError('Ambiguous anatomical bone names')
    return names, transforms


def mesh(wld, name):
    return decode_mesh(wld.fragments[wld.by_name[name + '_DMSPRITEDEF'][0] - 1])


def labels(model):
    return [bone for count, bone in model['bones'] for _ in range(count)]


def world_points(model, transforms, code):
    return np.array([from_native_axes(code, (transforms[bone] @ np.array([*point, 1]))[:3])
                     for point, bone in zip(model['vertices'], labels(model))])


def material_labels(wld, model):
    palette = struct.unpack_from('<I', model['header'], 16)[0]
    refs = wld.references(palette)
    return [wld.names[refs[material][1] - 1]
            for count, material in model['polygon_materials'] for _ in range(count)]


def compact(model, polygons, materials):
    used = sorted({i for polygon in polygons for i in polygon[1:]})
    mapping = {old: new for new, old in enumerate(used)}
    bone_ids = labels(model)
    for key in ('vertices', 'uv', 'normals'):
        model[key] = [model[key][i] for i in used]
    model['bones'] = runs([bone_ids[i] for i in used])
    model['polygons'] = [(flag, mapping[a], mapping[b], mapping[c]) for flag, a, b, c in polygons]
    model['polygon_materials'] = runs(materials)
    model['colors'] = []
    model['aux'] = []
    model['vertex_materials'] = []
    return model


def skirt_warp(point, lo, hi, scale, center, source_center,
               waist_scale, waist_center, source_waist_center):
    """Return the fitted position and its full derivative for normal transport."""
    t = (point[2] - lo[2]) / (hi[2] - lo[2])
    blend = max(0, min(1, (t - .5) * 2))
    # The top edge belongs to the garment below it: use the interior derivative
    # at t == 1 instead of the derivative of the unused clamped region above.
    derivative = 2 / (hi[2] - lo[2]) if .5 < t <= 1 else 0
    local_scale = scale.copy()
    local_scale[:2] = scale[:2] * (1 - blend) + waist_scale * blend
    source_xy = source_center[:2] * (1 - blend) + source_waist_center * blend
    target_xy = center[:2] * (1 - blend) + waist_center * blend
    fitted = (point - source_center) * scale + center
    fitted[:2] = (point[:2] - source_xy) * local_scale[:2] + target_xy
    jacobian = np.diag(local_scale)
    jacobian[:2, 2] = derivative * (
        -(source_waist_center - source_center[:2]) * local_scale[:2]
        + (point[:2] - source_xy) * (waist_scale - scale[:2])
        + waist_center - center[:2])
    return fitted, jacobian


def vertex_keys(model):
    """UV splits share geometry only when their rigid bone also matches."""
    return [(bone, *(round(v, 9) for v in point))
            for point, bone in zip(model['vertices'], labels(model))]


def boundary_loops(model, polygons):
    keys = vertex_keys(model)
    representatives = {key: index for index, key in enumerate(keys)}
    edges = defaultdict(list)
    for _, a, b, c in polygons:
        a, b, c = (representatives[keys[i]] for i in (a, b, c))
        for u, v in ((a, b), (b, c), (c, a)):
            edges[tuple(sorted((u, v)))].append((u, v))
    boundary = [uses[0] for uses in edges.values() if len(uses) == 1]
    following = dict(boundary)
    if len(following) != len(boundary) or set(following) != set(following.values()):
        raise ValueError('Garment boundary is not a collection of directed loops')
    loops = []
    while following:
        start = min(following)
        loop, cursor = [], start
        while cursor in following:
            loop.append(cursor)
            cursor = following.pop(cursor)
        if cursor != start:
            raise ValueError('Garment boundary is not closed')
        loops.append(loop)
    return loops


def join_waist(model, cloth_slots, transforms, code):
    """Close the torso/skirt seam with identical local coordinates and bones.

    Merely overlapping fitted surfaces leaves an open ring. Reuse the native
    torso's eight-point waist, retaining separate skirt UVs and native rigging.
    """
    materials = [mat for count, mat in model['polygon_materials'] for _ in range(count)]
    chest = [p for p, mat in zip(model['polygons'], materials)
             if mat in (cloth_slots[1], cloth_slots[2])]
    skirt = [p for p, mat in zip(model['polygons'], materials) if mat == cloth_slots[5]]
    points = world_points(model, transforms, code)
    torso = min(boundary_loops(model, chest), key=lambda loop: points[loop, 2].mean())
    rim = max(boundary_loops(model, skirt), key=lambda loop: points[loop, 2].mean())
    if len(torso) != 8 or len(rim) != 8:
        raise ValueError('Expected the native eight-edge waist rings')
    # Adjacent surfaces traverse their shared edge in opposite directions.
    opposite = list(reversed(torso))
    choices = [opposite[i:] + opposite[:i] for i in range(len(opposite))]
    paired = min(choices, key=lambda loop: np.square(points[loop] - points[rim]).sum())
    keys, bones = vertex_keys(model), labels(model)
    if any(bones[a] != bones[b] for a, b in zip(rim, paired)):
        raise ValueError('Waist rings must share the native pelvis bone')
    matches = {keys[source]: target for source, target in zip(rim, paired)}
    skirt_ids = {i for p in skirt for i in p[1:]}
    moved = {i for i in skirt_ids if keys[i] in matches}
    # Carry the rim displacement down the garment. Snapping only its top row
    # can put it below the next row and turn the connecting faces inside out.
    center = points[rim, :2].mean(axis=0)
    angles = np.arctan2(points[rim, 1] - center[1], points[rim, 0] - center[0])
    order = np.argsort(angles)
    angles = angles[order]
    if np.any(np.diff(angles) < 1e-8):
        raise ValueError('Ambiguous waist angles')
    original_rim = points[rim][order]
    displacements = (points[paired] - points[rim])[order]
    hem = points[list(skirt_ids), 2].min()
    inverses = {bone: np.linalg.inv(transform) for bone, transform in transforms.items()}
    for index in skirt_ids - moved:
        point = points[index]
        angle = math.atan2(point[1] - center[1], point[0] - center[0])
        rim_z = np.interp(angle, angles, original_rim[:, 2], period=2 * math.pi)
        weight = np.clip((point[2] - hem) / (rim_z - hem), 0, 1)
        displacement = np.array([np.interp(angle, angles, displacements[:, axis], period=2 * math.pi)
                                 for axis in range(3)])
        fitted = point + weight * displacement
        local = inverses[bones[index]] @ np.array([*to_native_axes(code, fitted), 1])
        model['vertices'][index] = local[:3].tolist()
    for index in moved:
        target = matches[keys[index]]
        model['vertices'][index] = list(model['vertices'][target])
        model['normals'][index] = list(model['normals'][target])
    # Recalculate the deformed skirt's normals while matching the unchanged
    # native torso normals at the seam. Reject any collapsed or inverted face.
    keys = vertex_keys(model)
    normals = defaultdict(lambda: np.zeros(3))
    fitted = world_points(model, transforms, code)
    for _, a, b, c in skirt:
        normal = -np.cross(fitted[b] - fitted[a], fitted[c] - fitted[a])
        original = -np.cross(points[b] - points[a], points[c] - points[a])
        if np.linalg.norm(normal) < 1e-8 or np.dot(normal, original) <= 0:
            raise ValueError('Joining the waist collapsed or inverted a skirt triangle')
        for index in (a, b, c):
            normals[keys[index]] += normal
    for index in skirt_ids - moved:
        normal = transforms[bones[index]][:3, :3].T @ np.array(to_native_axes(code, normals[keys[index]]))
        length = np.linalg.norm(normal)
        if length < 1e-8:
            raise ValueError('Invalid joined skirt normal')
        model['normals'][index] = (normal / length).tolist()
    return dict(waist_edges=len(rim), waist_vertex_copies=len(moved),
                prior_waist_max_separation=float(np.linalg.norm(points[rim] - points[paired], axis=1).max()))


def robe_mesh(target, donor_wld, code, cloth_slots):
    """Native upper body/hands/feet plus a fitted, natively rigged robe skirt."""
    donor = ('GN' if code in ('DWM', 'DWF', 'TRM', 'TRF', 'OGM', 'OGF', 'HOM', 'HOF') else 'HU') + code[-1]
    base = mesh(target, code)
    donor_robe = mesh(donor_wld, donor + '01')
    # Fit in the ordinary standing pose. Different Classic families use very
    # different bind stances; fitting spread-leg bounds produces a folded hem
    # when the actor returns to standing. Convert back to native local space.
    source_names, source_bind = skeleton(donor_wld, donor, 'P01')
    target_names, target_bind = skeleton(target, code, 'P01', animation_wld=donor_wld)
    bone_map = {i: target_names.index(name) for i, name in enumerate(source_names)
                if name in target_names}
    target_world = world_points(base, target_bind, code)
    source_world = world_points(donor_robe, source_bind, donor)
    target_materials = material_labels(target, base)
    donor_materials = material_labels(donor_wld, donor_robe)
    # A robe covers chest, upper arms and forearms. Keep target skin/hand/foot
    # UVs and local vertices exactly; hide the ordinary trousers and ankle wraps.
    replace = {'CH0001_MDF': 1, 'CH0002_MDF': 2, 'UA0001_MDF': 3,
               'FA0001_MDF': 4}
    kept, mapped = [], []
    base_palette = struct.unpack_from('<I', base['header'], 16)[0]
    slots = {target.names[ref-1]: slot for slot, (_, ref) in enumerate(target.references(base_palette))}
    for polygon, name in zip(base['polygons'], target_materials):
        part = name[3:]
        # HOF's single FT0001 texture includes both feet and toes; the other
        # actors have separate FT0002 feet below their FT0001 ankle wraps.
        if part.startswith('LG') or (part == 'FT0001_MDF' and code != 'HOF'):
            continue
        kept.append(polygon)
        mapped.append(cloth_slots[replace[part]] if part in replace else slots[name])
    result = compact(copy.deepcopy(base), kept, mapped)
    skirt_polygons = [p for p, mat in zip(donor_robe['polygons'], donor_materials) if mat == 'CLK0405_MDF']
    if not skirt_polygons:
        raise ValueError('Donor has no native robe skirt')
    skirt_vertices = sorted({i for p in skirt_polygons for i in p[1:]})
    # Fit the full lower garment in world space so shared seam vertices receive
    # the same transform even when assigned to different leg bones.
    source_skirt = source_world[skirt_vertices]
    lo, hi = source_skirt.min(axis=0), source_skirt.max(axis=0)
    lower = sorted({i for p, mat in zip(base['polygons'], target_materials)
                    if mat[3:].startswith('LG') or mat[3:] == 'FT0001_MDF' for i in p[1:]})
    target_lower = target_world[lower]
    target_lo, target_hi = target_lower.min(axis=0), target_lower.max(axis=0)
    chest = sorted({i for p, mat in zip(base['polygons'], target_materials)
                    if mat[3:].startswith('CH') for i in p[1:]})
    chest_points = target_world[chest]
    chest_bottom = chest_points[:, 2].min()
    waist = chest_points[chest_points[:, 2] <= chest_bottom + .40 * np.ptp(chest_points[:, 2])]
    waist_lo, waist_hi = waist.min(axis=0), waist.max(axis=0)
    target_hi[2] = max(target_hi[2], chest_bottom + .06 * np.ptp(target_world[:, 2]))
    # Fit near the torso before joining its exact waist ring; preserve native
    # ankle coverage and fit the top separately from the flared hem.
    scale = (target_hi - target_lo) / (hi - lo)
    scale[:2] *= 1.10
    center = (target_hi + target_lo) / 2
    source_center = (hi + lo) / 2
    source_waist = source_skirt[source_skirt[:, 2] >= hi[2] - .35 * (hi[2] - lo[2])]
    waist_scale = (waist_hi[:2] - waist_lo[:2]) / np.ptp(source_waist[:, :2], axis=0) * 1.05
    waist_center = (waist_hi[:2] + waist_lo[:2]) / 2
    source_waist_center = (source_waist[:, :2].max(axis=0) + source_waist[:, :2].min(axis=0)) / 2
    start = len(result['vertices'])
    vertex_map = {old: start + new for new, old in enumerate(skirt_vertices)}
    new_bones = labels(result)
    donor_bones = labels(donor_robe)
    inverses = {bone: np.linalg.inv(transform) for bone, transform in target_bind.items()}
    for index in skirt_vertices:
        source_bone = donor_bones[index]
        if source_bone not in bone_map:
            raise ValueError('Robe bone has no target anatomical equivalent')
        bone = bone_map[source_bone]
        fitted, jacobian = skirt_warp(source_world[index], lo, hi, scale, center,
                                     source_center, waist_scale, waist_center,
                                     source_waist_center)
        local = inverses[bone] @ np.array([*to_native_axes(code, fitted), 1])
        result['vertices'].append(local[:3].tolist())
        result['uv'].append(donor_robe['uv'][index])
        # Transform a normal through source bind, fitting and target inverse.
        normal = np.linalg.inv(source_bind[source_bone][:3, :3]).T @ np.array(donor_robe['normals'][index])
        normal = np.linalg.solve(jacobian.T, np.array(from_native_axes(donor, normal)))
        normal = target_bind[bone][:3, :3].T @ np.array(to_native_axes(code, normal))
        length = np.linalg.norm(normal)
        if length < 1e-8:
            raise ValueError('Invalid fitted normal')
        result['normals'].append((normal / length).tolist())
        new_bones.append(bone)
    result['polygons'].extend((flag, vertex_map[a], vertex_map[b], vertex_map[c])
                              for flag, a, b, c in skirt_polygons)
    result['polygon_materials'] = runs([mat for n, mat in result['polygon_materials'] for _ in range(n)]
                                      + [cloth_slots[5]] * len(skirt_polygons))
    result['bones'] = runs(new_bones)
    seam = join_waist(result, cloth_slots, target_bind, code)
    largest = max(abs(v) for point in result['vertices'] for v in point)
    result['scale'] = min(13, int(math.floor(math.log2(32760 / largest))))
    return result, dict(code=code, donor=donor, vertices=len(result['vertices']),
                        triangles=len(result['polygons']), skirt_triangles=len(skirt_polygons),
                        target_bones=len(target_names), fit_scale=scale.tolist(), **seam)
