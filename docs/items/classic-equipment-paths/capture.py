"""Capture stock Classic item/drop evidence read-only; no player tables."""
import base64,gzip,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'docs/releases/classic-raid-augments-20261112'))
from probe import remote

CODE=r"""
import base64,gzip,json,importlib.util,datetime
from pathlib import Path
p=Path('/opt/nightcap/releases/stock-worn-atk-20261113-v1/release.py')
s=importlib.util.spec_from_file_location('stock',p);o=importlib.util.module_from_spec(s);s.loader.exec_module(o);o.initialize()
def rows(q):return [json.loads(x) for x in o.op.sql(q).splitlines()]
def table(t,where='1'):
 cols=[x.split('\t')[0] for x in o.op.sql('SHOW COLUMNS FROM `'+t+'`').splitlines()]
 pairs=','.join(repr(c)+',`'+c+'`' for c in cols)
 return rows('SELECT JSON_OBJECT('+pairs+') FROM `'+t+'` WHERE '+where)
pairs=["'zone',z.short_name","'zoneid',z.zoneidnumber","'npc',n.id","'npc_name',n.name","'npc_level',n.level","'item',i.id","'item_name',i.Name","'chance',l.chance","'probability',t.probability","'lt_multiplier',t.multiplier","'ld_multiplier',l.multiplier","'spawn_chance',e.chance","'condition',s._condition","'condition_value',s.cond_value","'npc_min_level',l.npc_min_level","'npc_max_level',l.npc_max_level","'trivial_min_level',l.trivial_min_level","'trivial_max_level',l.trivial_max_level"]
for alias in ('s','e','lt','ld','l'):
 for f in ('min_expansion','max_expansion','content_flags','content_flags_disabled'):
  pairs.append(repr(alias+'_'+f)+','+alias+'.'+f)
routes=rows('SELECT DISTINCT JSON_OBJECT('+','.join(pairs)+''') FROM zone z
JOIN spawn2 s ON s.zone=z.short_name AND s.version=z.version
JOIN spawnentry e ON e.spawngroupID=s.spawngroupID JOIN npc_types n ON n.id=e.npcID
JOIN loottable lt ON lt.id=n.loottable_id JOIN loottable_entries t ON t.loottable_id=lt.id
JOIN lootdrop ld ON ld.id=t.lootdrop_id JOIN lootdrop_entries l ON l.lootdrop_id=ld.id
JOIN items i ON i.id=l.item_id WHERE z.expansion=0 AND z.version=0 AND n.id<900000
AND i.id>0 AND i.id<200000 AND i.itemclass=0 AND i.slots>0 AND i.augtype=0 AND i.itemtype<>54''')
ids=sorted({r['item']+k for r in routes for k in (0,200000,400000,600000)})
items=[]
for start in range(0,len(ids),500):items+=table('items','id IN ('+','.join(map(str,ids[start:start+500]))+')')
focuses=sorted({r[c] for r in items for c in ('focuseffect','worneffect') if r[c]>0})
spells=table('spells_new','id IN ('+','.join(map(str,focuses))+') OR name REGEXP \'^(Spell Haste|Improved Healing|Mana Preservation) (I|II|III|IV)$\'')
spells=table('spells_new',"id IN ("+','.join(map(str,focuses))+") OR name REGEXP '^(Spell Haste|Improved Healing|Mana Preservation|Improved Damage|Burning Affliction|Speed of|Swift|Aura of|Attack|Accuracy|Improved Dodge|Improved Parry|Improved Riposte|Aura of Battle|Regeneration|Flowing Thought|Shielding|Magic Resistance|Resist Magic)'")
out=dict(captured_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),routes=routes,items=items,spells=spells,zones=table('zone','expansion=0 AND version=0'),content_flags=table('content_flags'),global_loot=table('global_loot'))
print(base64.b64encode(gzip.compress(json.dumps(out,separators=(',',':')).encode(),mtime=0)).decode())
"""
if __name__=='__main__':
 raw=base64.b64decode(remote(CODE,timeout=300).strip(),validate=True)
 data=json.loads(gzip.decompress(raw));(HERE/'production.json.gz').write_bytes(raw)
 print(json.dumps({k:len(v) if isinstance(v,list) else v for k,v in data.items()}))
