"""Bounded SK-main native arena calibration; no live database or service writes."""
import copy,gzip,hashlib,json,sys
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
        if item['slot']==13:item.update(id=605403,augments=[])
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
    report=dict(scope='Level50 Human SK/CLR/MNK, maximum legal purchased AA, inherited strong current-drop gear with non-undead weapon605403. Native melee/Monk buttons/Mend, Lifedraw and Superior Healing. Valor/Symbol preparation. Fixed controller excludes SK pet, Life Leech, optimal activated SK AAs, quest Perl/adds and Kael movement; no claim of global BiS or full encounter acceptance.',
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

if __name__=='__main__':run()
