"""SELECT-only production evidence for the explicit class-armor reward catalog."""
import argparse
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REMOTE = r'''
import datetime, hashlib, json, re, subprocess
from pathlib import Path
catalog = CATALOG_LITERAL
root = Path('/opt/nightcap/deploy/production')
quests = root / 'data/server/quests'
cmd = ['docker','compose','exec','-T','db','mariadb',
       '--defaults-extra-file=/run/secrets/db_backup_config','--batch','--raw',
       '--skip-column-names','--default-character-set=utf8mb4','peq']
def sql(query):
    r = subprocess.run(cmd, cwd=root, text=True, capture_output=True, timeout=60,
        input='SET TRANSACTION READ ONLY; START TRANSACTION WITH CONSISTENT SNAPSHOT; '+query+' ROLLBACK;')
    if r.returncode: raise RuntimeError(r.stderr[-1500:])
    return [json.loads(line) for line in r.stdout.splitlines()]
paths = {p for f in catalog['families'] for p in f['scripts']}
paths.update(catalog['unchanged_crafted_resizing'])
paths.add('overthere/Kurron_Ni.pl')
ids = {i for f in catalog['families'] for values in f['scripts'].values() for i in values}
base_ids = sorted(ids)
ids.update(range(4173,4189))
ids = sorted({i+offset for i in ids for offset in (0,200000,400000,600000)})
names = sorted({Path(p).stem for p in paths})
npcs = sql("SELECT JSON_OBJECT('id',id,'name',name) FROM npc_types WHERE name IN ("+
    ','.join("'"+n+"'" for n in names)+") ORDER BY id;")
scripts = {}
precedence = {}
for relative in sorted(paths):
    p = quests / relative
    data = p.read_bytes()
    scripts[relative] = {'sha256':hashlib.sha256(data).hexdigest(), 'source':data.decode('utf-8')}
    zone = Path(relative).parent.as_posix()
    stem = Path(relative).stem
    found = set()
    for npc in [n for n in npcs if n['name']==stem]:
        for directory in (zone+'/v0',zone,'global'):
            for name in (str(npc['id']),stem,stem+'_'+str(npc['id'])):
                for ext in ('.pl','.lua'):
                    alternative = quests/directory/(name+ext)
                    if alternative.is_file(): found.add(str(alternative.relative_to(quests)))
    precedence[relative] = sorted(found)
fields = ['id','Name','itemclass','itemtype','slots','classes','races','reqlevel','reclevel',
          'ac','hp','mana','endur','astr','asta','aagi','adex','awis','aint','acha',
          'heroic_str','heroic_sta','heroic_agi','heroic_dex','heroic_wis','heroic_int','heroic_cha',
          'spelldmg','healamt','augtype','augslot1type','augslot2type','augslot3type',
          'augslot4type','augslot5type','augslot6type','color','loregroup','attuneable']
items = sql('SELECT JSON_OBJECT('+','.join("'%s',`%s`"%(f,f) for f in fields)+
    ') FROM items WHERE id IN ('+','.join(map(str,ids))+') ORDER BY id;')
helpers = {}
for relative in ('lua_modules/items.lua','plugins/check_handin.pl','plugins/quest_handin.pl','plugins/globals.pl'):
    p=quests/relative
    if p.is_file(): helpers[relative]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'source':p.read_text()}
pattern = re.compile(r'(?<!\d)('+ '|'.join(map(str,base_ids))+r')(?!\d)')
dependencies = []
for p in quests.rglob('*'):
    if p.suffix not in ('.pl','.lua') or not p.is_file(): continue
    data=p.read_bytes()
    lines=[{'line':n,'text':line.strip()} for n,line in enumerate(data.decode('utf-8',errors='replace').splitlines(),1)
           if pattern.search(line) and not line.lstrip().startswith(('#','--'))]
    if lines: dependencies.append({'path':str(p.relative_to(quests)),
        'sha256':hashlib.sha256(data).hexdigest(),'matches':lines})
consumers = sql("SELECT JSON_OBJECT('id',id,'recipe_id',recipe_id,'item_id',item_id,'componentcount',componentcount) FROM tradeskill_recipe_entries WHERE componentcount>0 AND item_id IN ("+','.join(map(str,base_ids))+') ORDER BY id;')
activities = sql("SELECT JSON_OBJECT('taskid',taskid,'activityid',activityid,'item_id_list',item_id_list,'item_list',item_list) FROM task_activities ORDER BY taskid,activityid;")
activities = [row for row in activities if pattern.search(str(row['item_id_list'])) or pattern.search(str(row['item_list']))]
print(json.dumps({'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'environment':'production','read_only':True,'scripts':scripts,'precedence':precedence,
    'npcs':npcs,'items':items,'helpers':helpers,'literal_dependencies':dependencies,
    'recipe_consumers':consumers,'task_consumers':activities}))
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    catalog = json.loads((ROOT/'docs/items/quest-armor-catalog.json').read_text())
    remote = REMOTE.replace('CATALOG_LITERAL', repr(catalog))
    result = subprocess.run(['ssh','-i','C:/Users/verre/.ssh/nightcap_ovh',
        '-o','BatchMode=yes','-o','ConnectTimeout=10','-o','StrictHostKeyChecking=yes',
        'ubuntu@135.148.47.202','sudo -n python3 -'], input=remote,
        text=True,capture_output=True,timeout=180)
    if result.returncode: raise RuntimeError(result.stderr[-1500:])
    data = json.loads(result.stdout)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'scripts':len(data['scripts']),'items':len(data['items']),
                      'observed_utc':data['observed_utc']}))


if __name__ == '__main__':
    main()
