"""Run inside Blender: editable reference-based winged Paladin helmet.

Creates its own scene; preserves all existing scenes and objects. Coordinates:
X right, -Y front, Z up; meters. Head fitting/export is a separate stage.
"""
import bpy
import bmesh
import math
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets/winged-helmet'
OUT.mkdir(parents=True, exist_ok=True)
SCENE = 'Nightcap Winged Paladin Helmet'
if SCENE in bpy.data.scenes:
    raise RuntimeError('Scene already exists; edit it rather than duplicating the build.')
scene = bpy.data.scenes.new(SCENE)
bpy.context.window.scene = scene
scene.unit_settings.system = 'METRIC'
collection = bpy.data.collections.new('HELMET - export geometry')
scene.collection.children.link(collection)
stage = bpy.data.collections.new('STUDIO - excluded from game export')
scene.collection.children.link(stage)

def material(name, color, metallic=0.0, roughness=0.45):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = roughness
    return mat

silver = material('EQ Silver - human plate', (0.58, 0.64, 0.70), 0.72, 0.36)
gold = material('EQ Gold - human plate', (0.62, 0.39, 0.07), 0.72, 0.3)
ivory = material('Silver Ivory Wing', (0.87, 0.88, 0.82), 0.27, 0.49)
shadow = material('Interior Darkened Steel', (0.022, 0.027, 0.033), 0.15, 0.64)

def mesh(name, verts, faces, mat, smooth=False):
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    if data.validate():
        raise RuntimeError('Invalid generated mesh: ' + name)
    data.update()
    obj = bpy.data.objects.new(name, data)
    collection.objects.link(obj)
    data.materials.append(mat)
    for poly in data.polygons:
        poly.use_smooth = smooth
    return obj

def tube(name, points, radius, mat, sides=6):
    verts, faces = [], []
    for i, point in enumerate(points):
        direction = Vector(points[min(i+1,len(points)-1)])-Vector(points[max(i-1,0)])
        direction.normalize()
        axis = direction.cross(Vector((0, 0, 1)))
        if axis.length < 0.01:
            axis = direction.cross(Vector((0, 1, 0)))
        axis.normalize()
        other = direction.cross(axis).normalized()
        for j in range(sides):
            a = 2*math.pi*j/sides
            verts.append(Vector(point)+radius*(axis*math.cos(a)+other*math.sin(a)))
        if i:
            for j in range(sides):
                p=(i-1)*sides+j; q=(i-1)*sides+(j+1)%sides
                faces.append((p,q,q+sides,p+sides))
    faces.extend([tuple(reversed(range(sides))),tuple(range(len(verts)-sides,len(verts)))])
    return mesh(name, verts, faces, mat, True)

N=40
# Elliptical dome, including a small flattened crown as in the menu art.
verts, faces = [], []
for row in range(10):
    a=(0.04+(math.pi/2-0.04)*row/9)
    for j in range(N):
        t=2*math.pi*j/N
        verts.append((0.175*math.sin(a)*math.sin(t),-0.19*math.sin(a)*math.cos(t),0.238+0.165*math.cos(a)))
    if row:
        for j in range(N):
            p=(row-1)*N+j; q=(row-1)*N+(j+1)%N
            faces.append((p,q,q+N,p+N))
faces.append(tuple(reversed(range(N))))
mesh('01 Silver domed crown',verts,faces,silver,True)
tube('02 Gold brow circlet',[(0.177*math.sin(2*math.pi*j/N),-0.192*math.cos(2*math.pi*j/N),0.238) for j in range(N+1)],.006,gold)

# Wraparound back and cheek plates; the front remains an actual opening.
verts,faces=[],[]
steps=32
for row in range(2):
    for j in range(steps+1):
        t=math.radians(37+286*j/steps)
        lower=.037+.015*math.cos(t)
        radius=1.0 if row==0 else 1.07
        verts.append((.175*radius*math.sin(t),-.19*radius*math.cos(t),.237 if row==0 else lower))
for j in range(steps):
    faces.append((j,j+1,j+steps+2,j+steps+1))
shell=mesh('03 Flared cheek and neck plates',verts,faces,silver,True)
solid=shell.modifiers.new('Forged plate thickness','SOLIDIFY');solid.thickness=.005
tube('04 Gold lower edge',verts[steps+1:],.005,gold)
for side,j in (('R',0),('L',steps)):
    tube('05 '+side+' face edge',[verts[j],verts[j+steps+1]],.005,gold)

# Downturned brow arches and the prominent gold nasal guard.
for sign,side in ((-1,'L'),(1,'R')):
    points=[(sign*x,y,z) for x,y,z in [(0,-.198,.245),(.035,-.195,.263),(.071,-.181,.251),(.1,-.159,.220),(.112,-.148,.18)]]
    tube('06 '+side+' arched eye surround',points,.0065,gold)
mesh('07 Gold nasal guard',[(-.018,-.200,.25),(.018,-.200,.25),(.012,-.216,.133),(0,-.225,.117),(-.012,-.216,.133),(-.009,-.207,.25),(0,-.224,.14),(.009,-.207,.25)],[(0,1,7,5),(5,7,6),(5,6,4,0),(7,1,2,6),(4,6,3),(3,6,2)],gold)
# Small gold forehead device visible in reference four.
mesh('08 Forehead heraldic device',[(0,-.173,.345),(-.011,-.182,.316),(-.023,-.180,.323),(-.01,-.186,.302),(0,-.188,.281),(.01,-.186,.302),(.023,-.180,.323),(.011,-.182,.316)],[(0,1,2,3,4,5,6,7)],gold)

def leading(t, sign):
    return Vector((sign*(.175+.086*math.sin(t*math.pi*.68)),.02+.085*t-.205*t*t,.265+.81*t))

# Swept feather blades: fine raised central quills and layered scalloped barbs.
for sign,side in ((-1,'Left'),(1,'Right')):
    tube('09 '+side+' gold wing socket',[(sign*.173,-.01,.24),(sign*.192,.003,.29),(sign*.195,.025,.33)],.012,gold)
    # Nine long, staggered feathers create the uninterrupted tall wing silhouette.
    for f in range(9):
        height=1.0-f*.077
        start=max(0, .08-f*.007)
        verts,faces=[],[]
        centers=[]
        for row in range(13):
            t=row/12
            h=start+(height-start)*t
            p=leading(h,sign)
            p.y += (.022+f*.018)*(math.sin(math.pi*t*.90))
            p.x += sign*(f*.0014)
            width=(.010+f*.0016)*math.sin(math.pi*(.08+.92*t))
            if row==12:width=.0006
            centers.append(tuple(p+Vector((sign*.004,0,0))))
            for edge in (-1,0,1):
                verts.append((p.x+sign*(.004*(1-abs(edge))),p.y+edge*width,p.z))
            if row:
                a=(row-1)*3
                faces.extend([(a,a+3,a+4,a+1),(a+1,a+4,a+5,a+2)])
        obj=mesh('10 '+side+' feather %02d'%(f+1),verts,faces,ivory,True)
        mod=obj.modifiers.new('Feather metal thickness','SOLIDIFY');mod.thickness=.002
        tube('11 '+side+' quill %02d'%(f+1),centers,.0011,silver,4)
    # Small overlapping root feathers around the gold attachment.
    for f in range(4):
        z=.26+f*.026
        x=sign*(.191+f*.006)
        mesh('12 '+side+' covert %02d'%f,[(x,-.006,z),(x+sign*.007,.006,z+.09),(x,.055,z+.055),(x-sign*.006,.055,z+.025)],[(0,1,2,3)],ivory,True)

# Cant the wings so their feather faces remain visible in the frontal reference.
for obj in collection.objects:
    if obj.name.startswith(('10 ', '11 ', '12 ')):
        sign = -1 if 'Left' in obj.name else 1
        angle = math.radians(-sign*25)
        for v in obj.data.vertices:
            x,y,z = v.co; dx = x-sign*.19; dy = y-.01
            t = max(0,min(1,(z-.265)/.81))
            v.co.x = sign*.19+dx*math.cos(angle)-dy*math.sin(angle)+sign*.07*t*t
            v.co.y = .01+dx*math.sin(angle)+dy*math.cos(angle)
    bm = bmesh.new(); bm.from_mesh(obj.data)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(obj.data); bm.free(); obj.data.update()
    if obj.name.startswith('01 '):
        inward = sum(p.normal.dot(p.center-Vector((0,0,.238))) for p in obj.data.polygons) < 0
    elif obj.name.startswith('03 '):
        inward = sum(p.normal.x*p.center.x+p.normal.y*p.center.y for p in obj.data.polygons) < 0
    else:
        inward = False
    if inward:
        bm = bmesh.new(); bm.from_mesh(obj.data)
        bmesh.ops.reverse_faces(bm, faces=list(bm.faces)); bm.to_mesh(obj.data); bm.free()
    obj.data.update()

# Reuse the unchanged stock human plate bitmap. Small coherent UV patches
# provide its silver, gold and pale metal, without painting replacement art.
image=bpy.data.images.load(str(OUT/'source-textures/humch0301.bmp'),check_existing=True)
for mat in (silver,gold,ivory):
    tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image
    mat.node_tree.links.new(tex.outputs['Color'],mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
for obj in collection.objects:
    layer=obj.data.uv_layers.new(name='Original EQ plate metal')
    mat=obj.data.materials[0]
    for loop in obj.data.loops:
        x,y,z=obj.data.vertices[loop.vertex_index].co
        if mat==gold:u,v=.025+.18*(x+.3)/.6,.012+.018*z/1.1
        elif mat==ivory:u,v=.08+.22*z/1.1,.14+.10*(y+.25)/.5
        else:u,v=.035+.25*(x+.3)/.6,.20+.20*z/1.1
        layer.data[loop.index].uv=(u,1-v)

# Visible studio, intentionally separate from export geometry.
def studio_obj(name,data,location):
    obj=bpy.data.objects.new(name,data);stage.objects.link(obj);obj.location=location;return obj
def aim(obj,target):
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
cam=studio_obj('Helmet inspection camera',bpy.data.cameras.new('Helmet inspection camera'),(1.65,-2.9,1.3))
cam.data.type='ORTHO';cam.data.ortho_scale=1.35;aim(cam,(0,0,.52));scene.camera=cam
for name,loc,power,size in [('Key',(-1.4,-2,2.3),160,2),('Fill',(1.5,-1.1,.8),100,1.8),('Rim',(0,1.4,1.8),230,1.4)]:
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size
    obj=studio_obj(name,data,loc);aim(obj,(0,0,.5))
world=bpy.data.worlds.new('Helmet charcoal studio');world.use_nodes=True
world.node_tree.nodes.get('Background').inputs[0].default_value=(.035,.047,.065,1)
world.node_tree.nodes.get('Background').inputs[1].default_value=.45;scene.world=world
scene.render.engine='CYCLES';scene.cycles.samples=32
scene.render.resolution_x=900;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX'
scene.render.image_settings.file_format='PNG'
scene.render.filepath=str(OUT/'helmet-three-quarter.png')
for obj in scene.objects:obj.select_set(False)
for obj in collection.objects:obj.select_set(True)
bpy.context.view_layer.objects.active=shell
for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D':
        area.spaces.active.region_3d.view_distance=1.9
        area.spaces.active.region_3d.view_location=(0,0,.53)
        area.spaces.active.region_3d.view_rotation=cam.rotation_euler.to_quaternion()
        area.spaces.active.shading.type='MATERIAL'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'winged-paladin-helmet.blend'))
result={'scene':scene.name,'mesh_objects':len(collection.objects),'blend':str(OUT/'winged-paladin-helmet.blend'),'status':'editable_mesh_draft_not_game_integrated'}
