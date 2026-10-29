"""Add the original Hate actors missing from the successor's native archive."""
import hashlib
import json
from pathlib import Path
from classic_model_archives import actor_names, read_pfs

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'assets/hate-layout-client.json'


def files(client):
    plan=json.loads(PLAN.read_text())
    raw={name:(client/name).read_bytes() for name in plan['sources']}
    for name,data in raw.items():
        if hashlib.sha256(data).hexdigest()!=plan['sources'][name]:
            raise ValueError('Unreviewed Hate client source: '+name)
    old=set(actor_names(read_pfs(raw['hateplane_chr.s3d'])['hateplane_chr.wld']))
    new=set(actor_names(read_pfs(raw['hateplaneb_chr.s3d'])['hateplaneb_chr.wld']))
    missing=sorted(name.removesuffix('_ACTORDEF').lower() for name in old-new)
    if missing!=plan['imports']:
        raise ValueError('Hate actor closure changed')
    lines=raw['hateplaneb_chr.txt'].decode('ascii').splitlines()
    if not lines or int(lines[0])!=len(lines)-1:
        raise ValueError('Malformed Hate model list')
    retained=[line for line in lines[1:] if line.split(',')[0].lower() not in missing]
    imports=retained+[code+',hateplane_chr' for code in missing]
    if len({line.split(',')[0].lower() for line in imports})!=len(imports):
        raise ValueError('Duplicate Hate model import')
    return {'hateplane_chr.s3d':raw['hateplane_chr.s3d'],
            'hateplaneb_chr.s3d':raw['hateplaneb_chr.s3d'],
            'hateplaneb_chr.txt':(str(len(imports))+'\n'+'\n'.join(imports)+'\n').encode('ascii')}
