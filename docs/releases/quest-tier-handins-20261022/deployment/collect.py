"""Retain compact deployment proof without exporting player rows or credentials."""
import json
from deploy import run, HERE, STAGE

report=json.loads(run(f'''
from pathlib import Path
import json,shutil,datetime,importlib.util
stage=Path({STAGE!r});spec=importlib.util.spec_from_file_location('op',stage/'rollout.py');op=importlib.util.module_from_spec(spec);spec.loader.exec_module(op);op.initialize()
folder=stage/'evidence/activation';deployed=op.load(folder/'deployed.json');pre=op.load(stage/'evidence/preflight.json');m=op.manifest()
assert deployed['gateway_open'] and op.r.compact('game')==deployed['game']
gateway=op.r.compact('gateway');assert gateway['running'] and not gateway['oom_killed']
# Gateway has no configured Docker healthcheck; null is not a failed health result.
assert gateway['health'] in (None,'healthy')
quests={{n:op.sha(op.ROOT/'data/server'/n) for n in m['quest_preimages']}}
assert quests=={{n:m['files'][n] for n in m['quest_preimages']}}
print(json.dumps({{'verified_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'gateway_open':True,'deployed':deployed,
'backup':op.load(folder/'backup.json'),'quest_files':quests,'services':{{s:op.r.compact(s) for s in ['game','gateway','db','web','tunnel']}},
'preserved':{{'runtime_files':len(pre['runtime'])-7,'content_tables':len(pre['content']),'caches':pre['cache_sha256'],'public':pre['public'],'wiki_release_before':pre['wiki_release']}},
'base_image_id':pre['old_image_id'],'image_id':pre['new_image_id'],'free_bytes':shutil.disk_usage(op.ROOT).free,
'owner_gameplay_accepted':False,'database_restored':False}}))
'''))
(HERE/'live-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:report[k] for k in ['verified_at','gateway_open','image_id','free_bytes','owner_gameplay_accepted']}))
