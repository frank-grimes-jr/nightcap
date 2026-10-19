"""Reproducible THJ custom AA content; offline, guarded, no character SQL."""
import argparse
from collections import defaultdict
from copy import deepcopy
from functools import lru_cache
import gzip,json
from pathlib import Path
from aa_tbs_policy import compile_policy,header
from wpm_migration import migration

ROOT=Path(__file__).resolve().parents[1]
RELEASE=ROOT/'docs/releases/thj-behaviors-20261019'
RETIRED=(25,252,8300,3521,3522,758)
BURNS={565:8450,793:8451,794:8452,625:11068}
CASTERS=sum(1<<(n-1) for n in (2,3,4,5,6,8,10,11,12,13,14,15))

@lru_cache(maxsize=1)
def snapshot():
    return json.loads(gzip.decompress((ROOT/'tools/fixtures/thj-behaviors-20261019.json.gz').read_bytes()))

def chain(aid,abilities,ranks):
    rid=abilities[aid]['first_rank_id'];seen=set()
    while rid in ranks:
        if rid in seen:raise ValueError('AA cycle')
        seen.add(rid);yield ranks[rid];rid=ranks[rid]['next_id']

def reset_effects(row,values):
    for i in range(1,13):
        row.update({f'effectid{i}':254,f'effect_base_value{i}':0,f'effect_limit_value{i}':0,f'max{i}':0,f'formula{i}':100})
    for i,(spa,base,limit) in enumerate(values,1):
        row.update({f'effectid{i}':spa,f'effect_base_value{i}':base,f'effect_limit_value{i}':limit})

def prepare():
    tables=deepcopy(snapshot()['tables'])
    policy=json.loads((RELEASE/'baseline-policy.json').read_text())
    abilities={a['id']:a for a in tables['aa_ability']};ranks={r['id']:r for r in tables['aa_ranks']}
    spells={s['id']:s for s in tables['spells_new']}
    policy.update(id='thj-behaviors-20261019',catalog='tools/fixtures/aa-thj-behaviors-catalog.json.gz',
        notes='THJ released May7 custom behaviors; native and calibrated parameters are explicit in thj-behaviors-20261019. Classic50 and starter grants preserved.')
    for aid in RETIRED:
        policy['rank_caps'][str(aid)]=0
        if aid not in policy['deferred_abilities']:policy['deferred_abilities'].append(aid)
    for aid,cap in {912:1,565:1,793:1,794:1,625:1,1156:6,30201:1}.items():
        policy['rank_caps'][str(aid)]=cap
        if aid in policy['deferred_abilities']:policy['deferred_abilities'].remove(aid)
        needs_exception=aid in abilities and any(r['expansion']>policy['expansion_max'] for r in list(chain(aid,abilities,ranks))[:cap])
        if needs_exception and aid not in policy['later_exceptions']:policy['later_exceptions'].append(aid)
        if not needs_exception and aid in policy['later_exceptions']:policy['later_exceptions'].remove(aid)
    abilities[500]['classes']=CASTERS
    for rank in chain(500,abilities,ranks):
        rank['recast_time']=60
        s=spells[rank['spell']];s.update(buffdurationformula=4,buffduration=600,suspendable=1)
    # A sourced rewrite of the exact native family, with native12AA purchase cost.
    ranks[10546]['recast_time']=60
    s=spells[23528];reset_effects(s,[(185,100,-1)])
    s.update(buffdurationformula=4,buffduration=2)
    # Opening1HP and50AC/50avoidance are explicit candidate calibrations.
    for sid,spa,base in ((5939,1,-50),(11033,172,-50),(12802,197,50)):
        s=spells[sid];reset_effects(s,[(79,-1,0),(spa,base,-1 if spa==197 else 0)])
        s.update(buffdurationformula=4,buffduration=2)
    s=spells[2775];reset_effects(s,[(79,1,0)])
    s.update(targettype=41,aoerange=100,can_mgb=0,buffdurationformula=0,buffduration=0,mana=0)
    for rank in chain(172,abilities,ranks):
        s=spells[rank['spell']];reset_effects(s,[(358,1,0)])
    # Six retained6-minute haste steps plus51-minute base reaches sourced15minutes.
    for aid,sid in BURNS.items():
        rank=next(chain(aid,abilities,ranks));rank['recast_time']=3060
        s=spells[sid];reset_effects(s,[(350,0,-40),(148,350,0)])
        s.update(buffdurationformula=4,buffduration=10,mana=0)
        s['formula2']=201;s['max2']=100000
    for rank in chain(1156,abilities,ranks):
        effects=[e for e in tables['aa_rank_effects'] if e['rank_id']==rank['id']]
        if not effects:raise ValueError('Missing mana haste')
        if not any(e['base2']==625 for e in effects):
            tables['aa_rank_effects'].append(dict(rank_id=rank['id'],slot=max(e['slot'] for e in effects)+1,
                effect_id=264,base1=effects[0]['base1'],base2=625))
    # Do not overwrite the unrelated native Dimensional Shield teleport proc.
    if 30201 in abilities or 43220 in ranks or 43220 in spells:raise ValueError('Reserved custom identity occupied')
    ability=dict(abilities[492],id=30201,name='[WIZ] Dimensional Shielding',classes=2048,first_rank_id=43220)
    rank=dict(ranks[12866],id=43220,spell=43220,title_sid=43220,desc_sid=43220,upper_hotkey_sid=43220,
        lower_hotkey_sid=43220,prev_id=-1,next_id=-1,expansion=13,level_req=1)
    s=dict(spells[27424],id=43220,name='Dimensional Shielding',spellgroup=43220,descnum=43220)
    reset_effects(s,[(10,0,0)])
    s.update(buffdurationformula=4,buffduration=20)
    tables['aa_ability'].append(ability);tables['aa_ranks'].append(rank);tables['spells_new'].append(s)
    # Exact released absolute values; runtime generic focus multiplier excludes these.
    for sid,value in ((5915,100),(11064,150)):
        spells[sid]['effect_base_value1']=value;spells[sid]['effect_limit_value1']=value
    # Retain trigger school, level, mana and cast-time limits; no unsourced broadening.
    for aid in (514,640):
        cap=policy['rank_caps'].get(str(aid),policy['default_max_ranks'])
        for rank in list(chain(aid,abilities,ranks))[:cap]:
            s=spells[rank['spell']]
            i=next(i for i in range(1,13) if s[f'effectid{i}']==339)
            s[f'effect_base_value{i}']=35
            proc=spells[s[f'effect_limit_value{i}']]
            if aid==514:
                tick=next(abs(proc[f'effect_base_value{j}']) for j in range(1,13) if proc[f'effectid{j}']==0)
                resist=next(abs(proc[f'effect_base_value{j}']) for j in range(1,13) if proc[f'effectid{j}']==46)
                reset_effects(proc,[(79,-tick,0),(0,-tick,0),(47,-resist,0)])
            else:
                damage=next(abs(proc[f'effect_base_value{j}']) for j in range(1,13) if proc[f'effectid{j}']==79)
                resist=next(abs(proc[f'effect_base_value{j}']) for j in range(1,13) if proc[f'effectid{j}']==47)
                # Keep the existing initial damage; divide it over existing duration for addedDoT.
                ticks=max(1,proc['buffduration'])
                reset_effects(proc,[(79,-damage,0),(0,-max(1,damage//ticks),0),(46,-resist,0)])
                proc.update(buffdurationformula=4,buffduration=ticks)
    # Canonical native song membership, not the casting character's primary class.
    for s in spells.values():
        if 0<s['classes8']<255 and s['cast_time']==3000:s['cast_time']=2500
    policy['deferred_abilities']=sorted(set(policy['deferred_abilities']))
    policy['later_exceptions']=sorted(set(policy['later_exceptions']))
    for name,rows in tables.items():
        keys=('rank_id','slot') if name=='aa_rank_effects' else ('rank_id','aa_id') if name=='aa_rank_prereqs' else ('id',)
        rows.sort(key=lambda row:tuple(row[k] for k in keys))
    return tables,policy

def groups():
    before=snapshot()['tables'];after,_=prepare();out=[]
    for table in before:
        key='rank_id' if table in ('aa_rank_effects','aa_rank_prereqs') else 'id'
        old,new=defaultdict(list),defaultdict(list)
        for row in before[table]:old[row[key]].append(row)
        for row in after[table]:new[row[key]].append(row)
        for value in sorted(old.keys()|new.keys()):
            if old[value]!=new[value]:out.append(dict(table=table,key={key:value},before=old[value],after=new[value]))
    return out

def main():
    after,policy=prepare();catalog={k:v for k,v in after.items() if k!='spells_new'}
    rows=compile_policy(catalog,policy)
    (ROOT/'config/aa-policy.json').write_text(json.dumps(policy,indent=2)+'\n')
    (ROOT/policy['catalog']).write_bytes(gzip.compress(json.dumps(catalog,separators=(',',':')).encode(),mtime=0))
    (ROOT/'server-mods/code/common/nightcap_aa_policy.h').write_text(header(rows,policy,catalog))
    gs=groups()
    (RELEASE/'content-forward.sql').write_text(migration(gs,'nightcap_thj_behaviors_20261019'))
    # New identities remain for earned state; disable by older policy/binary, never delete.
    reverse=[dict(g,before=g['after'],after=g['before']) for g in gs if g['before']]
    (RELEASE/'content-rollback.sql').write_text(migration(reverse,'nightcap_thj_behaviors_rollback'))
    (RELEASE/'content-plan.json').write_text(json.dumps(gs,indent=2)+'\n')
    rule=dict(ruleset_id=1,rule_name='Spells:NightcapTHJBehaviors',rule_value='true',notes='THJ behavior candidate; paired world/zone, content and client required')
    disabled=dict(rule,rule_value='false')
    for name,old,new in [('forward',[],[rule]),('disable',[rule],[disabled]),('enable',[disabled],[rule])]:
        group=dict(table='rule_values',key={'ruleset_id':1,'rule_name':rule['rule_name']},before=old,after=new)
        (RELEASE/f'rule-{name}.sql').write_text(migration([group],'nightcap_thj_behavior_rule'))
    print(json.dumps({'ranks':len(rows),'families':len({r['ability_id'] for r in rows}),'changed_groups':len(gs)}))

if __name__=='__main__':main()
