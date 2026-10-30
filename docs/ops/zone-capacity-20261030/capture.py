"""Read-only capacity, resource and zone-timer capture. Never applies changes."""
import datetime
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
from content_patch import capture

SSH = ['C:/Windows/System32/OpenSSH/ssh.exe', '-i', 'C:/Users/verre/.ssh/nightcap_ovh',
       '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', '-o', 'StrictHostKeyChecking=yes',
       'ubuntu@135.148.47.202']


def remote(code):
    result = subprocess.run(SSH + ['sudo -n python3 -B -'], input=code,
                            capture_output=True, text=True, timeout=60)
    result.check_returncode()
    return json.loads(result.stdout)


def query(sql):
    return remote('import subprocess,json\n'
        'r=subprocess.run(["docker","exec","-i","nightcap-production-db-1",'
        '"mariadb","--defaults-extra-file=/run/secrets/db_backup_config",'
        '"--batch","--raw","--skip-column-names","peq"],'
        f'input={sql!r},text=True,capture_output=True,check=True)\n'
        'print(json.dumps(r.stdout))\n')


def main():
    out = Path(sys.argv[1])
    if out.exists():
        raise ValueError('Preserve existing capture; choose a new filename')
    data = capture(query, {'zone': '1=1'})
    data['rules'] = query("SELECT ruleset_id,rule_name,rule_value FROM rule_values WHERE rule_name IN "
                        "('Zone:StateSavingOnShutdown','Zone:KillProcessOnDynamicShutdown','Zone:AutoShutdownDelay');")
    data['resources'] = remote('''import json,subprocess,shutil
from pathlib import Path
def run(args):return subprocess.check_output(args,text=True)
names=['nightcap-production-'+x+'-1' for x in ('game','db','gateway','web','tunnel')]
rows=json.loads(run(['docker','inspect',*names]))
services={r['Name']:{'id':r['Id'],'image':r['Image'],'start':r['State']['StartedAt'],
 'restarts':r['RestartCount'],'oom':r['State']['OOMKilled'],'running':r['State']['Running'],
 'memory_limit':r['HostConfig']['Memory']} for r in rows}
game=rows[0]
worker_env=[s for s in game['Config']['Env'] if s.startswith('NIGHTCAP_ZONE_WORKERS=')]
code="""import json,hashlib
from pathlib import Path
cg=Path('/sys/fs/cgroup')
print(json.dumps({'memory_current':int((cg/'memory.current').read_text()),
 'memory_peak':int((cg/'memory.peak').read_text()),'memory_limit':int((cg/'memory.max').read_text()),
 'memory_events':(cg/'memory.events').read_text(),
 'supervisor_sha256':hashlib.sha256(Path('/opt/nightcap/start.py').read_bytes()).hexdigest()}))
"""
native=json.loads(subprocess.check_output(['docker','exec','-i',names[0],'python3','-B','-'],input=code,text=True))
mem={s.split(':')[0]:int(s.split()[1])*1024 for s in Path('/proc/meminfo').read_text().splitlines() if s.startswith(('MemAvailable:','MemTotal:'))}
print(json.dumps({'services':services,'worker_env':worker_env,'native':native,'host_memory':mem,
 'disk_free':shutil.disk_usage('/opt/nightcap').free,
 'zone_rss':run(['docker','exec',names[0],'ps','-C','zone','-o','pid=,rss=']),
 'compose_sha256':__import__('hashlib').sha256(Path('/opt/nightcap/deploy/production/compose.yaml').read_bytes()).hexdigest()}))
''')
    data['captured_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    data['production_changed'] = False
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'zones':len(data['rows']['zone']), 'resources':data['resources']}))


if __name__ == '__main__':
    main()
