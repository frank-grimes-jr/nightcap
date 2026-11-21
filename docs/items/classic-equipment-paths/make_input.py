"""Matched native fixtures: current stock caches, explicit legal item/AA pools."""
import copy,gzip,json,collections
from pathlib import Path
HERE=Path(__file__).resolve().parent
OLD=HERE.parent/'classic-defense-coverage'
def main():
 out=json.loads((OLD/'input.json').read_bytes());pol=json.loads((HERE/'policy.json').read_bytes())['families'];targets=json.loads(gzip.decompress((HERE/'targets.json.gz').read_bytes()));it={r['id']:r for r in targets['items']}
 out['rules']=json.loads((HERE/'runtime.json').read_bytes())['rules'];out['policy']={str(int(k)+200000*t):v for k,v in pol.items() for t in range(4)}
 out.pop('category_matrix',None);out.pop('focus_controls',None);out['defense_cases']=[];out['offense_cases']=[]
 for k,e in pol.items():
  b=it[int(k)];cl=next(n for n in range(1,17) if b['classes']&(1<<(n-1)));race=next(n if n<=12 else {13:128,14:130,15:330,16:522}[n] for n in range(1,17) if b['races']&(1<<(n-1)));deity=396
  if b['deity']:deity=next(200+n for n in range(1,17) if b['deity']&(1<<n)) if not b['deity']&1 else 396
  slot=next(n for n in range(22) if b['slots']&(1<<n))
  for t in (0,3):out['defense_cases'].append(dict(id=f'host-{k}-tier{t}',classes=[cl],race=race,deity=deity,level=50,character_id=0,slots=[[slot,int(k)+200000*t,[]]],aa_budget=0,aa_rank_ids=[]))
 # Preserve established full Prismatic/Dodging and current raid-loadout controls.
 for c in json.loads((OLD/'input.json').read_bytes())['defense_cases']:
  if c['id'].startswith('full'):out['defense_cases'].append(c)
 # New full legal normal-crafted and Ascended quest paths, paired against themselves.
 templates=[c for c in out['cases'] if c['id'].startswith('pre_raid-') and c['seed']==1]
 replacements={'fine_plate':{2:21001,6:21005,9:21009,10:21009,12:21010,17:21004,19:21012,15:14667,16:14663},'ro':{2:603150,7:603152,9:603153,12:603154,17:603151,18:603155,19:603156,15:614667,16:614663}}
 for name,rep in replacements.items():
  for original in templates:
   for seed in (51,52,53):
    c=copy.deepcopy(original);c['id']=name+'-'+c['id']+'-'+str(seed);c['seed']=seed;c['slots']=[[slot,rep.get(slot,item),augs] for slot,item,augs in c['slots']];out['cases'].append(c)
 # Haste: full legal paladin/warrior loadouts, no AA and legal current AA prefix.
 for c in out['cases']:
  if c['id'].startswith(('fine_plate-','ro-')) and c['heal_spell']==17:
   out['offense_cases'].append({**c,'id':'melee-'+c['id'],'spells':[],'timed_melee':True})
 # Real wizard spell-level gates; DD, area, DoT and lifetap separately. Item focus duplicates share a pool.
 for level in (20,35,50):
  for kind,cl,spells in [('direct',12,[732] if level==50 else [383]),('area',13,[83]),('dot_lifetap',11,[360 if level==20 else 451,445])]:
   for name,slots in [('none',[]),('damage',[[3,14683,[]]]),('dot',[[15,14675,[]]]),('both',[[3,14683,[]],[15,14675,[]]]),('damage_duplicate',[[3,14683,[]],[16,14682,[]]]),('dot_duplicate',[[15,14675,[]],[5,14674,[]]])]:
    out['offense_cases'].append(dict(id=f'spell-{level}-{kind}-{name}',classes=[cl],race=1,level=level,character_id=0,slots=slots,aa_budget=0,aa_rank_ids=[],spells=spells,timed_melee=False))
 # Combined endgame caster: legal stock raid equipment, current scale and offensive AA ranks.
 import sys
 sys.path.insert(0,str(HERE.parents[2]/'tools'))
 from aa_tbs_policy import compile_policy
 cfg=json.loads((HERE.parents[2]/'config/aa-policy.json').read_bytes());catalog=json.loads(gzip.decompress((HERE.parents[2]/cfg['catalog']).read_bytes()));allowed=compile_policy(catalog,cfg);ranks={r['id']:r for r in catalog['aa_ranks']}
 selected=[r['rank_id'] for ability,count in [(23,3),(114,6),(397,3)] for r in sorted(allowed,key=lambda r:r['ordinal']) if r['ability_id']==ability and r['ordinal']<=count]
 budget=sum(ranks[k]['cost'] for k in selected)
 data=json.loads(gzip.decompress((HERE/'production.json.gz').read_bytes()));pool=[r for r in data['items'] if r['id']>=600000 and r['classes']&2048 and r['races']&1 and not r['deity'] and r['reqlevel']<=50 and r['reclevel']<=50]
 slots=[];lores=set();used=set()
 for slot in [3,15,2,17,18,19,12,7,9,10,1,4,5,6,8,11,13,14,16,20]:
  candidates=[r for r in pool if r['slots']&(1<<slot) and (r['loregroup']!=-1 or r['id'] not in used) and (r['loregroup']<=0 or r['loregroup'] not in lores)]
  if slot in (3,15):r=it[{3:614683,15:614675}[slot]]
  elif candidates:r=max(candidates,key=lambda r:(r['hp']+r['mana']+5*r['aint']+r['spelldmg'], -r['id']))
  else:continue
  used.add(r['id']);lores.add(r['loregroup']);slots.append([slot,r['id'],[]])
 for aug in (False,True):
  for aa in (False,True):
   gear=copy.deepcopy(slots)
   if aug:
    host=next(v for v in gear if v[0] in (2,7,9,10,12,17,18,19) and next(r for r in pool if r['id']==v[1])['augslot1type']==7);host[2]=[609603]
   out['offense_cases'].append(dict(id=f'full-caster-aug{int(aug)}-aa{int(aa)}',classes=[12],race=1,level=50,character_id=0,slots=gear,aa_budget=budget if aa else 0,aa_rank_ids=selected if aa else [],spells=[732],timed_melee=False))
 # Haste must be checked below and above the new item's strength; use steady-state timer.
 baseline=next(c for c in out['offense_cases'] if c['id'].startswith('melee-ro-') and not c['aa_rank_ids'])
 allitems={r['id']:r for r in data['items']};allitems.update(it)
 for mode in ('no_haste','stronger_haste'):
  c=copy.deepcopy(baseline);c['id']='haste-control-'+mode
  c['slots']=[r for r in c['slots'] if not allitems[r[1]]['haste'] and r[0]!=8]
  if mode=='stronger_haste':c['slots'].append([8,11621,[]])
  out['offense_cases'].append(c)
 for c in list(out['offense_cases']):
  if c['id'].startswith('full-caster') and c['aa_rank_ids']:
   for seed in range(1,21):out['offense_cases'].append({**copy.deepcopy(c),'id':c['id']+'-seed'+str(seed),'seed':seed})
 (HERE/'input.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print({k:len(v) for k,v in out.items() if isinstance(v,(list,dict))})
if __name__=='__main__':main()
