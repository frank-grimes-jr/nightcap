import copy,json,unittest
from pathlib import Path
import ecommons_hub as hub
from test_pok_compact_hub import fixture as compact

def fixture():
 b=compact();r=b['rows'];b['reference_guards']={name:'0' for name in hub.reference_guards()};b['scopes']=hub.scopes()
 for t in hub.KEYS:r.setdefault(t,[]);b['schemas'][t]={'create':'ENGINE=InnoDB'}
 for _,a,c in hub.ROUTES:
  for n in (a,c):r['doors'].append({'id':str(n)})
 r['start_zones']=[{'player_choice':str(i),'player_race':'1','player_class':'1','player_deity':'1','zone_id':'202','bind_id':'202','start_zone':'202'} for i in range(411)]
 for name,value in [('Expansion:CurrentExpansion','0'),('Character:MaxLevel','50'),('World:EnableTutorialButton','false'),('World:StartZoneSameAsBindOnCreation','true')]:r['rule_values'].append(dict(ruleset_id='1',rule_name=name,rule_value=value))
 for rs in ('1','10'):r['rule_values'].append(dict(ruleset_id=rs,rule_name='World:SoFStartZoneID',rule_value='202'))
 r['zone']=[{'id':'22','short_name':'ecommons'},{'id':'25','short_name':'nektulos','map_file_name':'nektulos_v0'}]
 r['spells_new']=[dict(id='3134',effectid1='83',buffduration='0',targettype='6',**{f'effectid{i}':'254' for i in range(2,13)}),dict(id='99001',cast_time='5000',recovery_time='1500',recast_time='600000',mana='0')]
 r['aa_ability']=[dict(id='2220',type='0',category='-1')]
 r['aa_ranks']=[dict(id='22200',spell='99001',recast_time='600',title_sid='-1',desc_sid='-1',upper_hotkey_sid='-1',lower_hotkey_sid='-1')]
 return b
class TunnelHub(unittest.TestCase):
 def setUp(self):self.plan=json.loads((hub.ROOT/'docs/ecommons-hub/plan.json').read_bytes())
 def test_network_and_recall(self):
  b=fixture();a=hub.desired(b,self.plan)['rows'];self.assertEqual(len(a['doors']),42);self.assertEqual(a['aa_ability'][0]['type'],'1');self.assertEqual(a['aa_ranks'][0]['upper_hotkey_sid'],'22200')
  s=next(s for s in a['spells_new'] if s['id']=='42604');self.assertEqual(s['effect_base_value3'],'4');self.assertEqual(s['effectid1'],'83')
  for t in ('npc_types','merchantlist','spawnentry','spawngroup'):self.assertEqual(a[t],b['rows'][t])
  for r in a['doors'][20:]:self.assertEqual(r['dest_instance'],'0');self.assertEqual(r['min_expansion'],'0');self.assertEqual(r['opentype'],'58')
 def test_rejects_topology_and_reservation_and_reference_drift(self):
  for kind in ('duplicate_group','door','reference','tutorial'):
   b=fixture()
   if kind=='duplicate_group':b['rows']['spawn2'][0]['spawngroupID']=b['rows']['spawn2'][1]['spawngroupID']
   if kind=='door':b['rows']['doors'].append(dict(id='40600'))
   if kind=='reference':b['reference_guards']['items']='1'
   if kind=='tutorial':next(r for r in b['rows']['rule_values'] if r['rule_name']=='World:EnableTutorialButton')['rule_value']='true'
   with self.subTest(kind=kind),self.assertRaises(ValueError):hub.desired(b,self.plan)
if __name__=='__main__':unittest.main()
