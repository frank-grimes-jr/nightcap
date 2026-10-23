"""Local transport for the authorized quest-tier release; never prints credentials."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import io
import shlex
import tarfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ARTIFACTS = Path('E:/EQ_Local_Dev/artifacts/quest-handin-tests')
STAGE = '/opt/nightcap/releases/quest-tier-handins-20261022'
SSH = ['C:/Windows/System32/OpenSSH/ssh.exe', '-i', 'C:/Users/verre/.ssh/nightcap_ovh',
       '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', '-o', 'StrictHostKeyChecking=yes',
       'ubuntu@135.148.47.202']
QUESTS = ['quests/lua_modules/items.lua', 'quests/overthere/Kurron_Ni.pl'] + [
    'quests/soltemple/'+name+'.pl' for name in ['Gardern','Joyce','Sultin','Vilissia','Vurgo']]


def run(source, timeout=240):
    result = subprocess.run(SSH+['sudo -n python3 -'], input=source, text=True,
                            capture_output=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(result.stderr[-5000:])
    return result.stdout


def probe():
    control = (ROOT/'docs/ops/waypoint-crystal-20261022/deployment/world_control.py').read_text()
    result = json.loads(run(f'''
import hashlib,importlib.util,json,shutil,subprocess,datetime
from pathlib import Path
helper=Path('/opt/nightcap/releases/zone-hunt-20261009/runtime_ops.py')
spec=importlib.util.spec_from_file_location('runtime',helper)
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
game=r.state('game'); image=game['Image']; hashes=r.image_hashes(image)
runtime=r.running(image,{{n:hashes['bin/'+n] for n in ['world','zone','ucs','loginserver','shared_memory']}},game['RestartCount'])
def control(action):
 p=subprocess.run(['docker','exec','-i',game['Id'],'python3','-',action],input={control!r},text=True,capture_output=True,check=True)
 return json.loads(p.stdout)
root=r.ROOT
print(json.dumps({{'captured_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'services':{{s:r.compact(s) for s in ['game','gateway','db','web','tunnel']}},
 'base_image_id':image,'base_hashes':hashes,'runtime':runtime,
 'runtime_helper_sha256':r.sha(helper),'disk_free_bytes':shutil.disk_usage(root).free,
 'quest_preimages':{{n:r.sha(root/'data/server'/n) for n in {QUESTS!r}}},
 'public':r.public(),'wiki_release':(root/'data/public/wiki/current').readlink().name,
 'cache_sha256':{{n:r.sha(root/'data/server/shared'/n) for n in ['items','spells']}},
 'world_count':control('count'),'world_locked':control('status'),
 'expired_npc_cache':r.sql("SELECT COUNT(*) FROM zone_state_spawns WHERE is_corpse=0 AND created_at < DATE_SUB(NOW(), INTERVAL 7 DAY);").strip()
}}))
'''))
    (HERE/'probe.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['captured_at','base_image_id','disk_free_bytes','world_count','world_locked','wiki_release','expired_npc_cache']},indent=2))


def prepare():
    probe_data = json.loads((HERE/'probe.json').read_text())
    files = {'bin/zone': ARTIFACTS/'zone', 'rollout.py': HERE/'rollout.py'}
    files.update({n:ROOT/'server-mods'/n for n in QUESTS})
    pins = {n:hashlib.file_digest(p.open('rb'),'sha256').hexdigest() for n,p in files.items()}
    build = json.loads((HERE.parent/'native-build-manifest.json').read_text())
    assert pins['bin/zone'] == build['zone_sha256']
    assert probe_data['base_hashes']['bin/zone'] == build['baseline_zone_sha256']
    m = {k:probe_data[k] for k in ['base_image_id','base_hashes','quest_preimages','runtime_helper_sha256']}
    m.update(files=pins,zone_sha256=pins['bin/zone'],
             client_channel_sha256=probe_data['public']['channel.json'],
             source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip())
    raw = (json.dumps(m,indent=2)+'\n').encode()
    (HERE/'manifest.json').write_bytes(raw)
    archive = ARTIFACTS/'quest-tier-production.tar.gz'
    with tarfile.open(archive,'w:gz') as tar:
        for n,p in files.items():
            info=tarfile.TarInfo(n); info.size=p.stat().st_size; info.mode=0o755 if n=='bin/zone' else 0o644
            with p.open('rb') as f:tar.addfile(info,f)
        info=tarfile.TarInfo('manifest.json');info.size=len(raw);info.mode=0o600;tar.addfile(info,io.BytesIO(raw))
    expected={**pins,'manifest.json':hashlib.sha256(raw).hexdigest()}
    source=f'''
import hashlib,os,sys,tarfile,shutil,json
from pathlib import Path
os.umask(0o077);stage=Path({STAGE!r});expected={expected!r}
assert not stage.exists()
assert shutil.disk_usage(stage.parent).free > {files['bin/zone'].stat().st_size}+1500*1024**2
stage.mkdir(mode=0o700)
seen=set()
with tarfile.open(fileobj=sys.stdin.buffer,mode='r|gz') as tar:
 for item in tar:
  assert item.isfile() and item.name in expected and item.name not in seen
  seen.add(item.name);p=stage/item.name
  assert p.resolve().is_relative_to(stage)
  p.parent.mkdir(parents=True,exist_ok=True)
  with p.open('xb') as f:shutil.copyfileobj(tar.extractfile(item),f)
  p.chmod(0o755 if item.name=='bin/zone' else 0o600)
  assert hashlib.file_digest(p.open('rb'),'sha256').hexdigest()==expected[item.name]
assert seen==set(expected)
print(json.dumps({{'stage':str(stage),'files':expected,'free_bytes':shutil.disk_usage(stage).free}}))
'''
    with archive.open('rb') as f:
        result=subprocess.run(SSH+['sudo -n python3 -c '+shlex.quote(source)],stdin=f,capture_output=True,timeout=300)
    assert result.returncode==0,result.stderr.decode()[-3000:]
    (HERE/'stage.json').write_bytes(result.stdout)
    print(result.stdout.decode())


def operate(action):
    assert action in {'preflight','activate','open'}
    log = HERE/(action+'.log')
    with log.open('x',encoding='utf-8') as f:
        result=subprocess.run(SSH+['sudo -n python3 '+STAGE+'/rollout.py '+action],
                              stdout=f,stderr=subprocess.STDOUT,timeout=900,text=True)
    print(log.read_text(encoding='utf-8')[-6000:])
    assert result.returncode==0, 'Inspect retained '+str(log)


if __name__ == '__main__':
    if sys.argv[1] in {'preflight','activate','open'}: operate(sys.argv[1])
    else: {'probe':probe, 'prepare':prepare}[sys.argv[1]]()
