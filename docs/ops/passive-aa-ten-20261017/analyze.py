"""Reproduce the private read-only AA pool calculation from the captured data."""
import collections
import gzip
import json
import sys
from pathlib import Path

ROOT=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[3]
HERE=ROOT/'docs/ops/passive-aa-ten-20261017'
sys.path.insert(0,str(ROOT/'tools'))
import aa_tbs_policy as policy

capture=json.loads(gzip.decompress((HERE/'production-snapshot.json.gz').read_bytes()))
tables=capture['tables'];config=json.loads((ROOT/'config/aa-policy.json').read_text())
fixture=json.loads(gzip.decompress((ROOT/config['catalog']).read_bytes()))
assert all(sorted(tables[k],key=lambda x:json.dumps(x,sort_keys=True))==sorted(rows,key=lambda x:json.dumps(x,sort_keys=True)) for k,rows in fixture.items())
abilities={x['id']:x for x in tables['aa_ability']}
ranks={x['id']:x for x in tables['aa_ranks']}
byfirst={x['first_rank_id']:x for x in tables['aa_ability']}
earned={byfirst[x['aa_id']]['id']:x['aa_value'] for x in tables['purchases']}
player=tables['palwar'][0]
mask=sum(1<<(player[key]-1) for key in ('class','class2','class3'))
allrows=policy.compile_policy(tables,config)
legal={(x['ability_id'],x['ordinal']):x for x in allrows if x['classes']&mask}
while True:
    removed=[key for key,row in legal.items() if any((aid,n) not in legal for aid,n in row['prereqs'].items())]
    if not removed:break
    for key in removed:del legal[key]
total=sum(ranks[row['rank_id']]['cost'] for row in legal.values())
spent=sum(ranks[row['rank_id']]['cost'] for row in legal.values() if row['ordinal']<=earned.get(row['ability_id'],0))
dormant=[]
for aid,count in earned.items():
    rid=abilities[aid]['first_rank_id']
    for ordinal in range(1,count+1):
        row=ranks[rid]
        if (aid,ordinal) not in legal:
            dormant.append({'ability_id':aid,'name':abilities[aid]['name'],'ordinal':ordinal,'rank_id':rid,'cost':row['cost']})
        rid=row['next_id']
assert spent+sum(row['cost'] for row in dormant)==player['aa_points_spent']
def threshold(level):
    modifier=1 if level<31 else 1.1 if level<36 else 1.2 if level<41 else 1.3 if level<46 else 1.4
    return round((level-1)**3*modifier*1000)
report={
 'captured_utc':capture['captured_utc'],'catalog_matches_fixture':True,
 'policy_id':config['id'],'global_families':len({x['ability_id'] for x in allrows}),'global_ranks':len(allrows),
 'palwar':player,'class_prerequisite_closed_pool':{'families':len({x['ability_id'] for x in legal.values()}),'ranks':len(legal),'total_cost':total,'owned_legal_cost':spent,'unbought_cost':total-spent,'banked_points':player['aa_points'],'new_points_needed':total-spent-player['aa_points']},
 'other_catalog_gates':dict(collections.Counter(str((abilities[x['ability_id']]['races'],abilities[x['ability_id']]['deities'],abilities[x['ability_id']]['status'])) for x in legal.values())),
 'dormant_earned_ranks':dormant,
 'key_owned':[{'ability_id':aid,'name':abilities[aid]['name'],'owned':earned.get(aid,0),'legal_cap':max((x['ordinal'] for x in legal.values() if x['ability_id']==aid),default=0)} for aid in [18,19,20,28,30,33,34,75,97,206,271,605]],
 'ideal_cumulative_aa_by_level':[{'level':lv,'normal_xp_threshold':threshold(lv),'at_10_percent':threshold(lv)/40000,'at_20_percent':threshold(lv)/20000} for lv in [10,20,27,30,35,40,50]],
 'ideal_xp_when_remaining_pool_funded':player['exp']+(total-spent-player['aa_points'])*40000,
 'limits':'Catalog/prerequisite costs are not combat strength. Ideal curve assumes equal normal/AA modifiers, passive mode, no XP losses, boosts, special rewards or prior-rate changes; ignores per-award integer rounding. Player history cannot be reconstructed from this snapshot.'
}
(HERE/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ('key_owned','ideal_cumulative_aa_by_level')},indent=2))
