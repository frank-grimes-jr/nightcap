"""Read-only production public-content capture and dungeon contract diagnosis."""
import argparse
import base64
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ZONES = ('befallen', 'unrest', 'highkeep', 'najena', 'cazicthule', 'permafrost',
         'soldungb', 'blackburrow', 'crushbone', 'runnyeye', 'soldunga', 'guktop',
         'gukbottom', 'mistmoore', 'kedge', 'paw', 'hole', 'qcat',
         'fearplane', 'hateplane', 'airplane')

REMOTE = r'''
import base64, datetime, hashlib, json, subprocess
from pathlib import Path
root=Path('/opt/nightcap/deploy/production')
def query(statement):
    r=subprocess.run(['docker','compose','exec','-T','db','mariadb',
        '--defaults-extra-file=/run/secrets/db_backup_config','--batch','--raw',
        '--skip-column-names','--default-character-set=utf8mb4','peq'],cwd=root,
        input='START TRANSACTION READ ONLY;\n'+statement+';\nROLLBACK;\n',
        text=True,capture_output=True,check=True,timeout=120)
    return r.stdout.splitlines()
def rows(table,where):
    assert table in ('zone','spawn2','spawngroup','spawnentry','npc_types','doors','items','tasks','task_activities')
    cols=[r.split('\t')[0] for r in query('SHOW COLUMNS FROM `'+table+'`')]
    expr=','.join("'"+c+"',`"+c+'`' for c in cols)
    return [json.loads(r) for r in query('SELECT JSON_OBJECT('+expr+') FROM `'+table+'` WHERE '+where)]
quoted=','.join("'"+z+"'" for z in zones)
data={'captured_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
      'environment':'production','scope':'read-only public content and feature metadata; no player records'}
data['zone']=rows('zone','short_name IN ('+quoted+') AND version=0')
data['spawn2']=rows('spawn2','zone IN ('+quoted+') AND version IN (0,-1)')
groups=','.join(str(r['spawngroupID']) for r in data['spawn2'])
data['spawnentry']=rows('spawnentry','spawngroupID IN ('+groups+')')
data['spawngroup']=rows('spawngroup','id IN ('+groups+')')
npcs=','.join(str(r['npcID']) for r in data['spawnentry'])
data['npc_types']=rows('npc_types','id IN ('+npcs+') OR id BETWEEN 71000 AND 71199 OR id BETWEEN 998800 AND 998829')
data['reserved_groups']=rows('spawngroup','id BETWEEN 986000 AND 986019 OR id BETWEEN 998800 AND 998829')
data['doors']=rows('doors','zone IN ('+quoted+') AND version IN (0,-1)')
data['items']=rows('items','id BETWEEN 960000 AND 960449')
data['tasks']=rows('tasks','id BETWEEN 9700 AND 9749')
data['task_activities']=rows('task_activities','taskid BETWEEN 9700 AND 9749')
data['feature_state']=query('SELECT revision,enabled FROM nightcap_dungeon_state WHERE id=1')
data['quest_sources']={}
questroot=root/'data/server/quests'
for zone in zones:
    directory=questroot/zone
    if directory.is_dir():
        for path in directory.iterdir():
            if path.suffix in ('.lua','.pl') and path.is_file():
                raw=path.read_bytes()
                data['quest_sources'][zone+'/'+path.name]={'sha256':hashlib.sha256(raw).hexdigest(),'base64':base64.b64encode(raw).decode()}
data['checks']={}
for family,checks in contract.items():
    values=query(';\n'.join(c['sql'] for c in checks))
    assert len(values)==len(checks),(family,len(values),len(checks))
    data['checks'][family]={'total':len(checks),'failed':[
        {'label':c['label'],'expected':c['expected'],'actual':v}
        for c,v in zip(checks,values) if v!=c['expected']]}
print(json.dumps(data,separators=(',',':')))
'''

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    contract=json.loads((ROOT/'docs/dungeons/runtime-contract.json').read_text())
    header='zones='+repr(ZONES)+'\ncontract='+repr(contract)+'\n'
    result=subprocess.run(['ssh','-i',str(Path.home()/'.ssh/nightcap_ovh'),
        '-o','BatchMode=yes','-o','ConnectTimeout=10','-o','StrictHostKeyChecking=yes',
        'ubuntu@135.148.47.202','sudo -n python3 -'],input=header+REMOTE,
        text=True,encoding='utf-8',capture_output=True)
    if result.returncode:
        raise RuntimeError(result.stderr[-3000:])
    data=json.loads(result.stdout)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'output':str(args.output),'rows':{k:len(v) for k,v in data.items() if isinstance(v,list)},'checks':data['checks']}))

if __name__=='__main__':main()
