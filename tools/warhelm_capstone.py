"""Bounded SK-main native arena calibration; no live database or service writes."""
import argparse,copy,gzip,hashlib,json,sys
from warhelm_balance import OUT,ROOT,sql,remote,RUNTIME,execute
from warhelm_content import compile_rows
from dungeon_migration import insert
from chapterhouse_capstone import compact
sys.path.insert(0,str(ROOT/'tools/balance'))
from aa_allocations import Purchases

def maximum():
    base=json.loads(remote(f"from pathlib import Path;print(Path({RUNTIME!r}+'/base-input.json').read_text())"))
    b=base['builds'][0]
    b.update(profile='sk-clr-mnk',classes=[5,2,7],deity='Bertoxxulous',aa_budget=0,aa_rank_ids=[],casting_stat_scored='int',aa_policy='current native legal purchases')
    fields=','.join("'"+s+"',a.base_"+s+'+a.alloc_'+s for s in ('str','sta','dex','agi','int','wis','cha'))
    creation=sql('SELECT JSON_OBJECT('+fields+') FROM char_create_point_allocations a JOIN char_create_combinations c ON c.allocation_id=a.id WHERE c.race=1 AND c.class=5 AND c.deity=201 AND c.expansions_req=0;').strip().splitlines()
    assert len(creation)==1,'Expected one reviewed Classic Human Shadow Knight allocation'
    b['creation']=json.loads(creation[0])
    # Only this isolated synthetic row is changed; the diagnostic verifies it.
    sql('UPDATE character_data SET class=5 WHERE id=90022; UPDATE character_multiclass SET class2=2,class3=7 WHERE character_id=90022;')
    for item in b['equipment']:
        # The inherited Indicolite hands/feet require Warrior. Darkforge is
        # legal SK armor with the same socket type. Keep the proc-free Tonfa
        # through held Monk;605403 is Paladin-only Ghoulbane, not a control.
        if item['slot']==12:item['id']=603144
        if item['slot']==19:item['id']=603146
        if item['slot']==13:item.update(id=662038,augments=[])
    probe=copy.deepcopy(base);probe.pop('encounter');probe['export_aa_catalog']=True
    result=execute('sk-catalog',probe)
    ranks=result['builds'][0]['aa_catalog']
    if isinstance(ranks,dict):ranks=ranks['ranks']
    p=Purchases(ranks);p.free_closure();excluded=p.all_closure()
    b.update(aa_budget=p.spent,aa_rank_ids=p.ids,aa_stage='all legal purchased')
    base['encounter'].update(combat_policy='skm',active_aa_policy='burst_regeneration',duration_ms=300000,
        preparation=dict(spell_ids=[312,487],recover=True))
    (OUT/'sk-aa.json').write_text(json.dumps(dict(spent=p.spent,excluded=excluded,owned=list(p.owned.values())),indent=2)+'\n')
    return base,p

def run():
    base,p=maximum();cases=[]
    report=dict(scope='Level50 Human SK/CLR/MNK, maximum legal purchased AA, inherited strong gear with class-legal Darkforge hands603144/feet603146 and proc-free Balanced Tonfa662038 through held Monk. Native melee/Monk buttons/Mend, Lifedraw and Superior Healing. Valor/Symbol preparation. Fixed controller excludes SK pet, Life Leech, optimal activated SK AAs, quest Perl/adds and Kael movement; no claim of global BiS or full encounter acceptance.',
        public_content='October23 Camil synthetic capture; source receipt retained in docs/quests/camil-chapterhouse',aa_spent=p.spent,cases=cases)
    bosses=[n for n in compile_rows()['npc_types'] if 998861<=n['id']<=998864]
    for boss in bosses:
        for mode in ('Grind','Raid'):
            for seed in (101,2718,8675309):
                enemy=dict(boss,id=32040)
                if mode=='Raid':enemy['hp']=int(enemy['hp']*1.35)
                sql(insert('npc_types',enemy).replace('INSERT INTO','REPLACE INTO',1))
                data=copy.deepcopy(base);data['encounter']['chapterhouse_raid']=mode=='Raid'
                name=f'sk-{boss["id"]}-{mode.lower()}-{seed}'
                output=execute(name,data,seed)
                assert output['encounter']['trace'][0]['npc_hp']==enemy['hp']
                row=dict(case=name,boss=boss['id'],mode=mode,seed=seed,stats=enemy,**compact(output));cases.append(row)
                for suffix in ('-result.json','.log'):
                    path=OUT/(name+suffix);raw=path.read_bytes();packed=gzip.compress(raw,mtime=0)
                    assert gzip.decompress(packed)==raw
                    path.with_name(path.name+'.gz').write_bytes(packed);path.unlink()
                    row[suffix+'_sha256']=hashlib.sha256(raw).hexdigest()
                (OUT/'sk-results.json').write_text(json.dumps(report,indent=2)+'\n')
                print(name,json.dumps({k:row[k] for k in ('result','seconds','hp_floor_pct','mana_floor_pct','npc_remaining')}),flush=True)

def controls():
    base,p=maximum()
    q=Purchases(list(p.ranks.values()));q.free_closure()
    for rank_id in p.ids:
        rank=q.ranks[rank_id]
        if not q.reasons(rank) and q.spent+rank['cost']<=500:q.buy(rank)
    b=base['builds'][0];b.update(aa_budget=q.spent,aa_rank_ids=q.ids,aa_stage='bounded500AA control')
    seen=set()
    for item in b['equipment']:
        item['id']=item['id']%200000+200000
        if item['id'] in seen:item['id']%=200000
        seen.add(item['id']);item['augments']=[]
    rows=[]
    for boss in [n for n in compile_rows()['npc_types'] if n['id'] in (998861,998864)]:
        enemy=dict(boss,id=32040);sql(insert('npc_types',enemy).replace('INSERT INTO','REPLACE INTO',1))
        for seed in (101,2718):
            name=f'sk-control-{boss["id"]}-{seed}'
            output=execute(name,base,seed)
            row=dict(case=name,boss=boss['id'],mode='Grind',seed=seed,stats=enemy,**compact(output));rows.append(row)
            for suffix in ('-result.json','.log'):
                path=OUT/(name+suffix);raw=path.read_bytes();packed=gzip.compress(raw,mtime=0)
                assert gzip.decompress(packed)==raw
                path.with_name(path.name+'.gz').write_bytes(packed);path.unlink()
                row[suffix+'_sha256']=hashlib.sha256(raw).hexdigest()
            (OUT/'sk-controls.json').write_text(json.dumps(dict(scope='Same SK/CLR/MNK controller; at most500legal AA, Polished gear, no augments. Progression contrast, not a minimum-entry recommendation.',cases=rows),indent=2)+'\n')
            print(name,json.dumps({k:row[k] for k in ('result','seconds','hp_floor_pct','mana_floor_pct','npc_remaining')}),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--controls',action='store_true');args=parser.parse_args()
    if args.controls:controls()
    else:run()
