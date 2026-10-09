"""Export a triangulated game mesh while preserving the editable source scene."""
import bpy
import json
from pathlib import Path

out = Path(bpy.data.filepath).parent
scene = bpy.data.scenes['Nightcap Winged Paladin Helmet']
bpy.context.window.scene = scene
depsgraph = bpy.context.evaluated_depsgraph_get()
result = {'schema': 1, 'coordinates': 'X right, -Y front, Z up, meters',
          'texture': 'humch0301.bmp', 'vertices': [], 'uv': [], 'normals': [], 'triangles': []}
indices = {}
for source in bpy.data.collections['HELMET - export geometry'].objects:
    # Fine quills remain in the source sculpture. Their feather ridges survive
    # on the low-poly silhouette without adding tiny, overlapping game surfaces.
    if source.name.startswith('11 '):
        continue
    obj = source.copy(); obj.data = source.data.copy()
    scene.collection.objects.link(obj)
    if source.name.startswith('10 '):
        mod = obj.modifiers.new('Game mesh reduction', 'DECIMATE'); mod.ratio = .6
    depsgraph.update()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh(); mesh.calc_loop_triangles()
    uv = mesh.uv_layers.active
    if uv is None:
        raise ValueError('Missing EQ UV mapping: ' + source.name)
    name = source.data.materials[0].name
    material = 1 if 'Gold' in name else 2 if 'Wing' in name else 0
    for triangle in mesh.loop_triangles:
        corners = []
        for loop in triangle.loops:
            vertex = mesh.vertices[mesh.loops[loop].vertex_index]
            xyz = tuple(obj.matrix_world @ vertex.co)
            normal = tuple(mesh.corner_normals[loop].vector)
            tex = tuple(uv.data[loop].uv)
            key = (material, tuple(round(v,7) for v in xyz), tuple(round(v,6) for v in normal), tuple(round(v,7) for v in tex))
            if key not in indices:
                indices[key] = len(result['vertices'])
                result['vertices'].append(xyz); result['normals'].append(normal)
                result['uv'].append((tex[0], 1-tex[1]))
            corners.append(indices[key])
        if len(set(corners)) != 3:
            raise ValueError('Degenerate export triangle')
        result['triangles'].append([material,*corners])
    evaluated.to_mesh_clear()
    data = obj.data
    bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.meshes.remove(data)
result['triangles'].sort(key=lambda p:p[0])
if len(result['triangles']) > 4096:
    raise ValueError('Game geometry budget exceeded')
(out/'helmet-game-mesh.json').write_text(json.dumps(result,separators=(',',':')))
for obj in scene.objects: obj.select_set(False)
for obj in bpy.data.collections['HELMET - export geometry'].objects: obj.select_set(True)
bpy.ops.export_scene.fbx(filepath=str(out/'winged-paladin-helmet.fbx'),use_selection=True,
    object_types={'MESH'},apply_unit_scale=True,axis_forward='-Z',axis_up='Y',
    bake_anim=False,use_mesh_modifiers=True)
result = {'triangles':len(result['triangles']),'vertices':len(result['vertices']),
          'game_mesh':str(out/'helmet-game-mesh.json')}
