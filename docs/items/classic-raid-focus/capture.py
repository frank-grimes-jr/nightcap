"""Capture public Classic stock routes and actual tier effects from the selected server."""
import json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'docs/releases/classic-raid-augments-20261112'))
from probe import remote

zones=('fearplane','hateplane','hateplaneb','airplane','kedge','permafrost','soldungb','hole','thole')
bosses=(73057,32040,64001,39065)
gates=' AND '.join(f"({alias}.min_expansion<=0 AND COALESCE({alias}.content_flags,'')='' AND COALESCE({alias}.content_flags_disabled,'')='')" for alias in ['s','e','lt','ld','l'])
route=f"""SELECT DISTINCT z.short_name,n.id,n.name,i.id,i.Name
FROM zone z JOIN spawn2 s ON s.zone=z.short_name AND s.version=z.version
JOIN spawnentry e ON e.spawngroupID=s.spawngroupID JOIN npc_types n ON n.id=e.npcID
JOIN loottable lt ON lt.id=n.loottable_id JOIN loottable_entries t ON t.loottable_id=lt.id
JOIN lootdrop ld ON ld.id=t.lootdrop_id JOIN lootdrop_entries l ON l.lootdrop_id=ld.id
JOIN items i ON i.id=l.item_id WHERE z.short_name IN {zones} AND z.version=0 AND z.expansion=0
AND (z.short_name IN ('fearplane','hateplane','hateplaneb','airplane') OR n.id IN {bosses} OR n.name LIKE '%Master_Yael%')
AND e.chance>0 AND t.probability>0 AND t.multiplier>0 AND l.multiplier>0 AND l.chance>0
AND (l.npc_min_level=0 OR n.level>=l.npc_min_level) AND (l.npc_max_level=0 OR n.level<=l.npc_max_level)
AND (l.trivial_min_level=0 OR l.trivial_min_level<=50) AND (l.trivial_max_level=0 OR l.trivial_max_level>=50)
AND s._condition=0 AND {gates} AND i.id<200000 AND i.slots>0 AND i.itemclass=0 AND i.itemtype<>54 AND i.reqlevel<=50 ORDER BY 1,2,4"""
cols='id Name slots classes itemtype reqlevel reclevel worneffect worntype wornlevel wornlevel2 focuseffect focustype focuslevel focuslevel2 clickeffect proceffect scrolleffect bardtype bardeffect haste mana hp ac'.split()
code="""import json,importlib.util
from pathlib import Path
s=importlib.util.spec_from_file_location('ops',Path('/opt/nightcap/releases/dungeon-readiness-20261106-v1/rollout.py'))
op=importlib.util.module_from_spec(s);s.loader.exec_module(op);op.initialize()
def rows(query):
 return [line.split(chr(9)) for line in op.p.sql(query).splitlines()]
routes=rows(route)
ids={int(x[3])+offset for x in routes for offset in (0,200000,400000,600000)}
items=[dict(zip(cols,row)) for row in rows('SELECT '+','.join('`'+c+'`' for c in cols)+' FROM items WHERE id IN ('+','.join(map(str,sorted(ids)))+') ORDER BY id')]
spells=rows("SELECT id,name,effectid1,effect_base_value1,effect_limit_value1 FROM spells_new WHERE id IN ("+','.join(str(i) for i in {int(r[c]) for r in items for c in ('worneffect','focuseffect') if int(r[c])>0})+") OR name IN ('Improved Healing II','Improved Damage II','Extended Range II','Spell Haste II','Mana Preservation II','Improved Dodge I','Serpent Sight','Enduring Breath','Faerune','Flowing Thought I') ORDER BY id")
print(json.dumps(dict(routes=routes,items=items,spells=spells)))
"""
if __name__=='__main__':
 d=json.loads(remote('route='+repr(route)+'\ncols='+repr(cols)+'\n'+code))
 (HERE/'audit.json').write_text(json.dumps(d,separators=(',',':'))+'\n',encoding='utf8')
 print(len(d['routes']),len(d['items']))
