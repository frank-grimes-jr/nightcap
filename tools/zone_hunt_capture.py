"""Read-only production content audit. No player rows or credentials are captured."""
import argparse, json, subprocess
from pathlib import Path
HERE = Path(__file__).parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
queries = {
 'spawns': "SELECT s.*,e.npcID,e.chance,n.name,n.level,n.race,n.class,n.bodytype,n.merchant_id,n.npc_faction_id,n.special_abilities FROM spawn2 s JOIN spawnentry e ON e.spawngroupID=s.spawngroupID JOIN npc_types n ON n.id=e.npcID JOIN zone z ON z.short_name=s.zone AND z.version=s.version WHERE z.expansion=0 AND s.version=0 ORDER BY s.zone,s.id,e.npcID",
 'reserved_ids': 'SELECT id,Name FROM items WHERE id BETWEEN 940000 AND 949999',
 'socket_candidates': 'SELECT id,Name,slots,classes,races,reqlevel,reclevel,augtype,augslot1type,augslot2type,augslot3type,augslot4type,augslot5type,augslot6type,augslot1visible,augslot2visible,augslot3visible,augslot4visible,augslot5visible,augslot6visible FROM items WHERE itemclass=0 AND augtype=0 AND (slots & 921732)<>0 AND id<800000',
 'classic_loot': 'SELECT DISTINCT lde.item_id FROM spawn2 s JOIN zone z ON z.short_name=s.zone AND z.version=s.version JOIN spawnentry se ON se.spawngroupID=s.spawngroupID JOIN npc_types n ON n.id=se.npcID JOIN loottable_entries lte ON lte.loottable_id=n.loottable_id JOIN lootdrop_entries lde ON lde.lootdrop_id=lte.lootdrop_id WHERE z.expansion=0 AND s.version=0',
 'item_schema': 'SHOW COLUMNS FROM items',
 'table_schema': 'SHOW COLUMNS FROM spawnentry',
 'feature_tables': "SHOW TABLES LIKE 'nightcap_zone_hunt%'",
}
remote = '''import json, subprocess, pathlib, hashlib
queries=QUERIES
out={}
for key,sql in queries.items():
 p=subprocess.run(['docker','compose','exec','-T','db','mariadb','--defaults-extra-file=/run/secrets/db_backup_config','--batch','peq'],cwd='/opt/nightcap/deploy/production',input='START TRANSACTION READ ONLY; '+sql+'; COMMIT;',text=True,capture_output=True)
 if p.returncode: raise RuntimeError(key+': '+p.stderr)
 lines=p.stdout.splitlines(); columns=lines[0].split('\\t') if lines else []
 out[key]=[dict(zip(columns,line.split('\\t'))) for line in lines[1:]]
quest_root=pathlib.Path('/opt/nightcap/deploy/production/data/server/quests')
out['quest_files']=[str(p.relative_to(quest_root)) for p in quest_root.glob('**/*') if p.suffix in ('.pl','.lua')]
out['quest_hashes']={str(p.relative_to(quest_root)):hashlib.sha256(p.read_text(errors='replace').encode()).hexdigest() for z in ('fearplane','kithicor','soldunga','soldungb','highkeep','crushbone') for p in (quest_root/z).glob('*') if p.suffix in ('.pl','.lua')}
print(json.dumps(out))
'''.replace('QUERIES',repr(queries))
command=[r'C:\Windows\System32\OpenSSH\ssh.exe','-i',r'C:\Users\verre\.ssh\nightcap_ovh','-o','BatchMode=yes','-o','ConnectTimeout=10','-o','StrictHostKeyChecking=yes','ubuntu@135.148.47.202','sudo -n python3 -']
p=subprocess.run(command,input=remote,text=True,capture_output=True,timeout=120)
if p.returncode: raise RuntimeError(p.stderr)
data=json.loads(p.stdout)
args.output.parent.mkdir(parents=True,exist_ok=True)
args.output.write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps({k:len(v) for k,v in data.items()}))
