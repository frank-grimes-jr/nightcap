"""Capture target content/schema and adapt Classic CT into isolated identities.

Read-only against local PEQ. Emits explicit rows for subsequent guarded staging
and migration; does not apply them. Player/account data is never selected.
"""
import json
from pathlib import Path
from dungeon_capture import query, rows

ROOT=Path(__file__).resolve().parents[1]
TABLES=('items','npc_types','spawngroup','spawnentry','loottable','loottable_entries',
        'lootdrop','lootdrop_entries','npc_spells','npc_spells_entries','npc_faction',
        'npc_faction_entries','grid','grid_entries','tasks','task_activities',
        'instance_list','instance_list_player')

# Explicit exclusions from the donor's shared caster lists. These spells were
# introduced with Velious (1419,1445) or Luclin (2551,2554), after Classic.
LATER_ERA_SPELLS={1419,1445,2551,2554}

def sql(value):
    if value is None:return 'NULL'
    if isinstance(value,str):return "X'"+value.encode().hex()+"'"
    return str(int(value)) if isinstance(value,bool) else str(value)

def adapt(donor, target):
    result={}
    maps={table:{r['id']:985000+i for i,r in enumerate(sorted(donor[table],key=lambda r:r['id']))}
          for table in ('npc_types','spawngroup','loottable','lootdrop','npc_spells','npc_faction')}
    maps['grid']={r['id']:9900+i for i,r in enumerate(sorted(donor['grid'],key=lambda r:r['id']))}
    item_map={}
    aliases={12335:'Clump of Gorilla Hair',16544:'Broom',16545:'Shovel',16546:'Torch',16547:'Stein'}
    for item in donor['items']:
        name=aliases.get(item['id'],item['Name'])
        exact=[r for r in target['items'] if r['id']==item['id'] and r['Name']==name]
        matches=exact or [r for r in target['items'] if r['Name']==item['Name'] and r['id']<200000]
        assert len(matches)==1,(item['id'],item['Name'],'ambiguous native loot identity')
        item_map[item['id']]=matches[0]['id']
    factions={r['id']:next(t['id'] for t in target['faction_list'] if t['name']==r['name']) for r in donor['faction_list']}
    for table in maps:
        result[table]=[]
        columns=target['columns'][table]
        for old in donor[table]:
            row={k:v for k,v in old.items() if k in columns}
            row['id']=maps[table][old['id']]
            if table=='npc_types':
                for field,parent in [('loottable_id','loottable'),('npc_spells_id','npc_spells'),('npc_faction_id','npc_faction')]:
                    row[field]=maps[parent].get(old[field],0)
                # The preserved level-39 SK definition has spells. Quarm's
                # custom 48500 omitted its list; restore the pinned SK list.
                if old['id']==48500:row['npc_spells_id']=maps['npc_spells'][9]
                row.update(qglobal=0,emoteid=0,merchant_id=0,npc_spells_effects_id=0)
                assert not old['merchant_id'] and not old['npc_spells_effects_id']
            elif table=='spawngroup':row['name']='nightcap_classic_ct_'+str(old['id'])
            elif table=='npc_spells':row['parent_list']=maps[table].get(old['parent_list'],0)
            elif table=='npc_faction':row['primaryfaction']=factions[old['primaryfaction']]
            result[table].append(row)
    relations={
      'spawnentry':[('spawngroupID','spawngroup'),('npcID','npc_types')],
      'loottable_entries':[('loottable_id','loottable'),('lootdrop_id','lootdrop')],
      'lootdrop_entries':[('lootdrop_id','lootdrop')],
      'npc_spells_entries':[('npc_spells_id','npc_spells')],
      'npc_faction_entries':[('npc_faction_id','npc_faction')],
      'grid_entries':[('gridid','grid')]}
    for table,relations_ in relations.items():
        result[table]=[]
        for old in donor[table]:
            if table=='npc_spells_entries' and (old['minlevel']>39 or old['spellid'] in LATER_ERA_SPELLS):continue
            row={k:v for k,v in old.items() if k in target['columns'][table]}
            for key,parent in relations_:row[key]=maps[parent][old[key]]
            if 'min_expansion' in row:row['min_expansion']=0
            if 'max_expansion' in row:row['max_expansion']=-1
            if table=='lootdrop_entries':row['item_id']=item_map[old['item_id']]
            if table=='npc_spells_entries':row['id']=9800000+len(result[table])
            if table=='npc_faction_entries':row['faction_id']=factions[old['faction_id']]
            result[table].append(row)
    result['nightcap_dungeon_spawns']=[]
    spawn_map={}
    for i,old in enumerate(sorted(donor['spawn2'],key=lambda r:r['id'])):
        # 21 donor points reference absent group 448001. They cannot spawn an
        # NPC; preserve their explicit exclusion in the audited source closure.
        if 11448208<=old['id']<=11448228:
            assert old['spawngroupID']==448001 and not any(r['spawngroupID']==448001 for r in donor['spawnentry'])
            continue
        assert old['_condition']==0 and old['variance']==0
        id=9000000+i;spawn_map[old['id']]=id
        result['nightcap_dungeon_spawns'].append(dict(zone_id=48,spawn_id=id,group_id=maps['spawngroup'][old['spawngroupID']],npc_id=0,
            boss_id=0,is_final=0,x=old['x'],y=old['y'],z=old['z'],heading=old['heading'],respawn=old['respawntime'],grid_id=maps['grid'].get(old['pathgrid'],0)))
    roster=[]
    for i,old_id in enumerate((48700,48507,48508,48509,48522,48500)):
        groups={r['spawngroupID'] for r in donor['spawnentry'] if r['npcID']==old_id}
        spawns=[r for r in donor['spawn2'] if r['spawngroupID'] in groups]
        assert len(spawns)==1
        old=spawns[0];npc=next(r for r in donor['npc_types'] if r['id']==old_id)
        spawn=next(r for r in result['nightcap_dungeon_spawns'] if r['spawn_id']==spawn_map[old['id']])
        spawn.update(npc_id=maps['npc_types'][old_id],boss_id=i+1,is_final=int(i==5))
        roster.append(dict(boss_id=i+1,npc_id=maps['npc_types'][old_id],name=npc['name'].replace('_',' '),
                           spawn_id=spawn['spawn_id'],is_final=i==5,spawn=spawn,donor_npc_id=old_id,donor_spawn_id=old['id']))
    return dict(tables=result,maps=maps,item_map=item_map,roster=roster)

def main():
    donor=json.loads((ROOT/'docs/dungeons/classic-ct.json').read_text())
    target={'columns':{},'ddl':{}}
    for table in TABLES:
        try:
            target['columns'][table]=[r[0] for r in query('SHOW COLUMNS FROM `'+table+'`')]
            ddl=query('SHOW CREATE TABLE `'+table+'`')
            target['ddl'][table]=ddl[0][1]+'\n'+'\n'.join('\t'.join(r) for r in ddl[1:])
        except Exception as e:
            raise RuntimeError('Cannot capture schema: '+table) from e
    names=','.join(sql(r['Name']) for r in donor['items'])
    target['items']=rows('items','(Name IN ('+names+') OR id IN (12335,16544,16545,16546,16547)) AND id<200000')
    target['faction_list']=[dict(id=int(r[0]),name=r[1]) for r in query("SELECT id,name FROM faction_list WHERE name IN ('Allize Taeew','Allize Volew')")]
    for table in ('npc_types','spawngroup','loottable','lootdrop','npc_spells','npc_faction'):
        assert not query(f'SELECT id FROM {table} WHERE id BETWEEN 985000 AND 985299'),table+' ID collision'
    assert not query('SELECT id FROM spawn2 WHERE id BETWEEN 9000000 AND 9000299')
    assert not query('SELECT id FROM npc_spells_entries WHERE id BETWEEN 9800000 AND 9800999')
    assert not query('SELECT id FROM grid WHERE zoneid=48 AND id BETWEEN 9900 AND 9999')
    assert not query('SELECT id FROM tasks WHERE id BETWEEN 9700 AND 9713')
    target['spell_names']=[dict(id=int(r[0]),name=r[1]) for r in query('SELECT id,name FROM spells_new WHERE id IN ('+','.join(str(r['spellid']) for r in donor['npc_spells_entries'] if r['minlevel']<=39)+')')]
    (ROOT/'docs/dungeons/target-content.json').write_text(json.dumps(target,indent=2)+'\n')
    adapted=adapt(donor,target)
    (ROOT/'docs/dungeons/classic-ct-adapted.json').write_text(json.dumps(adapted,indent=2)+'\n')
    print(json.dumps({k:len(v) for k,v in adapted['tables'].items()}))

if __name__=='__main__':main()
