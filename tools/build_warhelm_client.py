"""Convert the pinned Live Warhelm into a separate Classic HE91 staging package.

No installed/reference client writes. Reuses the Camil native mesh/palette writer.
Structural validation is not visible in-game acceptance.
"""
import argparse,hashlib,io,json,math,struct
from pathlib import Path
from PIL import Image
from classic_model_archives import read_pfs,write_pfs
from classic_model_materials import _Wld
from helmet_wld_layout import registered_meshes
from build_winged_helmet_client import add_helmet,CLASSIC_ARCHIVES,from_native_axes

SOURCE_SHA1='fd99da9998c8f13a592912e4e476261bc714a583'

def source_mesh(blob):
    if hashlib.sha1(blob).hexdigest()!=SOURCE_SHA1:raise ValueError('Unreviewed source EQG')
    files=read_pfs(blob);b=files['it99100.mod']
    if b[:4]!=b'EQGM':raise ValueError('Expected EQGM')
    version,size,nm,nv,nt,nb=struct.unpack_from('<6I',b,4)
    if (version,nm,nv,nt,nb)!=(3,2,556,652,106):raise ValueError('Source model drift')
    strings=b[28:28+size];p=28+size
    def text(offset):return strings[offset:].split(b'\0')[0].decode('ascii')
    for i in range(nm):
        mid,name,shader,count=struct.unpack_from('<4I',b,p);p+=16
        if mid!=i:raise ValueError('Material ordering drift')
        p+=12*count
    game={'vertices':[],'normals':[],'uv':[],'triangles':[],
          'material_frames':[['ncashenbase.bmp'],[f'ncashen{i:02d}.bmp' for i in range(1,25)]],
          'frame_ms':150,'replace_head':True}
    # EQG front +X -> shared helmet front -Y. Normalize the body below the horns
    # to the Camil fitting coordinate frame; the native writer fits each actor.
    for i in range(nv):
        x,y,z,nx,ny,nz,color,u,v,u2,v2=struct.unpack_from('<6fI4f',b,p);p+=44
        game['vertices'].append([y*.45,-x*.45,(z-2.0231101513)*.36])
        n=[ny/.45,-nx/.45,nz/.36];length=math.sqrt(sum(q*q for q in n))
        if not length:raise ValueError('Zero normal')
        # EQG DDS coordinates have the opposite vertical origin from the BMP
        # textures used here. See Zaela/EQGModelImporter src/viewer.cpp's DDS
        # TCoords.Y conversion. Preserve wrapping U; flip V at this boundary.
        game['normals'].append([q/length for q in n]);game['uv'].append([u,1-v])
    for i in range(nt):
        a,c,d,material,flags=struct.unpack_from('<5I',b,p);p+=20
        if material>=2 or max(a,c,d)>=nv:raise ValueError('Bad source triangle')
        va,vb,vc=[game['vertices'][v] for v in (a,c,d)]
        e=[vb[k]-va[k] for k in range(3)];f=[vc[k]-va[k] for k in range(3)]
        cross=[e[1]*f[2]-e[2]*f[1],e[2]*f[0]-e[0]*f[2],e[0]*f[1]-e[1]*f[0]]
        if sum(cross[k]*game['normals'][a][k] for k in range(3))<0:c,d=d,c
        game['triangles'].append([material,a,c,d])
    frames=files['animated_flame_helmet_c_01.txt'].decode().splitlines()
    assert frames[:2]==['24','150']
    textures={}
    names=['anim_base_helm_c.dds']+[f'animated_flame_helmet_c_{i:02d}.dds' for i in range(1,25)]
    targets=game['material_frames'][0]+game['material_frames'][1]
    for source,target in zip(names,targets):
        output=io.BytesIO();Image.open(io.BytesIO(files[source])).convert('RGB').save(output,format='BMP');textures[target]=output.getvalue()
    return game,textures

def fit_head(w,code,face,bone,scale,shift):
    labels=[b for count,b in face['bones'] for _ in range(count)]
    points=[from_native_axes(code,p) for p,b in zip(face['vertices'],labels) if b==bone]
    low=[min(p[k] for p in points) for k in range(3)];high=[max(p[k] for p in points) for k in range(3)]
    # No crown-specific narrowing: this full-face skull has a different contour.
    scale[:]=[(high[0]-low[0])*1.15/.35,(high[1]-low[1])*1.15/.38,(high[2]-low[2]+.05)/.403]
    shift[:]=[(high[0]+low[0])/2,(high[1]+low[1])/2,low[2]]
    return {'method':'native head bounds; visible race/face fit QA pending','face_bounds':[low,high]}

def build(client,eqg,output):
    client=client.resolve();output=output.resolve()
    if output==client or client in output.parents or output.exists():raise ValueError('Use a new staging folder outside the client')
    game,textures=source_mesh(eqg.read_bytes())
    result={'status':'structurally validated candidate; not installed; in-game QA pending','material':91,'source_eqg_sha1':SOURCE_SHA1,'archives':{}}
    archive_bytes={}
    for archive,codes in CLASSIC_ARCHIVES.items():
        raw=(client/archive).read_bytes();files=read_pfs(raw);name=archive[:-4]+'.wld';before=_Wld(files[name])
        # Pair with the installed Camil asset; preserve every HE90 mesh.
        for code in codes:
            if code+'HE90_DMSPRITEDEF' not in before.by_name:raise ValueError('Matching Camil client baseline required')
        old_meshes={code:set(registered_meshes(before,code)) for code in codes}
        modified,audit=add_helmet(files[name],game,codes,91,fit_head)
        after=_Wld(modified)
        # Full-global loading retains stock cross-race bitmap dependencies.
        # Validate typed closure, not the separate per-actor import prefix rule.
        seen=set()
        def visit(index):
            if index in seen:return
            seen.add(index)
            for _,child in after.references(index):visit(child)
        for code in codes:
            for palette in after.palettes(code):visit(palette)
        for code in codes:
            if not old_meshes[code]<=set(registered_meshes(after,code)):raise AssertionError('Existing head variant lost')
        for n,b in textures.items():
            if n in files and files[n]!=b:raise ValueError('Texture identity collision')
        original=dict(files);files[name]=modified;files.update(textures)
        packed=write_pfs(files)
        assert read_pfs(packed)==files
        assert all(files[n]==b for n,b in original.items() if n!=name)
        archive_bytes[archive]=packed
        result['archives'][archive]={'source_sha256':hashlib.sha256(raw).hexdigest(),'output_sha256':hashlib.sha256(packed).hexdigest(),'models':audit,'retained_head_variants':{k:sorted(v) for k,v in old_meshes.items()}}
    output.mkdir(parents=True)
    for n,b in archive_bytes.items():(output/n).write_bytes(b)
    (output/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    (output/'helmet-game-mesh.json').write_text(json.dumps(game)+'\n')
    print(json.dumps({'output':str(output),'actors':sum(len(a['models']) for a in result['archives'].values()),'material':91}))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--client',type=Path,required=True);p.add_argument('--eqg',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();build(a.client,a.eqg,a.output)
