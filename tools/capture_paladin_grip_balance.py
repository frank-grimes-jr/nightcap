"""Read-only production capture of public Paladin weapon/quest definitions."""
import argparse,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REMOTE=r'''
import datetime,hashlib,json,re,subprocess
from pathlib import Path
root=Path('/opt/nightcap/deploy/production');quests=root/'data/server/quests'
def sql(q):
 r=subprocess.run(['docker','compose','exec','-T','db','mariadb','--defaults-extra-file=/run/secrets/db_backup_config','--batch','--raw','--skip-column-names','peq'],cwd=root,input='SET TRANSACTION READ ONLY; START TRANSACTION WITH CONSISTENT SNAPSHOT; '+q+' ROLLBACK;',capture_output=True,text=True,timeout=45)
 if r.returncode:raise RuntimeError(r.stderr[-1000:])
 return [json.loads(x) for x in r.stdout.splitlines()]
ids=[5504,205504,405504,605504,11050,211050,411050,611050,10099,810099]
fields=['id','Name','itemtype','damage','delay','classes','slots','reqlevel','reclevel','ac','hp','mana','proceffect','procrate','banedmgamt','banedmgbody','banedmgrace','banedmgraceamt','elemdmgtype','elemdmgamt','augslot1type','augslot2type','augslot3type','augslot4type','augslot5type','augslot6type']
expr='JSON_OBJECT('+','.join("'%s',`%s`"%(f,f) for f in fields)+')'
fields += ['accuracy','astr','awis','heroic_str','heroic_wis','healamt','spelldmg','proclevel2']
expr='JSON_OBJECT('+','.join("'%s',`%s`"%(f,f) for f in fields)+')'
comparables=['Ghoulbane','Sword of the Morning','Sword of Skyfire','Wurmslayer','Runed Falchion','Deepwater Harpoon']
items=sql('SELECT '+expr+' FROM items WHERE id IN ('+','.join(map(str,ids))+') OR '+ ' OR '.join("Name LIKE '"+n+"%'" for n in comparables)+' ORDER BY id;')
npcs=sql("SELECT JSON_OBJECT('id',id,'name',name) FROM npc_types WHERE name IN ('Brother_Hayle','#Brother_Hayle','Inte_Akera','Irak_Altil','#Irak_Altil','Epic_Forgemaster') ORDER BY id;")
pattern=re.compile(r'(?<!\d)(5504|605504|11050|611050|10099|810099)(?!\d)')
scripts={};matches=[]
for p in quests.rglob('*'):
 if p.suffix not in ('.lua','.pl') or not p.is_file():continue
 data=p.read_bytes();text=data.decode('utf-8',errors='replace')
 found=[{'line':i,'text':l.strip()} for i,l in enumerate(text.splitlines(),1) if pattern.search(l) and not l.lstrip().startswith(('#','--'))]
 if found:
  rel=p.relative_to(quests).as_posix();matches.append({'path':rel,'matches':found});scripts[rel]={'sha256':hashlib.sha256(data).hexdigest(),'source':text}
precedence={}
dispatch={}
for zone,stem in [('paw','Brother_Hayle'),('southkarana','#Brother_Hayle'),('airplane','Inte_Akera'),('fearplane','Irak_Altil'),('hohonora','#Irak_Altil'),('ecommons','Epic_Forgemaster'),('poknowledge','Epic_Forgemaster')]:
 found=[]
 for n in [n for n in npcs if n['name']==stem]:
  for folder in [quests/zone]+sorted((quests/zone).glob('v*'))+[quests/'global']:
   for name in [str(n['id']),stem,stem+'_'+str(n['id'])]:
    for ext in ['.lua','.pl']:
     p=folder/(name+ext)
     if p.is_file():
      rel=p.relative_to(quests).as_posix();found.append(rel);data=p.read_bytes();scripts[rel]={'sha256':hashlib.sha256(data).hexdigest(),'source':data.decode('utf-8')}
 precedence[zone+'/'+stem]=sorted(set(found))
 # Match GetQIByNPCQuest's filename order. Refuse ambiguous Lua/Perl peers
 # rather than assume interpreter registration order. Defaults are lower priority.
 resolutions=[]
 for npc in [n for n in npcs if n['name']==stem]:
  versioned=[quests/zone/'v0']+sorted(p for p in (quests/zone).glob('v*') if p.is_dir() and p.name!='v0')
  for version in versioned:
   folders=[version,quests/zone,quests/'global']
   names=[str(npc['id']),stem.replace('`','-'),stem.replace('`','-')+'_'+str(npc['id'])]
   bases=[folder/name for folder in folders for name in names]+[folder/'default' for folder in folders]
   selected=[]
   for base in bases:
    peers=[Path(str(base)+ext) for ext in ('.lua','.pl') if Path(str(base)+ext).is_file()]
    if peers:
     selected=[p.relative_to(quests).as_posix() for p in peers];break
   resolutions.append({'npc_id':npc['id'],'version':version.name,'selected':selected})
 dispatch[zone+'/'+stem]=resolutions
p=quests/'lua_modules/items.lua';data=p.read_bytes();helpers={'lua_modules/items.lua':{'sha256':hashlib.sha256(data).hexdigest(),'source':data.decode('utf-8')}}
recipes=sql('SELECT JSON_OBJECT(\'id\',id,\'recipe_id\',recipe_id,\'item_id\',item_id,\'componentcount\',componentcount,\'successcount\',successcount) FROM tradeskill_recipe_entries WHERE item_id IN ('+','.join(map(str,ids))+') ORDER BY id;')
print(json.dumps(dict(observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),environment='production',read_only=True,items=items,npcs=npcs,scripts=scripts,precedence=precedence,dispatch=dispatch,literal_dependencies=matches,helpers=helpers,recipe_references=recipes)))
'''
def main(out):
 if out.exists():raise FileExistsError("Retain existing capture; choose a new output path")
 r=subprocess.run(['ssh','-i','C:/Users/verre/.ssh/nightcap_ovh','-o','BatchMode=yes','-o','ConnectTimeout=10','-o','StrictHostKeyChecking=yes','ubuntu@135.148.47.202','sudo -n python3 -'],input=REMOTE,text=True,capture_output=True,timeout=180)
 if r.returncode:raise RuntimeError(r.stderr[-1500:])
 d=json.loads(r.stdout);out.parent.mkdir(parents=True,exist_ok=True);
 with out.open('x',encoding='utf-8') as stream:stream.write(json.dumps(d,indent=2)+'\n')
 print(json.dumps({'items':len(d['items']),'scripts':len(d['scripts']),'precedence':d['precedence'],'recipes':d['recipe_references']}))
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
 main(parser.parse_args().output)
