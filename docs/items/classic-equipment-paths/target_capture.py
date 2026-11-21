"""Read all fields and qualities of explicit candidates for drift-safe migrations."""
import base64,gzip,json
from capture import CODE,remote,HERE
if __name__=='__main__':
 policy=json.loads((HERE/'policy.json').read_bytes())['families'];ids=[int(k)+200000*t for k in policy for t in range(4)]
 effects=sorted({e[f] for e in policy.values() for f in ('focus','worn') if f in e})
 code=CODE.split('pairs=[')[0]+"ids="+repr(ids)+";items=[]\nfor start in range(0,len(ids),300):items+=table('items','id IN ('+','.join(map(str,ids[start:start+300]))+')')\n"
 code+="out=dict(items=items,spells=table('spells_new','id IN ("+','.join(map(str,effects))+")'),captured_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())\nprint(base64.b64encode(gzip.compress(json.dumps(out,separators=(',',':')).encode(),mtime=0)).decode())"
 raw=base64.b64decode(remote(code,timeout=300).strip(),validate=True);d=json.loads(gzip.decompress(raw));(HERE/'targets.json.gz').write_bytes(raw);print({k:len(v) if isinstance(v,list) else v for k,v in d.items()})
