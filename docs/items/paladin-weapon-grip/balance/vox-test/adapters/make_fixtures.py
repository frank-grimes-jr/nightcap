"""Explicit Palwar copy, twenty proposed grips and four comparison controls."""
from pathlib import Path
import json,copy,hashlib
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent/'paladin-weapon-toggle'
profile=json.loads((HERE/'palwar-private-reference.json').read_text())['tables']
char=profile['character_data'][0]
items={r['id']:r for r in profile['items']}
assess=json.loads((ROOT/'docs/items/paladin-weapon-grip/balance/assessment/assessment-results.json').read_text())
candidate={p['id']:p for p in assess['profiles'] if p['two']}
assert len(candidate)==10 and char['level']==45 and char['race']==7 and char['class']==3
assert profile['character_multiclass'][0]['class2']==1 and profile['character_multiclass'][0]['class3']==7
shield=next(r for r in profile['inventory'] if r['item_id']==409310)
primary=next(r for r in profile['inventory'] if r['slot_id']==13)
def equip(r,slot=None):
 out={'slot':r['slot_id'] if slot is None else slot,'id':r['item_id'],'custom_data':r['custom_data'] or ''}
 out['augments']=[{'socket':n,'id':r['augment_'+key]} for n,key in enumerate(['one','two','three','four','five','six']) if r['augment_'+key]]
 return out
base={'profile':'palwar-snapshot','tier':'Captured mixed quality','classes':[3,1,7],'level':45,'race':'Dwarf','race_id':7,'deity_id':208,'gender_id':0,
      'creation':{k:char[k] for k in ['str','sta','agi','dex','int','wis','cha']},'test_character_id':1,
      'saved_aa':profile['character_alternate_abilities'],'saved_aa_points':char['aa_points'],'saved_aa_spent':char['aa_points_spent'],
      'saved_skills':profile['character_skills'],'spellbook':profile['character_spells'],'memmed':profile['character_memmed_spells'],
      'aa_budget':char['aa_points'],'equipment':[equip(r) for r in profile['inventory'] if 0<=r['slot_id']<=21 and r['slot_id'] not in [13,14]]}
conditions=[]
for equal in [False,True]:
 for ident,p in sorted(candidate.items()):
  for grip in ['1h','2h']:
   b=copy.deepcopy(base);b['weapon_id']=ident;b['candidate_block']=p['block'] if grip=='1h' else 0;b['equalize_2hs']=equal
   b['profile']=f"palwar-{ident}-{grip}-"+('equalized' if equal else 'captured')
   w=equip(primary,13);w['id']=ident;w['custom_data']='nightcap_paladin_grip^1^' if grip=='1h' else ''
   o={'damage':p['one'] if grip=='1h' else p['two'],'delay':p['delay'] if grip=='1h' else p['two_delay'],'accuracy':p['accuracy']}
   if ident==10099:o.update(mana=50,astr=30,awis=30,heroic_str=8,heroic_wis=8,healamt=30,spelldmg=15,proclevel2=45)
   if ident==810099:o.update(heroic_wis=10,healamt=35,proclevel2=45)
   w['test_override']=o;b['equipment'].append(w)
   if grip=='1h':b['equipment'].append(equip(shield,14))
   conditions.append({'id':b['profile'],'weapon_name':p['name'],'grip':grip,'kind':'proposed','build':b})
 for ident in [605403,605158,605057,5504]:
  b=copy.deepcopy(base);b.update(weapon_id=ident,candidate_block=0,equalize_2hs=equal)
  current=ident==5504;b['profile']=f"palwar-control-{ident}-"+('equalized' if equal else 'captured')
  w=equip(primary,13);w['id']=ident
  if not current:w['custom_data']=''
  b['equipment'].append(w)
  if not current:b['equipment'].append(equip(shield,14))
  conditions.append({'id':b['profile'],'weapon_name':items[ident]['Name'],'grip':'1h','kind':'current-equipped-no-shield' if current else 'comparator','build':b})
def fixture(c,combat=True,pulse=32):
 out={'builds':[c['build']],'export_equipment':True,'wpm_state':True,'condition_id':c['id']}
 if combat:out['encounter']={'npc_id':73057,'npc_position':[-262,857,22,407],'duration_ms':900000,'pulse_ms':pulse,'return_to_melee':True,'combat_policy':'melee_heal','healing_spell':15,'use_mend':True,'melee_specials':True}
 return out
fixtures=HERE/'fixtures';fixtures.mkdir(exist_ok=True)
for c in conditions:
 for mode in ['stats','combat']:(fixtures/(c['id']+'-'+mode+'.json')).write_text(json.dumps(fixture(c,mode=='combat'),indent=2)+'\n')
matrix={'scope':'Full-resource Palwar level45 copy; captured buffs/native remaining durations, actual owned-AA native active view; learned Greater Healing, Monk attacks/Mend/pursuit; no optimized activated-AA rotation or surrounding raid adds',
        'conditions':conditions,'seeds':[101,2718,1729,8675309,314159],'pulse_ms':32,'duration_ms':900000,'expected_runs':len(conditions)*5,
        'skill_control':'Equalized group changes only initial2HS from32to230; all native skill learning remains enabled and exported',
        'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [HERE/'palwar-private-reference.json',HERE/'public-combat-reference.json.gz']}}
(HERE/'matrix-private.json').write_text(json.dumps(matrix,indent=2)+'\n')
print(json.dumps({'conditions':len(conditions),'seeds':5,'planned_fights':matrix['expected_runs'],'shield':409310,'healing_spell':15,'live_player_changed':False}))
