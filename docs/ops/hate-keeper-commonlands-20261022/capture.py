"""Capture public content preimages and hub placement evidence, read-only."""
import json,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
REMOTE=r'''
import csv,hashlib,io,json,subprocess
from pathlib import Path
root=Path('/opt/nightcap/deploy/production')
def query(q,headers=False):
 args=['docker','compose','exec','-T','db','mariadb','--defaults-extra-file=/run/secrets/db_backup_config','--batch','--raw','peq']
 if not headers:args.insert(-1,'--skip-column-names')
 p=subprocess.run(args,cwd=root,input='START TRANSACTION READ ONLY;\n'+q+';\nROLLBACK;',capture_output=True,text=True,check=True)
 return p.stdout
scopes={'npc_types':'id=998812','spawnentry':'npcID=998812 OR spawngroupID=998812','spawngroup':'id=998812','spawn2':'id=9100012 OR spawngroupID=998812','zone':"short_name='hateplane' AND version=0",'nightcap_dungeon_spawns':'zone_id=76 OR spawn_id=9100012','zone_state_spawns':'zone_id=76 AND instance_id=0 AND is_corpse=0 AND is_zone=0 AND spawn2_id=9100012 AND spawngroup_id=998812 AND npc_id IN (0,998812)'}
r={'schemas':{},'scopes':scopes,'rows':{}}
for table,scope in scopes.items():
 columns=[l.split('\t')[0] for l in query('SHOW COLUMNS FROM '+table).splitlines()]
 r['schemas'][table]={'create':query('SHOW CREATE TABLE '+table).split('\t',1)[1].rstrip()}
 fields=','.join("'"+c+"',CAST(`"+c+'` AS CHAR)' for c in columns)
 r['rows'][table]=[json.loads(l) for l in query('SELECT JSON_OBJECT('+fields+') FROM `'+table+'` WHERE '+scope).splitlines()]
print(json.dumps({'preimages':r,'legacy_hate_instances':query("SELECT COUNT(*) FROM instance_list WHERE zone=76 AND COALESCE(notes,'') NOT LIKE 'nc-dungeon:%'"),'hub':list(csv.DictReader(io.StringIO(query("SELECT n.id,n.name,n.lastname,s.id spawn_id,s.x,s.y,s.z,s.heading,s.pathgrid FROM npc_types n JOIN spawnentry e ON e.npcID=n.id JOIN spawn2 s ON s.spawngroupID=e.spawngroupID WHERE s.zone='ecommons' AND s.version=0 AND s.x BETWEEN -450 AND -100 AND s.y BETWEEN -1650 AND -1400 ORDER BY s.y,s.x",True)),delimiter='\t'))}))
'''
cmd=['ssh','-i',str(Path.home()/'.ssh/nightcap_ovh'),'-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','ubuntu@135.148.47.202','sudo -n python3 -']
p=subprocess.run(cmd,input=REMOTE,text=True,capture_output=True,check=True)
r=json.loads(p.stdout)
(HERE/'preimages.json').write_text(json.dumps(r['preimages'],indent=2)+'\n')
(HERE/'hub.json').write_text(json.dumps(r['hub'],indent=2)+'\n')
(HERE/'legacy-check.json').write_text(json.dumps({'legacy_hate_instances':int(r['legacy_hate_instances'])})+'\n')
print(json.dumps({'saved_keeper_rows':len(r['preimages']['rows']['zone_state_spawns']),'legacy_hate_instances':int(r['legacy_hate_instances']),'hub_rows':len(r['hub'])},indent=2))
