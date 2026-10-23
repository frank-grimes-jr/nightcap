"""Read-only production release/content capture; no player records exported."""
import datetime, hashlib, importlib.util, json, shutil, subprocess
from pathlib import Path

ROOT=Path('/opt/nightcap/deploy/production')
PRIOR=Path('/opt/nightcap/releases/aa-level-progression-20261023-v3/rollout.py')
spec=importlib.util.spec_from_file_location('prior',PRIOR)
prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior);prior.initialize()
r=prior.r;sql=prior.sql

def rows(table,where='1'):
    cols=[line.split('\t')[0] for line in sql('SHOW COLUMNS FROM `'+table+'`;').splitlines()]
    return [dict(zip(cols,json.loads(line))) for line in sql('SELECT JSON_ARRAY('+','.join('`'+c+'`' for c in cols)+') FROM `'+table+'` WHERE '+where+';').splitlines()]

result={'captured_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'services':{s:r.compact(s) for s in ('game','gateway','db','web','tunnel')},
 'disk_free':shutil.disk_usage(ROOT).free,'runtime':r.runtime(),'public':r.public(),
 'channel_sha256':prior.sha(ROOT/'data/public/channel.json'),
 'prior_operator_sha256':prior.sha(PRIOR),'helper_sha256':prior.sha(prior.base.HELPER),
 'memory_available_kib':next(x.split()[1] for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:'))}
result['base_hashes']=r.image_hashes(result['services']['game']['image_id'])
result['health']=subprocess.run(['docker','exec',r.state('game')['Id'],'python3','/opt/nightcap/start.py','--health'],capture_output=True,text=True).returncode
result['startup_guards']=prior.startup_guards()
content={'captured_at':result['captured_at'],'environment':'production','scope':'public definitions only'}
content['zone']=rows('zone',"short_name IN ('chapterhouse','commons') AND version=0")
content['spawn2']=rows('spawn2',"zone='chapterhouse'")
groups=','.join(str(s['spawngroupID']) for s in content['spawn2'])
content['spawnentry']=rows('spawnentry',f'spawngroupID IN ({groups})')
ids=','.join(str(s['npcID']) for s in content['spawnentry'])
content['npc_types']=rows('npc_types',f'id IN ({ids})')
content['doors']=rows('doors',"zone='chapterhouse'")
content['templates']={t:rows(t,w)[0] for t,w in (
 ('npc_types','id=999228'),('spawngroup','id=999228'),('spawnentry','npcID=999228'),
 ('spawn2',"zone='unrest' AND spawngroupID=999228"))}
content['benchmarks']=rows('npc_types','id IN (73103,32040,63092,66095)')
content['helmet']=rows('items','id=990500')
scopes={'npc_types':'id BETWEEN 998820 AND 998859','spawngroup':'id BETWEEN 998820 AND 998859',
 'spawnentry':'npcID BETWEEN 998820 AND 998859 OR spawngroupID BETWEEN 998820 AND 998859',
 'spawn2':'id BETWEEN 9220000 AND 9220099','items':'id BETWEEN 961000 AND 961019 OR id BETWEEN 960414 AND 960419',
 'tasks':'id IN (9742,9743,9800)','task_activities':'taskid IN (9742,9743,9800)',
 'nightcap_waypoints':"zone='chapterhouse' OR zone_id=760",'nightcap_dungeon_spawns':'zone_id=760'}
content['reservations']={t:int(sql('SELECT COUNT(*) FROM `'+t+'` WHERE '+w+';')) for t,w in scopes.items()}
assert not any(content['reservations'].values()),content['reservations']
hazards={t:rows(t,w) for t,w in (('zone_points',"zone='chapterhouse'"),('ground_spawns','zoneid=760'),
 ('fishing','zoneid=760'),('forage','zoneid=760'),('traps',"zone='chapterhouse'"),('object','zoneid=760'))}
result['content']=content;result['secondary_content']=hazards
result['saved_chapterhouse_counts']=sql('SELECT instance_id,is_corpse,COUNT(*) FROM zone_state_spawns WHERE zone_id=760 GROUP BY instance_id,is_corpse;').splitlines()
result['chapterhouse_instances']=int(sql('SELECT COUNT(*) FROM instance_list WHERE zone=760;'))
result['existing_vigil_tables']=sql("SHOW TABLES LIKE 'nightcap_vigil_%';").splitlines()
result['script_shadows']={str(p.relative_to(ROOT/'data/server')):prior.sha(p) for folder in ('chapterhouse','chapterhouse_version1') for p in (ROOT/'data/server/quests'/folder).glob('*') if p.is_file()}
print(json.dumps(result,separators=(',',':')))
