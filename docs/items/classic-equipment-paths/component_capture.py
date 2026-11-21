"""Read-only Classic component routes and merchant spawn gates."""
import base64,gzip,json
from capture import CODE,remote,HERE
code=CODE.split("ids=sorted")[0].replace("AND i.id>0 AND i.id<200000 AND i.itemclass=0 AND i.slots>0 AND i.augtype=0 AND i.itemtype<>54", "AND i.id>0 AND i.id<200000")+r"""
fields=["'zone',z.short_name","'npc',n.id","'name',n.name","'merchant',n.merchant_id","'condition',s._condition","'condition_value',s.cond_value","'chance',e.chance"]
for a in ('s','e'):
 for f in ('min_expansion','max_expansion','content_flags','content_flags_disabled'):fields.append(repr(a+'_'+f)+','+a+'.'+f)
merchants=rows('SELECT DISTINCT JSON_OBJECT('+','.join(fields)+') FROM zone z JOIN spawn2 s ON s.zone=z.short_name AND s.version=z.version JOIN spawnentry e ON e.spawngroupID=s.spawngroupID JOIN npc_types n ON n.id=e.npcID WHERE z.expansion=0 AND z.version=0 AND n.id<900000 AND n.merchant_id>0')
print(base64.b64encode(gzip.compress(json.dumps(dict(routes=routes,merchant_spawns=merchants,captured_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()),separators=(',',':')).encode(),mtime=0)).decode())
"""
if __name__=='__main__':
 raw=base64.b64decode(remote(code,timeout=600).strip(),validate=True);d=json.loads(gzip.decompress(raw));(HERE/'components.json.gz').write_bytes(raw);print({k:len(v) if isinstance(v,list) else v for k,v in d.items()})
