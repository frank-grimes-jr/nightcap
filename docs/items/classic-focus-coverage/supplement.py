"""Read-only global-loot and conditional-spawn audit supplement."""
import json,sys
from pathlib import Path
from capture import CODE,remote,HERE
code=CODE.split('pairs=[')[0]+'''
query="""SELECT JSON_OBJECT('global_id',g.id,'description',g.description,'global_min_expansion',g.min_expansion,'global_max_expansion',g.max_expansion,'enabled',g.enabled,'item',i.id,'name',i.Name,'focus',i.focuseffect,'chance',l.chance,'probability',t.probability,'lt_min_expansion',lt.min_expansion,'ld_min_expansion',ld.min_expansion,'l_min_expansion',l.min_expansion)
FROM global_loot g JOIN loottable lt ON lt.id=g.loottable_id
JOIN loottable_entries t ON t.loottable_id=lt.id JOIN lootdrop ld ON ld.id=t.lootdrop_id
JOIN lootdrop_entries l ON l.lootdrop_id=ld.id JOIN items i ON i.id=l.item_id
WHERE i.itemclass=0 AND i.slots>0 AND i.augtype=0 AND i.itemtype<>54"""
print(json.dumps(dict(global_equipment=rows(query),spawn_conditions=table('spawn_conditions'),captured_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())))
'''
if __name__=='__main__':
 data=json.loads(remote(code,timeout=180));(HERE/'supplement.json').write_text(json.dumps(data,indent=2)+'\n')
 print({k:len(v) if isinstance(v,list) else v for k,v in data.items()})
