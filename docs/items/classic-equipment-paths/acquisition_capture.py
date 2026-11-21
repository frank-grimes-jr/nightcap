"""Read-only recipe, stock item roster and active Classic quest source capture."""
import base64,gzip,json
from capture import CODE,remote,HERE
code=CODE.split('pairs=[')[0]+r"""
import hashlib
recipes=table('tradeskill_recipe','enabled=1 AND min_expansion<=0 AND (max_expansion=-1 OR max_expansion>=0)')
rids=[r['id'] for r in recipes];entries=[]
for start in range(0,len(rids),800):entries+=table('tradeskill_recipe_entries','recipe_id IN ('+','.join(map(str,rids[start:start+800]))+')')
columns=['id','Name','itemclass','itemtype','slots','classes','races','deity','reqlevel','reclevel','augtype','augrestrict','focuseffect','focustype','worneffect','worntype','proceffect','proctype','haste','attack','accuracy','hp','mana','ac','healamt','spelldmg','regen','manaregen','tradeskills','bagtype','loregroup','nodrop','norent','astr','asta','aagi','adex','awis','aint','acha','mr','fr','cr','dr','pr','damage','delay','clicklevel','clickeffect']
fields=','.join(repr(c)+',`'+c+'`' for c in columns)
items=rows('SELECT JSON_OBJECT('+fields+') FROM items WHERE id>0 AND id<200000')
zones=table('zone','expansion=0 AND version=0')
np=rows("SELECT DISTINCT JSON_OBJECT('zone',s.zone,'id',n.id,'name',n.name,'level',n.level,'merchant',n.merchant_id) FROM zone z JOIN spawn2 s ON s.zone=z.short_name AND s.version=z.version JOIN spawnentry e ON e.spawngroupID=s.spawngroupID JOIN npc_types n ON n.id=e.npcID WHERE z.expansion=0 AND z.version=0 AND n.id<900000")
root=Path('/opt/nightcap/deploy/production/data/server/quests');sources=[]
for z in zones:
 folder=root/z['short_name']
 if not folder.is_dir():continue
 for f in sorted(folder.rglob('*')):
  if f.is_file() and f.suffix in ('.pl','.lua'):
   raw=f.read_bytes();text=raw.decode('utf8',errors='replace')
   if any(v in text.lower() for v in ('summonitem','summon_item','quest_reward','questreward','reward_id','assign_task','assigntask')):
    sources.append(dict(path=str(f.relative_to(root)),sha256=hashlib.sha256(raw).hexdigest(),text=text))
merchants=[];ids=sorted({n['merchant'] for n in np if n['merchant']})
for start in range(0,len(ids),500):merchants+=table('merchantlist','merchantid IN ('+','.join(map(str,ids[start:start+500]))+')')
spells=table('spells_new',' OR '.join('effectid'+str(i)+' IN (124,286,11,216,2)' for i in range(1,13)))
out=dict(captured_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),recipes=recipes,entries=entries,items=items,npcs=np,quests=sources,merchants=merchants,offensive_spells=spells)
print(base64.b64encode(gzip.compress(json.dumps(out,separators=(',',':')).encode(),mtime=0)).decode())
"""
if __name__=='__main__':
 raw=base64.b64decode(remote(code,timeout=600).strip(),validate=True);d=json.loads(gzip.decompress(raw));(HERE/'acquisition.json.gz').write_bytes(raw)
 print({k:len(v) if isinstance(v,list) else v for k,v in d.items()})
