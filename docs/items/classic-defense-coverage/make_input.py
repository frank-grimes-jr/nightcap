"""Create matched stock-only progression fixtures and legal sustain AA prefixes."""
import collections,gzip,json,sys
from pathlib import Path
from analyze import load,HERE
from coverage import routes as active
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from aa_tbs_policy import compile_policy

def main():
    data=load();items={r['id']:r for r in data['items']};routes=active(data)
    config=json.loads((ROOT/'config/aa-policy.json').read_text())
    aa=json.loads(gzip.decompress((ROOT/config['catalog']).read_bytes()))
    allowed=compile_policy(aa,config);ranks={r['id']:r for r in aa['aa_ranks']}
    def aa_selection(classes,budget):
        mask=sum(1<<(c-1) for c in classes);chosen=[];owned=collections.Counter();spent=0
        by={(r['ability_id'],r['ordinal']):r for r in allowed}
        def buy(a,n):
            nonlocal spent
            if owned[a]>=n:return True
            r=by.get((a,n))
            if not r or not r['classes']&mask:return False
            if n>1 and not buy(a,n-1):return False
            for dep,count in r['prereqs'].items():
                if a==150 and dep==26 and mask&16942:continue
                if not buy(dep,count):return False
            cost=ranks[r['rank_id']]['cost']
            if spent+cost>budget:return False
            chosen.append(r['rank_id']);owned[a]=n;spent+=cost;return True
        for a,n in ((28,3),(33,3),(34,3),(150,3),(18,9),(19,6),(120,1),(435,3)):buy(a,n)
        return chosen,spent
    def gear(classes,level,raid,forced):
        mask=sum(1<<(c-1) for c in classes);tier=3 if raid else 0
        eligible={r['item'] for r in routes if (r['zoneid']<=77 or raid and r['zone']=='hateplaneb') and
            (raid or r['zone'] not in ('airplane','fearplane','hateplane','hateplaneb')) and r['npc_level']<= (70 if raid else level+2)}
        pool=[items[b+200000*tier] for b in eligible if b+200000*tier in items]
        pool=[r for r in pool if r['classes']&mask and r['races']&1 and r['reqlevel']<=level and r['reclevel']<=level]
        taken=set();lores=set();slots=[]
        for slot in (13,14,17,18,19,2,7,12,6,8,9,10,1,4,3,5,11,15,16,20):
            candidates=[r for r in pool if r['slots']&(1<<slot)]
            if slot==13:candidates=[r for r in candidates if r['itemtype'] in (0,2,3)]
            if slot==14:candidates=[r for r in candidates if r['itemtype']==8]
            if slot in forced:
                r=items[forced[slot]+200000*tier]
                assert r['classes']&mask and r['races']&1 and r['slots']&(1<<slot) and r['reqlevel']<=level,(slot,r['Name'],classes,r['slots'])
                candidates=[r]
            candidates=[r for r in candidates if not (r['loregroup']==-1 and r['id'] in taken) and not (r['loregroup']>0 and r['loregroup'] in lores)]
            if not candidates:continue
            r=max(candidates,key=lambda r:(r['hp']+r['mana']*.5+r['ac']*8+r['awis']*3+r['healamt']*4,-r['id']))
            taken.add(r['id']);lores.add(r['loregroup']);slots.append([slot,r['id'],[]])
        return sorted(slots)
    stages=[('early',20,[3,1],63009,63,{1:10354,15:10350,9:10120,2:10122,14:9307,10:2299}),
        ('mid_pal',35,[3,1],66011,66,{15:10312,16:10337,8:2340,2:1302}),
        ('mid_clr',35,[2,1],66011,66,{15:10312,16:10337,8:2340,2:1302}),
        ('mid_dru',35,[6,1],66011,66,{15:10312,16:10337,8:2340,2:1302}),
        ('mid_shm',35,[10,1],66011,66,{15:10312,16:10337,8:2340,2:1302}),
        ('pre_raid',50,[3,1],32002,32,{15:10364,16:10337,12:4306,2:1302,19:4407,14:9311,6:4302}),
        ('raid',50,[3,1],73057,73,{17:4852,12:4855,9:4854,2:4341,19:4407,14:9403,6:1557})]
    cases=[];builds=[]
    for index,(name,level,classes,npc,z,forced) in enumerate(stages):
        slots=gear(classes,level,name=='raid',forced)
        selected,spent=aa_selection(classes,{20:40,35:100,50:200}[level])
        builds.append(dict(id=name,classes=classes,level=level,slots=slots,aa_rank_ids=selected,aa_spent=spent))
        for aa_on in (False,True):
            for spell in ((200,17) if level==20 else (17,12) if name=='mid_pal' else (17,15)):
                for seed in range(1,4):
                    cases.append(dict(id=f'{name}-aa{int(aa_on)}-spell{spell}-seed{seed}',level=level,classes=classes,
                        character_id=920100+index,slots=slots,aa_rank_ids=selected if aa_on else [],aa_budget=spent if aa_on else 0,
                        heal_spell=spell,npc_id=npc,zone_id=z,duration_ms=180000,channeling=min(200,level*5),seed=seed,attackers=1,heal_at_percent=75))
    policy=json.loads((HERE/'policy.json').read_text())['families']
    out=dict(rules=json.loads((HERE/'runtime.json').read_bytes())['rules'],
        policy={str(int(b)+200000*t):v for b,v in policy.items() for t in range(4)},cases=cases)
    # Full prior endgame augment sets exercise unchanged Dodging scale interaction.
    prior=json.loads((ROOT/'docs/items/classic-focus-coverage/stress-input.json').read_bytes())
    for c in prior['cases']:
        if 'full' in c['id'] or 'dodge' in c['id']:
            if c.get('seed',1)<=3:out['cases'].append(c)
    pressure=[c for c in cases if c['seed']==1 and (c['id'].startswith('pre_raid-') or c['id'].startswith('raid-'))]
    for c in pressure:
        for seed in range(11,21):out['cases'].append({**c,'id':'pressure-'+c['id']+'-'+str(seed),'seed':seed,'attackers':3})
    out['defense_cases']=[]
    for ident,entry in policy.items():
        base=items[int(ident)]
        # Exhaustive policy hosts at base and Ascended quality; no synthetic stats/effects.
        cl=next(c for c in range(1,17) if base['classes']&(1<<(c-1)))
        race=next(c for c in range(1,13) if base['races']&(1<<(c-1)))
        slot=next(s for s in range(1,22) if base['slots']&(1<<s))
        for tier in (0,3):
            out['defense_cases'].append(dict(id=f'host-{ident}-tier{tier}',classes=[cl],race=race,level=50,character_id=0,slots=[[slot,int(ident)+tier*200000,[]]],aa_budget=0,aa_rank_ids=[]))
    for b in builds:
        for aa_on in (False,True):
            c=next(c for c in cases if c['id'].startswith(b['id']+'-') and bool(c['aa_rank_ids'])==aa_on)
            out['defense_cases'].append({**c,'id':'full-'+b['id']+'-aa'+str(int(aa_on))})
    # A pure caster wears the same accessible Dodge effect without an added warrior class.
    for cl in (2,6,10,11,12,13,14):
        out['defense_cases'].append(dict(id=f'pure-class-{cl}',classes=[cl],race=1,level=50,character_id=0,slots=[[6,601557,[]],[2,604341,[]],[19,604407,[]]],aa_budget=0,aa_rank_ids=[]))
    (HERE/'input.json').write_text(json.dumps(out,indent=2)+'\n')
    (HERE/'loadouts.json').write_text(json.dumps(dict(scope='Stock legal fixtures selected by a fixed HP/AC/mana score, with focus target slots held identical before/after. No claim of complete BiS. AA sustain selections, not all legal AAs. No buffs/pets/regeneration.',builds=builds),indent=2)+'\n')
    print('cases',len(cases),'AA spent',[b['aa_spent'] for b in builds])
if __name__=='__main__':main()
