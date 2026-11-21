"""Create explicit reviewable item policy from named stock acquisition families."""
import collections,gzip,json,re
from pathlib import Path
HERE=Path(__file__).resolve().parent
def main():
 a=json.loads(gzip.decompress((HERE/'acquisition.json.gz').read_bytes()));it={r['id']:r for r in a['items']};audit=json.loads((HERE/'acquisition-audit.json').read_bytes());reached=audit['reached'];policy={};held=[]
 def add(k,category,**effects):
  i=it[k];effects={f:v for f,v in effects.items() if i[{'focus':'focuseffect','worn':'worneffect'}[f]]<=0}
  if effects:policy[str(k)]={'name':i['Name'],'category':category,**effects}
 # Merchant-priced enchanted jewelry: alternatives to existing focuses, not extra focus categories.
 for k,effect in {14640:2339,14641:2339,14642:2340,14643:2340,14664:2345,14665:2345,14666:2346,14667:2347,14660:2342,14661:2342,14662:2343,14663:2344,14676:3889,14677:3889,14678:3889,14679:3889,14681:2336,14682:2337,14683:2338,14672:2366,14673:2366,14674:2367,14675:2368}.items():
  assert str(k) in reached,(k,'unreachable jewelry')
  add(k,'crafted_jewelry',**({'worn':effect} if effect==3889 else {'focus':effect}))
 # No output/recipe changes: every quality keeps its current forging path.
 patterns=[r'^(Small |Large )?Fine Plate ',r'^(Enchanted |Imbued )?Dwarven (Plate|Breastplate|Chain)',r'^(Enchanted |Imbued )?Koada`Dal Mithril ',r'^Enchanted Teir`Dal Chain ',r'^(Imbued )?Ogre War ']
 for k,i in it.items():
  if not any(re.search(p,i['Name']) for p in patterns) or i['itemclass']!=0 or i['augtype']:continue
  if str(k) not in reached:
   held.append({'id':k,'name':i['Name'],'reason':'ingredient/container chain not verified'});continue
  slots=i['slots'];effects={};caster=bool(i['classes']&16942)
  if slots==4:effects={'worn':2686}
  elif slots==524288 and caster:effects={'worn':1298}
  elif slots==4096:effects={'worn':4348}
  elif slots==64:effects={'worn':2201}
  elif slots==131072:effects={'worn':3889};effects.update({'focus':2346} if caster else {})
  elif slots==1536 and caster:effects={'focus':2343}
  elif slots==32 and caster:effects={'focus':2340}
  if effects:add(k,'crafted_armor',**effects)
 # Substantial stock class quests; existing quality grants and epic component identity preserved.
 cat=json.loads((HERE.parents[0]/'quest-armor-catalog.json').read_bytes())
 for family in cat['families']:
  for k in sorted({k for values in family['scripts'].values() for k in values}):
   i=it[k];slots=i['slots'];cl=family['class'];effects={}
   if slots==4:effects={'worn':2687}
   elif slots==4096:effects={'worn':1925}
   elif slots==64:effects={'worn':2594}
   elif slots==128:effects={'worn':3889}
   elif slots==262144:effects={'worn':3892}
   elif slots==524288 and cl not in ('Warrior','Bard'):effects={'worn':1299}
   elif slots==131072:effects={'worn':3889};effects.update({'focus':2346} if cl in ('Ranger','Shaman') else {'focus':2367} if cl=='Shadowknight' else {})
   elif slots==1536 and cl not in ('Warrior','Bard'):effects={'focus':2343}
   if effects:add(k,'class_quest',**effects)
 # Named earned drop alternatives preserve existing raw haste and occupied effects.
 for k in (2319,2465,3170):add(k,'stock_drop',worn=4348)
 for k in (3808,4865,4905,4915,5179):add(k,'stock_drop',worn=1925)
 for k in (4405,4385,5176):add(k,'stock_drop',worn=2594)
 # Ro is conditional on the separately guarded Classic zone correction and proven Ronium chain.
 for k,e in {3150:{'worn':2687},3151:{'focus':2346},3152:{'worn':3889},3153:{'focus':2343},3154:{'focus':2340,'worn':1925},3155:{'worn':3892},3156:{'worn':1299}}.items():add(k,'ro_quest',**e)
 out={'scope':'Candidate pending native validation, full-quality row guards and acquisition review. Empty fields only. Same effects across qualities. Custom augments, spells, AA ranks and existing strength unchanged.','families':dict(sorted(policy.items(),key=lambda kv:int(kv[0]))),'held':held}
 (HERE/'policy.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8')
 print('families',len(policy),'categories',dict(collections.Counter(v['category'] for v in policy.values())),'held',len(held))
if __name__=='__main__':main()
