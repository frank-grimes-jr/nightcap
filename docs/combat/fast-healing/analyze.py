from pathlib import Path
import json,hashlib,shutil
A=Path(__file__).resolve().parent
W=Path('E:/EQ_Local_Dev/_worktrees/fast-healing');D=W/'docs/combat/fast-healing'
b=json.loads((A/'before.json').read_bytes());a=json.loads((A/'after.json').read_bytes())
checks=0;rows=[]
for name,c in a['cohorts'].items():
 old=b['cohorts'][name];assert c['stats']==old['stats'];assert c['paladin_procs']==old['paladin_procs']
 for sid,v in c['spells'].items():
  prev=old['spells'][sid];assert v['direct']>=prev['direct']
  if sid in ('12','15'):assert v==prev,(name,sid,'unchanged heal differs')
  assert v['sympathetic_full']==min(48,v['direct']//20)
  assert v['sympathetic_overheal']==min(2,v['sympathetic_full']) and v['worn_precedence']==0
  assert v['cast_ms']==prev['cast_ms']
  for p,q in zip(prev['pressure'],v['pressure']):
   assert p['landed']==q['landed'] and p['mana']==q['mana'],(name,sid,p,q)
   expect=v['direct']+(v['sympathetic_full'] if q['sympathetic'] else 0)
   assert q['healing']==q['landed']*expect,(name,sid,q,expect)
   assert q['healing']>=p['healing']
   checks+=1
  cycle=(v['cast_ms']+1500)/1000
  rows.append({'gear':name,'spell':sid,'before':prev['direct'],'after':v['direct'],'sympathetic':v['sympathetic_full'],'uninterrupted_hps_including_recovery':round((v['direct']+v['sympathetic_full'])/cycle,2)})
report={'result':'PASS','matched_pressure_cells':checks,'cast_attempts_per_binary':checks*200,'proc_cases':18,'rows':rows,'limitations':['No earned AA allocation in gear fixtures','Controlled native cast-completion hit counts, not full NPC encounter/pathing/fizzle simulation','750HA is a synthetic cap stress','Player in-game acceptance remains open']}
(A/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
for n in ['before.json','after.json','build.json','input.json','probe.cpp','native.py','validation.json','analyze.py']:
 shutil.copyfile(A/n,D/n)
print(json.dumps(report,indent=2))
