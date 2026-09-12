"""Capture wider gear acquisition candidates without certifying quest/recipe reachability."""
import argparse
import gzip
import hashlib
import json
import re
from datetime import datetime,timezone
from pathlib import Path

from baseline import query_json
from snapshot import era_predicate,row_json


# Discovery lexer only, not a Perl/Lua interpreter or quest eligibility proof.
TOKENS=re.compile(r'--\[(=*)\[.*?\]\1\]|\[(=*)\[.*?\]\2\]|--[^\n]*|\#[^\n]*|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|[A-Za-z_][\w.:]*|\d+|[^\s]',re.S)
ITEM_GATE='i.reqlevel<=50 AND (i.slots & 2097150)>0 AND (i.classes & 7747)>0 AND (i.races & 1)>0 AND (i.deity=0 OR (i.deity & 1)>0)'
ZONE_GATE="z.version=0 AND (z.expansion=0 OR z.short_name='poknowledge')"


def reward_candidates(source):
    tokens=[(m.group(),m.start()) for m in TOKENS.finditer(source)
            if not m.group().startswith(('--','#'))]
    found=[]
    for index,(name,pos) in enumerate(tokens[:-1]):
        method=re.split(r'[.:]',name)[-1].lower()
        if method not in ('summonitem','questreward') or tokens[index+1][0]!='(':
            continue
        args=[[]]; depth=1
        for token,_ in tokens[index+2:]:
            if token=='(':
                depth+=1
            elif token==')':
                depth-=1
                if not depth:
                    break
            if token==',' and depth==1:
                args.append([])
            else:
                args[-1].append(token)
        position=5 if method=='questreward' else 0
        literal=args[position] if position<len(args) else []
        value=literal[0] if len(literal)==1 else ''
        if re.fullmatch(r'''["']\d+["']''',value):
            value=value[1:-1]
        item_id=int(value) if value.isdigit() else None
        found.append({'line':source.count('\n',0,pos)+1,'call':name,
                      'item_id':item_id if item_id and item_id<=2147483647 else None,
                      'arguments':[''.join(a) for a in args],
                      'status':'unreviewed_reference_not_acquisition_proof'})
    return found


def scan_quests(root,zones):
    results=[]
    for zone in sorted(set(zones)|{'global'}):
        folder=root/zone
        if not folder.is_dir():
            continue
        files=sorted(p for p in folder.rglob('*') if p.suffix.lower() in ('.pl','.lua'))
        lua={p.with_suffix('') for p in files if p.suffix.lower()=='.lua'}
        for file in files:
            if file.suffix.lower()=='.pl' and file.with_suffix('') in lua:
                continue
            raw=file.read_bytes(); text=raw.decode('utf-8',errors='replace')
            rewards=reward_candidates(text)
            if rewards:
                results.append({'path':file.relative_to(root).as_posix(),
                                'sha256':hashlib.sha256(raw).hexdigest(),
                                'source':text,'reward_candidates':rewards})
    return results


def object_sql(table,alias):
    if table not in {'global_loot','merchantlist','tradeskill_recipe','tradeskill_recipe_entries'}:
        raise ValueError('Unexpected acquisition table')
    columns=query_json("SELECT JSON_OBJECT('name',COLUMN_NAME) FROM information_schema.COLUMNS "
                       f"WHERE TABLE_SCHEMA='peq' AND TABLE_NAME='{table}' ORDER BY ORDINAL_POSITION")
    if not columns or any(not re.fullmatch(r'\w+',r['name']) for r in columns):
        raise ValueError('Unexpected content schema')
    return 'JSON_OBJECT('+','.join(f"'{r['name']}',{alias}.`{r['name']}`" for r in columns)+')'


def source_queries():
    spawn_gate=f"""{ZONE_GATE} AND s._condition=0 AND se.chance>0
AND NOT EXISTS(SELECT 1 FROM spawn2_disabled sd WHERE sd.spawn2_id=s.id AND sd.instance_id=0 AND sd.disabled<>0)
AND {era_predicate('s')} AND {era_predicate('se')}"""
    merchants=f"""SELECT DISTINCT JSON_OBJECT('table','merchant_sources','row',JSON_OBJECT(
'zone',z.short_name,'npc_id',n.id,'npc_name',n.name,'npc_class',n.class,
'alt_currency_id',n.alt_currency_id,'npc_faction_id',n.npc_faction_id,
'primary_faction',f.primaryfaction,
'merchant', {object_sql('merchantlist','m')}))
FROM zone z JOIN spawn2 s ON s.zone=z.short_name AND s.version=z.version
JOIN spawnentry se ON se.spawngroupID=s.spawngroupID JOIN npc_types n ON n.id=se.npcID
JOIN merchantlist m ON m.merchantid=n.merchant_id
LEFT JOIN npc_faction f ON f.id=n.npc_faction_id
WHERE {spawn_gate} AND {era_predicate('m')}
AND m.min_status<=0 AND m.max_status>=0 AND m.level_required<=50 AND m.probability>0"""
    recipe_ids=f"""SELECT DISTINCT e.recipe_id FROM tradeskill_recipe_entries e
JOIN items i ON i.id=e.item_id JOIN tradeskill_recipe r ON r.id=e.recipe_id
WHERE e.successcount>0 AND r.enabled=1 AND {era_predicate('r')} AND {ITEM_GATE}"""
    return [merchants,
        f"SELECT JSON_OBJECT('table','global_loot','row',{object_sql('global_loot','g')}) FROM global_loot g",
        f"""SELECT JSON_OBJECT('table','global_loot_entries','row',JSON_OBJECT(
        'global_id',g.id,'lootdrop_id',d.id,'item_id',e.item_id,'chance',e.chance,
        'multiplier',e.multiplier,'npc_min_level',e.npc_min_level,'npc_max_level',e.npc_max_level))
        FROM global_loot g JOIN loottable l ON l.id=g.loottable_id
        JOIN loottable_entries t ON t.loottable_id=l.id JOIN lootdrop d ON d.id=t.lootdrop_id
        JOIN lootdrop_entries e ON e.lootdrop_id=d.id
        WHERE g.enabled=1 AND t.probability>0 AND t.multiplier>0 AND e.chance>0 AND e.multiplier>0
        AND {era_predicate('g')} AND {era_predicate('l')} AND {era_predicate('d')} AND {era_predicate('e')}""",
        f"SELECT JSON_OBJECT('table','recipes','row',{object_sql('tradeskill_recipe','r')}) FROM tradeskill_recipe r WHERE r.id IN ({recipe_ids})",
        f"SELECT JSON_OBJECT('table','recipe_entries','row',{object_sql('tradeskill_recipe_entries','e')}) FROM tradeskill_recipe_entries e WHERE e.recipe_id IN ({recipe_ids})"]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--quests',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    zones=query_json(f"SELECT JSON_OBJECT('zone',z.short_name) FROM zone z WHERE {ZONE_GATE}")
    quests=scan_quests(args.quests,[z['zone'] for z in zones])
    queries=source_queries()
    tables={'merchant_sources':[],'global_loot':[],'global_loot_entries':[],'recipes':[],'recipe_entries':[]}
    for row in query_json(';\n'.join(queries)):
        tables[row['table']].append(row['row'])
    references={r['item_id'] for q in quests for r in q['reward_candidates'] if r['item_id']}
    references.update(r['merchant']['item'] for r in tables['merchant_sources'])
    references.update(r['item_id'] for r in tables['recipe_entries'])
    for row in tables['global_loot_entries']:
        references.add(row['item_id'])
        if 0<row['item_id']<200000:
            references.update(row['item_id']+offset for offset in (200000,400000,600000))
    # Include all epic base/upgraded rows for explicit acquisition review; not an automatic grant.
    epics=[5532,10099,10650,10651,10652,10908,11057,11566,14341,14383,20487,20488,20490,20542,20544]
    references.update(epics); references.update(i+800000 for i in epics)
    ids=','.join(str(i) for i in sorted(references)) or '0'
    item_query=f"SELECT {row_json('items','i')} FROM items i WHERE ({ITEM_GATE}) AND i.id IN ({ids})"
    tables['candidate_items']=query_json(item_query)
    for rows in tables.values():
        rows.sort(key=lambda r:json.dumps(r,sort_keys=True))
    payload={'schema_version':1,'captured_at':datetime.now(timezone.utc).isoformat(),
             'scope':'Acquisition discovery candidates only. Global-loot NPC restrictions, merchant faction/class/bucket access, quest execution/NPC/version/prerequisites, epic accessibility, and recipe components/learning remain unverified. No quest/merchant/craft tier copies are assumed obtainable.',
             'zones':zones,'quests':quests,'tables':tables}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_bytes(gzip.compress(json.dumps(payload,separators=(',',':')).encode(),mtime=0))
    sql=';\n'.join(queries+[item_query])+';\n'
    manifest={'schema_version':1,'kind':'acquisition_candidates','snapshot_sha256':hashlib.sha256(args.output.read_bytes()).hexdigest(),
              'scope':payload['scope'],'captured_at':payload['captured_at'],
              'quest_files':len(quests),'referenced_item_ids':len(references),
              'rows':{name:len(rows) for name,rows in tables.items()},
              'query_sha256':hashlib.sha256(sql.encode()).hexdigest()}
    args.output.with_suffix('.manifest.json').write_bytes((json.dumps(manifest,indent=2)+'\n').encode())
    args.output.with_suffix('.queries.sql').write_bytes(sql.encode())
    print(json.dumps(manifest,indent=2))


if __name__=='__main__':
    main()
