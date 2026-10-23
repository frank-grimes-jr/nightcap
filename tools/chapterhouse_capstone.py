"""Current-content maximum-AA capstone calibration, including Ghoulbane/proc controls."""
import argparse,collections,copy,gzip,hashlib,json,sys
from chapterhouse_balance import OUT,ROOT,DB,sql,remote,RUNTIME,execute
from chapterhouse_content import compile_rows
from dungeon_migration import insert
sys.path.insert(0,str(ROOT/'tools/balance'))
from aa_allocations import Purchases

def maximum():
    base=json.loads(remote(f"from pathlib import Path; print(Path({RUNTIME!r}+'/base-input.json').read_text())"))
    probe=copy.deepcopy(base);probe.pop('encounter');probe['export_aa_catalog']=True
    probe['builds'][0].update(aa_budget=0,aa_rank_ids=[],aa_stage='current catalog',aa_policy='fresh production public content; current compiled release policy')
    result=execute('capstone-catalog',probe)
    ranks=result['builds'][0]['aa_catalog']
    if isinstance(ranks,dict):ranks=ranks['ranks']
    p=Purchases(ranks);p.free_closure();excluded=p.all_closure()
    (OUT/'capstone-aa.json').write_text(json.dumps(dict(spent=p.spent,owned=list(p.owned.values()),excluded=excluded),indent=2)+'\n')
    b=base['builds'][0];b.update(aa_budget=p.spent,aa_rank_ids=p.ids,aa_stage='all legal purchased',aa_policy='current compiled eligibility and actual native purchases')
    # Both spells have original Paladin <=50 access and are in the reviewed hub pool.
    base['encounter'].update(duration_ms=240000,preparation=dict(spell_ids=[2583,312],recover=True))
    print('Current maximum legal AA spent:',p.spent,flush=True)
    return base,p

def compact(output):
    b=output['builds'][0];e=output['encounter'];by_spell=collections.defaultdict(lambda:dict(hits=0,damage=0))
    for hit in e['damage_ledger']:
        if hit['depth']!=0:continue
        damage=max(0,min(hit['hp_before'],hit['hp_before']-hit['hp_after']))
        if damage:
            by_spell[str(hit['spell'])]['hits']+=1;by_spell[str(hit['spell'])]['damage']+=damage
    prepared=e.get('preparation',{}).get('final_state',{})
    hp=prepared.get('max_hp',b['hp']);mana=prepared.get('max_mana',b['mana']);trace=e['trace']
    return dict(result=e['result'],seconds=e['elapsed_ms']/1000,hp=hp,mana=mana,
        hp_floor_pct=round(min(t['player_hp'] for t in trace)/hp*100,1),
        mana_floor_pct=round(min(t['player_mana'] for t in trace)/mana*100,1),
        npc_remaining=trace[-1]['npc_hp'],damage_by_spell=dict(by_spell),
        mend_requests=len(e['mend_requests']),spell_attempts=len(e['attempts']),
        aa_spent=b['aa_spent'],slay_messages=sum(x.get('string_id') in (1007,1008) for x in e['events']),
        preparation=prepared)

def case(base,boss,mode,weapon,seed,label='max'):
    enemy=dict(boss,id=32040)
    if mode=='Raid':enemy['hp']=int(enemy['hp']*1.35)
    sql(insert('npc_types',enemy).replace('INSERT INTO','REPLACE INTO',1))
    data=copy.deepcopy(base);data['encounter']['chapterhouse_raid']=mode=='Raid'
    if weapon!=662038:
        primary=next(i for i in data['builds'][0]['equipment'] if i['slot']==13)
        primary['id']=weapon
        # Weapon sockets differ; preserve only validated existing compatible augments.
        primary['augments']=[]
    name=f'capstone-{boss["id"]}-{mode.lower()}-{weapon}-{label}-{seed}'
    output=execute(name,data,seed)
    assert output['encounter']['trace'][0]['npc_hp']==enemy['hp'], 'Unexpected initial native HP scaling'
    result=dict(case=name,boss=boss['id'],mode=mode,weapon=weapon,seed=seed,stats=enemy,**compact(output))
    for suffix in ('-result.json','.log'):
        path=OUT/(name+suffix);raw=path.read_bytes();packed=gzip.compress(raw,mtime=0)
        assert gzip.decompress(packed)==raw
        path.with_name(path.name+'.gz').write_bytes(packed);path.unlink()
        result[suffix+'_sha256']=hashlib.sha256(raw).hexdigest()
    print(name,json.dumps({k:result[k] for k in ('result','seconds','hp_floor_pct','mana_floor_pct','npc_remaining')}),flush=True)
    return result

def run(quick=False):
    base,p=maximum();bosses=[n for n in compile_rows()['npc_types'] if 998821<=n['id']<=998824]
    rows=[]
    if quick:cases=[(bosses[-1],'Grind',w,101) for w in (662038,605403)]
    else:cases=[(b,m,w,s) for b in bosses for m in ('Grind','Raid') for w in (662038,605403) for s in (101,2718,8675309)]
    report=dict(scope='Level50 WAR/PAL/MNK, actual full legal AA purchases, fresh production public definitions. Strong current-drop gear, not proof of global BiS. Native preparation, melee/skills, Stun, Mend, heals and earned Rage of Rallos. Quest timers/adds and Chapterhouse movement excluded.',raid='135% starting HP; native CommonDamage applies 115% after calculation via diagnostic-only RaidNPC predicate',public_capture_sha256=hashlib.sha256((OUT/'balance-public-content.json.gz').read_bytes()).hexdigest(),legal_max_spent=p.spent,cases=rows)
    path=OUT/('capstone-quick.json' if quick else 'capstone-results.json')
    for b,m,w,s in cases:
        rows.append(case(base,b,m,w,s));path.write_text(json.dumps(report,indent=2)+'\n')

def controls():
    base,p=maximum();bosses=[n for n in compile_rows()['npc_types'] if n['id'] in (998821,998824)];rows=[]
    for budget in (98,500):
        data=copy.deepcopy(base);q=Purchases(list(p.ranks.values()));q.free_closure()
        for rank_id in p.ids:
            rank=q.ranks[rank_id]
            if not q.reasons(rank) and q.spent+rank['cost']<=budget:q.buy(rank)
        build=data['builds'][0];build.update(aa_budget=q.spent,aa_rank_ids=q.ids)
        seen=set()
        for item in build['equipment']:
            item['id']=item['id']%200000+200000
            if item['id'] in seen:item['id']%=200000
            seen.add(item['id']);item['augments']=[]
        for boss in bosses:rows.append(case(data,boss,'Grind',205403,101,str(q.spent)+'AA-Polished'))
    rows.append(case(base,dict(bosses[-1],bodytype=1),'Grind',605403,101,'living-control'))
    (OUT/'capstone-controls.json').write_text(json.dumps(rows,indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--quick',action='store_true');p.add_argument('--controls',action='store_true');a=p.parse_args()
    if a.controls:controls()
    else:run(a.quick)
