import importlib.util,json
from pathlib import Path
stage=Path('/opt/nightcap/releases/multiclass-skills-20261013')
spec=importlib.util.spec_from_file_location('release',stage/'rollout.py');q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
m=q.manifest();p=q.load('preflight.json');a=q.load('activated.json')
result=q.r.running(p['new_image_id'],m['binaries'])
assert result['started_at']==a['runtime']['started_at']
for name in ['db','web','tunnel']:assert q.r.compact(name)==p['services'][name]
assert q.r.compact('gateway')['running'] and q.policies()==p['policies'] and q.r.content_data()==p['content']
q.r.closed_ports()
print(json.dumps({'status':'healthy_after_client_publication','runtime':result,'gateway_open':True,'supporting_services_preserved':True,'policies_content_preserved':True,'database_restored':False,'player_tables_preserved':a['player_tables_preserved'],'custom_tables_preserved':a['custom_tables_preserved']}))
