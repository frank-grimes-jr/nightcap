"""Read-only tradeskill container and spell-created ingredient evidence."""
import base64,gzip,json
from capture import CODE,remote,HERE
code=CODE.split('pairs=[')[0]+r"""
zones=[z['zoneidnumber'] for z in table('zone','expansion=0 AND version=0')]
where='zoneid IN ('+','.join(map(str,zones))+')'
objects=table('object',where)
spells=table('spells_new','('+ ' OR '.join('effectid'+str(i)+'=32' for i in range(1,13))+') AND ('+' OR '.join('classes'+str(i)+' BETWEEN 1 AND 50' for i in range(1,17))+')')
print(base64.b64encode(gzip.compress(json.dumps(dict(objects=objects,spells=spells,scrolls=table('items','scrolleffect IN ('+','.join(str(r['id']) for r in spells)+')'),captured_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()),separators=(',',':')).encode(),mtime=0)).decode())
"""
if __name__=='__main__':
 raw=base64.b64decode(remote(code,timeout=300).strip(),validate=True);d=json.loads(gzip.decompress(raw));(HERE/'craft-support.json.gz').write_bytes(raw);print({k:len(v) if isinstance(v,list) else v for k,v in d.items()})
