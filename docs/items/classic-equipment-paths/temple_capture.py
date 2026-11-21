"""Read-only Temple of Solusek Ro acquisition supplement."""
import base64,gzip,json
from capture import CODE,remote,HERE
code=CODE.split('pairs=[')[0]+r"""
root=Path('/opt/nightcap/deploy/production/data/server/quests/soltemple');sources=[]
import hashlib
if root.exists():
 for f in sorted(root.glob('*')):
  if f.suffix in ('.pl','.lua'):sources.append(dict(path='soltemple/'+f.name,text=f.read_text(),sha256=hashlib.sha256(f.read_bytes()).hexdigest()))
out=dict(zones=table('zone',"short_name='soltemple'"),spawns=table('spawn2',"zone='soltemple'"),quests=sources,npcs=table('npc_types','id BETWEEN 80000 AND 80999'),entries=table('spawnentry','spawngroupID IN ('+','.join(str(r['spawngroupID']) for r in table('spawn2',"zone='soltemple'"))+')'))
print(base64.b64encode(gzip.compress(json.dumps(out,separators=(',',':')).encode(),mtime=0)).decode())
"""
if __name__=='__main__':
 raw=base64.b64decode(remote(code,timeout=120).strip(),validate=True);d=json.loads(gzip.decompress(raw));(HERE/'soltemple.json.gz').write_bytes(raw);print({k:len(v) for k,v in d.items()})
