"""Add a numbered helmet to each Classic actor's native mesh block.

Produces a separate staging archive. The source RoF2 client is always read-only.
Material 90 is below the native Velious remapping range (240..255).
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct

from classic_model_archives import crypt, read_pfs, write_pfs, wld_parts
from classic_model_materials import _Wld
from helmet_wld import decode_mesh, encode_mesh
from helmet_wld_layout import mesh_block, registered_meshes, reorder

HEAD_MATERIAL = 90
SOURCE_DIGESTS = {
    'global_chr.s3d': '6de89b8bea0c4ed387f8ef92774018a44a35c1fb440aa0a3052c56ce680a2eed',
    'global4_chr.s3d': 'a828808b84d44c3abbcfff66aac8706ad18b37bc058b4f95a162e1abb9b0819b',
}
# Native race registry, verified against the pinned RoF2 RegisterActor calls.
# ELM is Wood Elf; HIM is High Elf (including Camil, race 5).
CLASSIC_RACES = {
    1:('HUM','HUF'), 2:('BAM','BAF'), 3:('ERM','ERF'), 4:('ELM','ELF'),
    5:('HIM','HIF'), 6:('DAM','DAF'), 7:('HAM','HAF'), 8:('DWM','DWF'),
    9:('TRM','TRF'), 10:('OGM','OGF'), 11:('HOM','HOF'), 12:('GNM','GNF'),
}
CLASSIC_ARCHIVES = {
    'global_chr.s3d': tuple(c for pair in CLASSIC_RACES.values() for c in pair),
    'global4_chr.s3d': ('BAM','BAF'),
}
POSITIVE_X_FRONT = {'DWM','DWF','TRM','TRF','OGM','OGF','HOM','HOF','GNM','GNF'}


def to_native_axes(code, point):
    x,y,z = point
    return (-y,x,z) if code in POSITIVE_X_FRONT else (x,y,z)


def from_native_axes(code, point):
    x,y,z = point
    return (y,-x,z) if code in POSITIVE_X_FRONT else (x,y,z)


def runs(values):
    result=[]
    for value in values:
        if result and result[-1][1]==value:
            result[-1]=(result[-1][0]+1,value)
        else:result.append((1,value))
    return result


def bare_face(w, code):
    """Retain face geometry and animated jaw, excluding separate hair bones.

    Stock plate models sometimes use face textures on horns and armor fins, so
    filtering their materials alone is not a reliable way to extract a face.
    """
    # Most plate heads provide the correctly exposed face without skin under
    # the old metal shell. Barbarian horns use skin materials. The closed
    # Gnome helmet removes too much face. Use bare heads
    # for those exceptions and let the fitted shell cover them.
    plate=code not in {'BAM','GNM'}
    index=w.by_name[code+('HE03' if plate else 'HE00')+'_DMSPRITEDEF'][0]
    m=decode_mesh(w.fragments[index-1])
    refs=w.references(struct.unpack_from('<I',m['header'],16)[0])
    labels=[bone for n,bone in m['bones'] for _ in range(n)]
    skeleton=w.fragments[w.by_name[code+'_HS_DEF'][0]-1]
    flags,count,_=struct.unpack_from('<III',skeleton,12)
    pos=24+12*bool(flags&1)+4*bool(flags&2);hair=set()
    for bone in range(count):
        _,_,track,_,children=struct.unpack_from('<i4I',skeleton,pos)
        pos+=20+4*children
        if w.names[track-1].startswith(code+'HA'):hair.add(bone)
    polygons=[];materials=[];offset=0
    for count,mat in m['polygon_materials']:
        for polygon in m['polygons'][offset:offset+count]:
            skin=not plate or w.names[refs[mat][1]-1].startswith(code+'HE00')
            if skin and not any(labels[v] in hair for v in polygon[1:]):
                polygons.append(polygon);materials.append(mat)
        offset+=count
    if not polygons:raise ValueError('No stock bare face for '+code)
    used=sorted({v for p in polygons for v in p[1:]});remap={v:i for i,v in enumerate(used)}
    for key in ('vertices','uv','normals'):
        m[key]=[m[key][i] for i in used]
    m['polygons']=[(flag,remap[a],remap[b],remap[c]) for flag,a,b,c in polygons]
    m['polygon_materials']=runs(materials);m['bones']=runs([labels[i] for i in used])
    m['aux']=[];m['colors']=[];m['vertex_materials']=[]
    return m


def snug_fit(w, code, face, head_bone, scale, shift):
    """Fit to the exposed face, not ears, hair or ornamental stock head fins.

    Preserve the established brow height and shell depth. Leave 8% lateral clearance
    around the skin surface and limit the first refinement to 25% per actor.
    This also moves the wing roots inward with their supporting shell.
    """
    refs=w.references(struct.unpack_from('<I',face['header'],16)[0])
    labels=[bone for n,bone in face['bones'] for _ in range(n)]
    vertices=set();offset=0
    for count,material in face['polygon_materials']:
        if w.names[refs[material][1]-1]==code+'HE0001_MDF':
            vertices.update(v for polygon in face['polygons'][offset:offset+count]
                            for v in polygon[1:] if labels[v]==head_bone)
        offset+=count
    if not vertices:raise ValueError('Missing facial fit surface for '+code)
    points=[from_native_axes(code,face['vertices'][v]) for v in vertices]
    xs=[p[0] for p in points]
    face_width=max(xs)-min(xs)
    old_width=.35*scale[0]
    width=min(old_width,max(old_width*.75,face_width*1.08))
    scale[0]=width/.35
    shift[0]=(max(xs)+min(xs))/2
    # Narrowing an elliptical dome reduces its clearance at the forehead.
    # Translate it just enough to contain the retained upper facial surface;
    # 0.96 leaves room for the faceted crown and native vertex quantization.
    # These radii and brow height match the Blender source dome.
    previous_depth_shift=shift[1]
    low,high=-math.inf,math.inf
    for x,y,z in points:
        if z<.245*scale[2]+shift[2]:continue
        cross=((x-shift[0])/(.175*scale[0]))**2
        cross+=((z-shift[2]-.238*scale[2])/(.165*scale[2]))**2
        if cross>=.96:raise ValueError('Crown too narrow for forehead: '+code)
        clearance=.19*scale[1]*math.sqrt(.96-cross)
        low=max(low,y-clearance);high=min(high,y+clearance)
    if low>high:raise ValueError('No crown clearance for '+code)
    shift[1]=max(low,min(high,shift[1]))
    return dict(previous_shell_width=old_width,face_width=face_width,
                shell_width=width,width_reduction=1-width/old_width,
                forehead_depth_shift=shift[1]-previous_depth_shift)


def add_helmet(raw, game, codes, head_material=HEAD_MATERIAL, fit_function=snug_fit):
    if struct.unpack_from('<I',raw,4)[0] != 0x15500:
        raise ValueError('Only pinned Classic WLD is supported')
    nv=len(game['vertices'])
    if not nv or len(game['uv'])!=nv or len(game['normals'])!=nv:
        raise ValueError('Invalid game vertex attributes')
    for field,width in (('vertices',3),('normals',3),('uv',2)):
        if any(len(p)!=width or any(not math.isfinite(v) for v in p) for p in game[field]):
            raise ValueError('Nonfinite or malformed game '+field)
    for mat,a,b,c in game['triangles']:
        if not 0<=mat<len(game.get('material_frames',[0,1,2])) or len({a,b,c})!=3 or any(not 0<=i<nv for i in (a,b,c)):
            raise ValueError('Invalid game triangle index or material')
    w=_Wld(raw);fragments=list(w.fragments);strings=bytearray(w.strings);audit=[]
    before_fragment={};after_block={};used_blocks=set();modified_palettes={}
    def name_ref(name):
        if name in w.by_name:raise ValueError('Fragment name already exists: '+name)
        offset=len(strings);strings.extend(name.encode('ascii')+b'\0');return -offset
    def append(kind,name,payload):
        body=struct.pack('<Ii',kind,name_ref(name) if name else 0)+payload
        body+=bytes((-len(body))%4)
        fragments.append(struct.pack('<I',len(body)-4)+body)
        return len(fragments)
    for code in codes:
        target=f'{code}HE{head_material:02d}_DMSPRITEDEF'
        if target in w.by_name:raise ValueError('Helmet head already exists: '+target)
        source_id=w.by_name[code+'HE00_DMSPRITEDEF'][0]
        first,last=mesh_block(w,source_id)
        if first in used_blocks:
            raise ValueError('Actors unexpectedly share a mesh block')
        used_blocks.add(first)
        added_start=len(fragments)+1
        original=decode_mesh(w.fragments[source_id-1]);m=bare_face(w,code)
        palette_id=struct.unpack_from('<I',m['header'],16)[0]
        palette=w.fragments[palette_id-1]
        old_refs=[ref for _,ref in w.references(palette_id)]
        if palette_id in modified_palettes:
            raise ValueError('Actors unexpectedly share a material palette')
        if any(struct.unpack_from('<I',w.fragments[i-1],16)[0]!=palette_id
               for i in range(first,last+1)):
            raise ValueError('Actor meshes do not share the stock material palette')
        # Existing human plate metal bitmap, unmodified. These archives retain
        # the native full-global loader and original cross-race materials.
        new_refs=[]
        sample=w.fragments[old_refs[0]-1]
        if 'material_frames' not in game:
            texname=(game['texture']+'\0').encode('ascii')
            bitmap=append(3,code+'_WING_BITMAP',struct.pack('<IH',0,len(texname))+crypt(texname))
            bitmap_info=append(4,'',struct.pack('<III',0,1,bitmap))
            bitmap_ref=append(5,'',struct.pack('<II',bitmap_info,0))
            for suffix in ('SILVER','GOLD','IVORY'):
                payload=bytearray(sample[12:]);struct.pack_into('<I',payload,20,bitmap_ref)
                new_refs.append(append(0x30,code+'_WING_'+suffix,payload))
        else:
            for material,frames in enumerate(game['material_frames']):
                if not frames or len(frames)>64:raise ValueError('Invalid animation frame count')
                bitmaps=[]
                for frame,name in enumerate(frames):
                    if not name.isascii() or '/' in name or '\\' in name:raise ValueError('Unsafe bitmap name')
                    texname=(name+'\0').encode('ascii')
                    bitmaps.append(append(3,f'{code}_HE{head_material}_{material}_{frame}',struct.pack('<IH',0,len(texname))+crypt(texname)))
                animated=len(frames)>1
                payload=struct.pack('<II',8 if animated else 0,len(frames))
                if animated:payload+=struct.pack('<I',game['frame_ms'])
                bitmap_info=append(4,'',payload+struct.pack('<'+'I'*len(bitmaps),*bitmaps))
                bitmap_ref=append(5,'',struct.pack('<II',bitmap_info,0))
                payload=bytearray(sample[12:]);struct.pack_into('<I',payload,20,bitmap_ref)
                new_refs.append(append(0x30,f'{code}_HE{head_material}_M{material}',payload))
        # Classic actors select the FIRST mesh's palette for every variant.
        # A private palette on HE90 leaves its new material indices invisible.
        # Extend the shared stock palette; keep all original slots in place.
        expanded=bytearray(palette)
        if len(expanded)!=20+4*len(old_refs):
            raise ValueError('Unsupported stock material palette layout')
        expanded.extend(struct.pack('<'+'I'*len(new_refs),*new_refs))
        struct.pack_into('<I',expanded,0,len(expanded)-8)
        struct.pack_into('<I',expanded,16,len(old_refs)+len(new_refs))
        modified_palettes[palette_id]=bytes(expanded)
        fragments[palette_id-1]=bytes(expanded)
        head_bone=max(original['bones'])[1]
        offset=0;head=[]
        for count,bone in original['bones']:
            if bone==head_bone:head.extend(from_native_axes(code,p) for p in original['vertices'][offset:offset+count])
            offset+=count
        bone_labels=[bone for n,bone in m['bones'] for _ in range(n)]
        lows=[min(p[k] for p in head) for k in range(3)]
        highs=[max(p[k] for p in head) for k in range(3)]
        scale=[(highs[0]-lows[0])*1.15/.35,(highs[1]-lows[1])*1.15/.38,(highs[2]-lows[2]+.05)/.403]
        shift=[(highs[0]+lows[0])/2,(highs[1]+lows[1])/2,lows[2]]
        if code in ('HIM','ELM'):scale=[2.3]*3;shift=[0,-.03,-.19]
        fit=fit_function(w,code,m,head_bone,scale,shift)
        if game.get('replace_head',False):
            # A fully enclosed helm replaces the selected head variant. Keeping
            # the face surface underneath causes clipping on wide Classic heads.
            for key in ('vertices','normals','uv','polygons','polygon_materials'):
                m[key]=[]
            bone_labels=[]
        start=len(m['vertices'])
        for p,n,uv in zip(game['vertices'],game['normals'],game['uv']):
            m['vertices'].append(to_native_axes(code,[p[k]*scale[k]+shift[k] for k in range(3)]))
            normal=[n[k]/scale[k] for k in range(3)];length=math.sqrt(sum(v*v for v in normal))
            if length<1e-8:raise ValueError('Zero mesh normal')
            m['normals'].append(to_native_axes(code,[v/length for v in normal]));m['uv'].append(uv)
        # Native WLD front winding is opposite the outward normal; Blender's
        # positive normal winding must be reversed at this format boundary.
        m['polygons'].extend((0,start+c,start+b,start+a) for _,a,b,c in game['triangles'])
        m['polygon_materials'].extend(runs([len(old_refs)+p[0] for p in game['triangles']]))
        bone_labels.extend([head_bone]*nv)
        m['bones']=runs(bone_labels)
        # Mesh operations describe the old topology. Omit the optional list for
        # the new topology; stock head meshes and their operations remain intact.
        m['aux']=[];m['colors']=[];m['vertex_materials']=[]
        largest=max(abs(v) for p in m['vertices'] for v in p)
        m['scale']=min(13,int(math.floor(math.log2(32760/largest))))
        newmesh=encode_mesh(m,name_ref(target),palette_id)
        fragments.append(newmesh)
        mesh_id=len(fragments)
        append(0x2d,f'{code}HE{head_material:02d}_DMSPRITE',struct.pack('<II',len(fragments),0))
        before_fragment[palette_id]=list(range(added_start,mesh_id))
        after_block[last]=[mesh_id,len(fragments)]
        audit.append(dict(code=code,head_material=head_material,vertices=len(m['vertices']),triangles=len(m['polygons']),stock_face_triangles=len(m['polygons'])-len(game['triangles']),head_bone=head_bone,fit_scale=scale,fit_shift=shift,lateral_fit=fit,front='+X' if code in POSITIVE_X_FRONT else '-Y'))
    strings.extend(bytes((-len(strings))%4))
    header=bytearray(w.header)
    struct.pack_into('<I',header,8,len(fragments));struct.pack_into('<I',header,20,len(strings))
    output=bytes(header)+crypt(strings)+b''.join(fragments)+w.trailer
    after=_Wld(output)
    expected=[modified_palettes.get(i,data) for i,data in enumerate(w.fragments,1)]
    if after.fragments[:len(w.fragments)]!=expected:
        raise AssertionError('Original fragments changed')
    # The Classic loader enumerates consecutive 0x36 records around the stock
    # head. Keep material dependencies before that block and the new head in it.
    order=[]
    for index in range(1,len(w.fragments)+1):
        order.extend(before_fragment.get(index,[]))
        order.append(index)
        order.extend(after_block.get(index,[]))
    output=reorder(output,order)
    after=_Wld(output)
    for code in codes:
        if f'{code}HE{head_material:02d}_DMSPRITEDEF' not in registered_meshes(after,code):
            raise AssertionError('Helmet is outside the native actor mesh block')
        actor=after.by_name[registered_meshes(after,code)[0]][0]
        actor_palette=struct.unpack_from('<I',after.fragments[actor-1],16)[0]
        head=after.fragments[after.by_name[f'{code}HE{head_material:02d}_DMSPRITEDEF'][0]-1]
        if struct.unpack_from('<I',head,16)[0]!=actor_palette:
            raise AssertionError('Helmet materials are outside the native actor palette')
        if any(mat>=len(after.references(actor_palette)) for _,mat in decode_mesh(head)['polygon_materials']):
            raise AssertionError('Helmet material index exceeds native actor palette')
    return output,audit


def helmet_files(source, game):
    """Return validated archive bytes and provenance without writing client files."""
    archives={};outputs={}
    for name,digest in SOURCE_DIGESTS.items():
        if hashlib.sha256((source/name).read_bytes()).hexdigest()!=digest:
            raise ValueError('Source archive does not match supported RoF2: '+name)
    texture=read_pfs((source/'global_chr.s3d').read_bytes())[game['texture']]
    for archive,codes in CLASSIC_ARCHIVES.items():
        raw=(source/archive).read_bytes();files=read_pfs(raw);wld=archive[:-4]+'.wld'
        patched,audit=add_helmet(files[wld],game,codes)
        original=dict(files);files[wld]=patched
        if game['texture'] in files and files[game['texture']]!=texture:
            raise ValueError('Conflicting stock texture')
        files[game['texture']]=texture
        packed=write_pfs(files)
        if read_pfs(packed)!=files:raise AssertionError('PFS integrity failed')
        if any(files[n]!=value for n,value in original.items() if n!=wld):
            raise AssertionError('Original texture changed')
        outputs[archive]=packed
        archives[archive]=dict(source_sha256=hashlib.sha256(raw).hexdigest(),output_sha256=hashlib.sha256(packed).hexdigest(),models=audit)
    return outputs,archives


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client',type=Path,required=True)
    parser.add_argument('--mesh',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    source=args.client.resolve();out=args.output.resolve()
    if out==source or source in out.parents or out.exists():
        raise ValueError('Output must be new and outside the source client')
    game=json.loads(args.mesh.read_bytes())
    outputs,archives=helmet_files(source,game)
    out.mkdir(parents=True)
    for archive,packed in outputs.items():(out/archive).write_bytes(packed)
    report=dict(status='staged_not_installed_or_game_verified',mesh_sha256=hashlib.sha256(args.mesh.read_bytes()).hexdigest(),archives=archives)
    (out/'helmet-audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))

if __name__=='__main__':main()
