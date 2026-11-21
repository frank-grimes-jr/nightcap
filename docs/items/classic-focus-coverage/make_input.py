"""Create matched stock-only progression fixtures and legal sustain AA prefixes."""
import collections,gzip,json,sys
from pathlib import Path
from analyze import load,active,HERE
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
        for a,n in ((28,3),(33,3),(34,3),(150,3),(18,9),(19,6)):buy(a,n)
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
                assert r['classes']&mask and r['races']&1 and r['slots']&(1<<slot) and r['reqlevel']<=level
                candidates=[r]
            candidates=[r for r in candidates if not (r['loregroup']==-1 and r['id'] in taken) and not (r['loregroup']>0 and r['loregroup'] in lores)]
            if not candidates:continue
            r=max(candidates,key=lambda r:(r['hp']+r['mana']*.5+r['ac']*8+r['awis']*3+r['healamt']*4,-r['id']))
            taken.add(r['id']);lores.add(r['loregroup']);slots.append([slot,r['id'],[]])
        return sorted(slots)
    stages=[('early',20,[3,1],63009,63,{1:10351,5:10359,15:10318}),
        ('mid_pal',35,[3,1],66011,66,{1:10407,4:10339,15:10355}),
        ('mid_clr',35,[2,1],66011,66,{1:10407,4:10339,15:10355}),
        ('mid_dru',35,[6,1],66011,66,{1:10407,4:10339,15:10355}),
        ('mid_shm',35,[10,1],66011,66,{1:10407,4:10339,15:10355}),
        ('pre_raid',50,[3,1],32002,32,{3:1411,8:1409,20:2406}),
        ('raid',50,[3,1],73057,73,{3:11052,6:1557,15:20747,9:4344})]
    cases=[];builds=[]
    for index,(name,level,classes,npc,z,forced) in enumerate(stages):
        slots=gear(classes,level,name=='raid',forced)
        selected,spent=aa_selection(classes,{20:40,35:100,50:200}[level])
        builds.append(dict(id=name,classes=classes,level=level,slots=slots,aa_rank_ids=selected,aa_spent=spent))
        for aa_on in (False,True):
            for spell in ((200,17) if level==20 else (17,12) if name=='mid_pal' else (17,15)):
                for seed in range(1,6):
                    cases.append(dict(id=f'{name}-aa{int(aa_on)}-spell{spell}-seed{seed}',level=level,classes=classes,
                        character_id=920100+index,slots=slots,aa_rank_ids=selected if aa_on else [],aa_budget=spent if aa_on else 0,
                        heal_spell=spell,npc_id=npc,zone_id=z,duration_ms=180000,channeling=min(200,level*5),seed=seed,attackers=1,heal_at_percent=75))
    policy=json.loads((HERE/'policy.json').read_text())['families']
    out=dict(rules=json.loads((HERE/'runtime.json').read_bytes())['rules'],
        policy={str(int(b)+200000*t):v for b,v in policy.items() for t in range(4)},cases=cases)
    (HERE/'input.json').write_text(json.dumps(out,indent=2)+'\n')
    (HERE/'loadouts.json').write_text(json.dumps(dict(scope='Stock legal fixtures selected by a fixed HP/AC/mana score, with focus target slots held identical before/after. No claim of complete BiS. AA sustain selections, not all legal AAs. No buffs/pets/regeneration.',builds=builds),indent=2)+'\n')
    print('cases',len(cases),'AA spent',[b['aa_spent'] for b in builds])
if __name__=='__main__':main()
