"""Blender background preview of the actual staged WLD meshes and textures.

Usage: blender --background --python preview_classic_robes.py -- CANDIDATE OUTPUT
This is an asset inspection, not a substitute for native RoF2 validation.
"""
import sys
from pathlib import Path
import struct
import argparse
import math
import numpy as np

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from classic_model_archives import read_pfs, crypt
from classic_model_materials import _Wld
from classic_robe_geometry import mesh, skeleton, world_points, labels
from build_classic_robes import TARGETS
from build_winged_helmet_client import POSITIVE_X_FRONT, from_native_axes

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('candidate', type=Path)
parser.add_argument('output', type=Path)
parser.add_argument('--pose', default='P01')
parser.add_argument('--frame', type=int, default=0)
parser.add_argument('--angle', type=float, default=0, help='actor rotation in degrees')
parser.add_argument('--actors', nargs='+', choices=TARGETS, default=TARGETS,
                    help='inspect a smaller set at higher detail')
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
candidate, output = args.candidate, args.output
output.mkdir(parents=True, exist_ok=False)
files = read_pfs((candidate / 'global_chr.s3d').read_bytes())
wld = _Wld(files['global_chr.wld'])
scene = bpy.data.scenes.new('Classic robes candidate')
bpy.context.window.scene = scene
world = bpy.data.worlds.new('Robe studio')
world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (.035, .045, .06, 1)
world.node_tree.nodes['Background'].inputs[1].default_value = .5
scene.world = world
cache = {}


def material(index):
    while wld.references(index):
        index = wld.references(index)[0][1]
    raw = wld.fragments[index - 1]
    if wld.kind(index) != 3:
        raise ValueError('Expected native bitmap')
    size = struct.unpack_from('<H', raw, 16)[0]
    filename = crypt(raw[18:18 + size]).rstrip(b'\0').decode('ascii').lower()
    if filename in cache:
        return cache[filename]
    path = output / filename
    path.write_bytes(files[filename])
    mat = bpy.data.materials.new(filename)
    mat.use_nodes = True
    texture = mat.node_tree.nodes.new('ShaderNodeTexImage')
    texture.image = bpy.data.images.load(str(path))
    texture.interpolation = 'Closest'
    surface = mat.node_tree.nodes['Principled BSDF']
    surface.inputs['Roughness'].default_value = .8
    mat.node_tree.links.new(texture.outputs['Color'], surface.inputs['Base Color'])
    cache[filename] = mat
    return mat


for cell, code in enumerate(args.actors):
    _, transforms = skeleton(wld, code, args.pose, args.frame)
    models = [mesh(wld, code + '01'), mesh(wld, code + 'HE00')]
    points = [world_points(model, transforms, code) for model in models]
    bottom = min(p[:, 2].min() for p in points)
    height = max(p[:, 2].max() for p in points) - bottom
    for model, vertices in zip(models, points):
        normals = [from_native_axes(code, np.linalg.inv(transforms[bone][:3, :3]).T @ np.array(normal))
                   for normal, bone in zip(model['normals'], labels(model))]
        vertices = [(x / height, y / height, (z - bottom) / height)
                    for x, y, z in vertices]
        if code not in POSITIVE_X_FRONT:
            vertices = [(y, -x, z) for x, y, z in vertices]
            normals = [(y, -x, z) for x, y, z in normals]
        angle = math.radians(args.angle)
        vertices = [(x * math.cos(angle) - y * math.sin(angle),
                     x * math.sin(angle) + y * math.cos(angle), z) for x, y, z in vertices]
        normals = [Vector((x * math.cos(angle) - y * math.sin(angle),
                           x * math.sin(angle) + y * math.cos(angle), z)).normalized()
                   for x, y, z in normals]
        data = bpy.data.meshes.new(code)
        data.from_pydata(vertices, [], [(c, b, a) for _, a, b, c in model['polygons']])
        data.update()
        obj = bpy.data.objects.new(code, data)
        scene.collection.objects.link(obj)
        obj.location = (cell // 2 * 1.15 + cell % 2 * .48, 0, 0)
        refs = wld.references(struct.unpack_from('<I', model['header'], 16)[0])
        used = sorted({i for _, i in model['polygon_materials']})
        slots = {original: new for new, original in enumerate(used)}
        for index in used:
            data.materials.append(material(refs[index][1]))
        layer = data.uv_layers.new()
        for loop in data.loops:
            u, v = model['uv'][loop.vertex_index]
            # Native Classic bitmap UVs already use this vertical convention.
            # Flipping V produces visibly upside-down faces in the inspection.
            layer.data[loop.index].uv = (u, v)
        pos = 0
        for count, mat in model['polygon_materials']:
            for polygon in data.polygons[pos:pos + count]:
                polygon.material_index = slots[mat]
                polygon.use_smooth = True
            pos += count
        data.normals_split_custom_set_from_vertices(normals)
    curve = bpy.data.curves.new(code, 'FONT')
    curve.body = code
    curve.align_x = 'CENTER'
    curve.size = .07
    label = bpy.data.objects.new(code + ' label', curve)
    scene.collection.objects.link(label)
    label.rotation_euler = (1.5707963268, 0, 0)
    label.location = (cell // 2 * 1.15 + cell % 2 * .48, -.4, -.12)

camera = bpy.data.objects.new('Robe camera', bpy.data.cameras.new('Robe camera'))
scene.collection.objects.link(camera)
columns = (len(args.actors) + 1) // 2
center_x = ((columns - 1) * 1.15 + (.48 if len(args.actors) > 1 else 0)) / 2
camera.location = (center_x, -12, 2.3)
camera.rotation_euler = (Vector((center_x, 0, .47)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
camera.data.type = 'ORTHO'
camera.data.ortho_scale = max(2.0, columns * 1.15 + .25)
scene.camera = camera
for location, power in [((center_x - .65, -5, 6), 1500), ((center_x + 2.35, 2, 4), 1000)]:
    light_data = bpy.data.lights.new('Robe light', 'AREA')
    light_data.energy = power
    light_data.size = 7
    light = bpy.data.objects.new('Robe light', light_data)
    scene.collection.objects.link(light)
    light.location = location
    light.rotation_euler = (Vector((center_x, 0, .5)) - light.location).to_track_quat('-Z', 'Y').to_euler()
scene.render.engine = 'CYCLES'
scene.cycles.samples = 16
scene.render.resolution_x = max(1000, columns * 400)
scene.render.resolution_y = 700
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = str(output / 'classic-robes-front.png')
bpy.ops.wm.save_as_mainfile(filepath=str(output / 'classic-robes.blend'))
bpy.ops.render.render(write_still=True)
