"""Run in Blender to inspect decoded, packaged heads in a separate scene."""
import sys, json, struct, math, importlib
from pathlib import Path
import bpy
from mathutils import Vector,Matrix,Quaternion

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from classic_model_archives import read_pfs,crypt
from classic_model_materials import _Wld
from helmet_wld import decode_mesh
import build_winged_helmet_client
importlib.reload(build_winged_helmet_client)
from build_winged_helmet_client import CLASSIC_RACES,from_native_axes

OUT=ROOT.parent/'warhelm-preview'
(OUT/'source-textures').mkdir(parents=True,exist_ok=True)
candidate=Path(globals().get('CANDIDATE',ROOT.parent/'warhelm-client-candidate-03'))
name=globals().get('SCENE_NAME','Packaged helmet - 24 original race fits warhelm')
render_path=Path(globals().get('RENDER_PATH',ROOT.parent.parent/'outputs/warhelm-classic-fit-sheet.png'))
if name in bpy.data.scenes:raise ValueError('Fit scene already exists')
scene=bpy.data.scenes.new(name);bpy.context.window.scene=scene
world=bpy.data.worlds.new(name);world.use_nodes=True
world.node_tree.nodes['Background'].inputs[0].default_value=(.04,.05,.07,1)
world.node_tree.nodes['Background'].inputs[1].default_value=.7;scene.world=world
sources={}
for archive in ['global_chr.s3d','global4_chr.s3d']:
    files=read_pfs((candidate/archive).read_bytes())
    sources[archive]=(_Wld(files[archive[:-4]+'.wld']),files)
cache={}
def material(w,files,index):
    name=w.names[index-1]
    refs=w.references(index)
    while refs:
        index=refs[0][1];refs=w.references(index)
    raw=w.fragments[index-1]
    if w.kind(index)!=3:raise ValueError('Expected bitmap')
    length=struct.unpack_from('<H',raw,16)[0]
    filename=crypt(raw[18:18+length]).rstrip(b'\0').decode('ascii').lower()
    if filename in cache:return cache[filename]
    path=OUT/'source-textures'/filename
    if not path.exists():path.write_bytes(files[filename])
    mat=bpy.data.materials.new('Native '+filename);mat.use_nodes=True
    nodes=mat.node_tree.nodes;tex=nodes.new('ShaderNodeTexImage')
    tex.image=bpy.data.images.load(str(path),check_existing=True);tex.interpolation='Closest'
    bsdf=nodes['Principled BSDF'];bsdf.inputs['Roughness'].default_value=.6
    mat.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])
    cache[filename]=mat;return mat

def bind_transforms(w,code):
    raw=w.fragments[w.by_name[code+'_HS_DEF'][0]-1]
    flags,count,_=struct.unpack_from('<III',raw,12)
    pos=24+12*bool(flags&1)+4*bool(flags&2);bones=[]
    for bone in range(count):
        _,_,track,_,n=struct.unpack_from('<i4I',raw,pos);pos+=20
        children=struct.unpack_from('<'+'I'*n,raw,pos);pos+=4*n
        ref=struct.unpack_from('<I',w.fragments[track-1],12)[0]
        rw,rx,ry,rz,x,y,z,scale=struct.unpack_from('<8h',w.fragments[ref-1],20)
        local=Matrix.Translation(Vector((x/256,y/256,z/256))) @ Quaternion((rw,rx,ry,rz)).normalized().to_matrix().to_4x4() @ Matrix.Scale(scale/256,4)
        bones.append((local,children))
    result={}
    def visit(bone,parent):
        local,children=bones[bone];result[bone]=parent@local
        for child in children:visit(child,result[bone])
    visit(0,Matrix.Identity(4));return result

codes=[c for pair in CLASSIC_RACES.values() for c in pair]
for cell,code in enumerate(codes):
    archive='global_chr.s3d'
    w,files=sources[archive];raw=w.fragments[w.by_name[code+'HE91_DMSPRITEDEF'][0]-1]
    m=decode_mesh(raw)
    bind=bind_transforms(w,code);head=max(m['bones'])[1];inverse=bind[head].inverted()
    labels=[bone for n,bone in m['bones'] for _ in range(n)]
    vertices=[from_native_axes(code,inverse@bind[bone]@Vector(p)) for p,bone in zip(m['vertices'],labels)]
    low=min(p[2] for p in vertices);height=max(p[2] for p in vertices)-low
    # Normalize only the inspection display; native vertices remain unchanged.
    vertices=[(p[0]/height,p[1]/height,(p[2]-low)/height) for p in vertices]
    data=bpy.data.meshes.new(code);data.from_pydata(vertices,[],[(c,b,a) for _,a,b,c in m['polygons']]);data.update()
    obj=bpy.data.objects.new(code+' packaged HE91',data);scene.collection.objects.link(obj)
    obj.location=(cell%7*1.1,0,-(cell//7)*1.3)
    refs=w.references(struct.unpack_from('<I',raw,16)[0]);used=sorted({i for _,i in m['polygon_materials']})
    lookup={mat:i for i,mat in enumerate(used)}
    for mat in used:data.materials.append(material(w,files,refs[mat][1]))
    layer=data.uv_layers.new()
    for loop in data.loops:
        u,v=m['uv'][loop.vertex_index];layer.data[loop.index].uv=(u,1-v)
    offset=0
    for count,mat in m['polygon_materials']:
        for poly in data.polygons[offset:offset+count]:poly.material_index=lookup[mat];poly.use_smooth=True
        offset+=count
    text=bpy.data.curves.new(code+' label','FONT');text.body=code;text.align_x='CENTER';text.size=.085
    label=bpy.data.objects.new(code+' label',text);scene.collection.objects.link(label)
    label.rotation_euler=(math.pi/2,0,0);label.location=(obj.location.x,-.5,obj.location.z-.11)
camera=bpy.data.objects.new('Fitting sheet camera',bpy.data.cameras.new('Fitting sheet camera'))
scene.collection.objects.link(camera);camera.location=(3.3,-15,-1.3)
camera.rotation_euler=(Vector((3.3,0,-1.3))-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.type='ORTHO';camera.data.ortho_scale=8.2;scene.camera=camera
for location,power,size in [((2,-8,6),2000,8),((6,-4,-1),1000,6)]:
    data=bpy.data.lights.new('Fit studio','AREA');data.energy=power;data.size=size
    light=bpy.data.objects.new('Fit studio',data);scene.collection.objects.link(light);light.location=location
    light.rotation_euler=(Vector((3,0,-1))-light.location).to_track_quat('-Z','Y').to_euler()
scene.render.engine='CYCLES';scene.cycles.samples=16
scene.render.resolution_x=2100;scene.render.resolution_y=1400;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.filepath=str(render_path)
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(render_path.with_suffix('.blend')))
bpy.ops.render.render(write_still=True)
result={'render':scene.render.filepath,'status':'packaged geometry preview; native game check pending'}
