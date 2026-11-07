"""Stage reviewed release bytes privately; run one-shot guarded actions separately."""
import argparse,base64,hashlib,json,subprocess,sys,tarfile
from pathlib import Path
from capture_lantern_content import SSH
from last_lantern_content import ROOT

HERE=ROOT/'docs/adventure-journal/release-20261107'
ART=ROOT/'artifacts/last-lantern-20261107'
STAGE='/opt/nightcap/releases/last-lantern-20261107-v1'

def remote(code,timeout=900):
    r=subprocess.run(SSH,input=code,text=True,encoding='utf-8',capture_output=True,timeout=timeout)
    if r.returncode:raise RuntimeError(r.stderr[-3000:]+r.stdout[-1500:])
    return json.loads(r.stdout)

def probe():
    result=remote(r'''
import hashlib,importlib.util,json
from pathlib import Path
path=Path('/opt/nightcap/releases/dungeon-readiness-20261106-v1/rollout.py')
s=importlib.util.spec_from_file_location('prior',path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);m.initialize()
r=m.p.r;root=r.ROOT
game=r.state('game');networks=set(game['NetworkSettings']['Networks'])&set(r.state('db')['NetworkSettings']['Networks']);assert len(networks)==1
maps=MAPS
actual=json.loads(r.out('docker','exec',game['Id'],'python3','-c',
 'from pathlib import Path;import hashlib,json;names='+repr(list(maps))+";print(json.dumps({n:hashlib.sha256(Path('/srv/nightcap/maps/base/'+n+'.map').read_bytes()).hexdigest() for n in names}))"))
assert actual==maps,'Production maps differ from native geometry probes'
rules=m.p.sql("SELECT rule_name,rule_value FROM rule_values WHERE ruleset_id=1 AND rule_name IN ('Items:FreeTrade','Items:DisableNoDrop','Items:DisableNoTransfer','Items:DisableNoPet','World:FVNoDropFlag','TaskSystem:RecordCompletedTasks');").splitlines()
tables=m.p.sql('SHOW TABLES;').splitlines()
print(json.dumps({'prior_operator_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
 'base_image_id':game['Image'],'base_hashes':r.image_hashes(game['Image']),
 'game_network':next(iter(networks)),'runtime_before':r.runtime(),'players':m.player_count(),
 'maps':actual,'rules':rules,'tables':tables,'free_bytes':__import__('shutil').disk_usage(root).free}))
'''.replace('maps=MAPS','maps='+repr(json.loads((HERE/'geometry.json').read_text())['maps'])))
    assert result['players']==0
    baseline=json.loads((HERE/'production-native-baseline.json').read_text())
    assert result['base_image_id']==baseline['image_id'] and result['base_hashes']==baseline['image_files']
    (ART/'release-probe.json').write_text(json.dumps(result,indent=2)+'\n')
    public={k:v for k,v in result.items() if k not in ('runtime_before','tables')}
    (HERE/'release-probe.json').write_text(json.dumps(public,indent=2)+'\n')
    print(json.dumps({'status':'PASS','players':0,'maps':len(result['maps']),'runtime_files':len(result['runtime_before']),'free_bytes':result['free_bytes']}))

def package():
    before=json.loads((ART/'release-probe.json').read_text())
    stage=ART/'payload';stage.mkdir(exist_ok=False)
    proof=json.loads((HERE/'native-build.json').read_text());assert proof['status']=='PASS'
    binaries={n:proof['shipping']['candidate-'+n] for n in ('zone','world','shared_memory')}
    (stage/'bin').mkdir()
    for n,pin in binaries.items():
        subprocess.run(['docker','cp','akk-stack-eqemu-server-1:/tmp/nightcap-last-lantern-20261107-v1/candidate-'+n+'.stripped',str(stage/'bin'/n)],check=True,capture_output=True)
        assert hashlib.sha256((stage/'bin'/n).read_bytes()).hexdigest()==pin
    subprocess.run(['docker','cp','akk-stack-eqemu-server-1:/tmp/nightcap-last-lantern-20261107-v1/cache_check',str(stage/'cache_check')],check=True,capture_output=True)
    for name in ('rollout.py','native-build.json','last-lantern-catalog.json','last-lantern-setup.sql','last-lantern-enable.sql','last-lantern-disable.sql'):
        source=HERE/name if (HERE/name).exists() else HERE.parent/name
        (stage/name).write_bytes(source.read_bytes())
    runtime=['plugins/'+n for n in ('epic05.pl','epic05_data.pl','epic05_store.pl')]
    runtime+=['quests/global/items/900501.pl','quests/ecommons/The_Ancient_Chronicler.pl']
    runtime+=['quests/'+zone+'/'+str(identity)+'.pl' for zone,identity in [('ecommons',998900),('ecommons',998901),('ecommons',998902),('guktop',998903),('unrest',998904),('runnyeye',998905)]]
    after={}
    for name in runtime:
        target=stage/'runtime'/name;target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes((ROOT/'server-mods'/name).read_text(encoding='utf-8').encode())
        after[name]=hashlib.sha256(target.read_bytes()).hexdigest()
    client=stage/'client';client.mkdir()
    for name in ('channel.json','previous-channel.json','spells_us.txt'):(client/name).write_bytes((ART/'signed'/name).read_bytes())
    for name in ('publish.py','test_publish.py'):(client/name).write_bytes((HERE/'client'/name).read_bytes())
    # All required migration guard tables exist as empty schemas; only public
    # definitions are copied. No player rows enter this rehearsal database.
    definitions=json.loads((HERE/'production-schema.json').read_text())
    extra={'instance_list','character_activities','character_advloot_claims','character_corpses','instance_list_player','logsys_categories','rule_sets','rule_values','variables','content_flags','zone'}
    tables=sorted((set(definitions)|extra)&set(before['tables']))
    public={'items','spells_new','npc_types','spawn2','spawnentry','spawngroup','tasks','task_activities','titles','lootdrop_entries','merchantlist','tradeskill_recipe_entries','logsys_categories','rule_sets','rule_values','variables','content_flags','zone'}
    files={p.relative_to(stage).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in stage.rglob('*') if p.is_file()}
    manifest={k:before[k] for k in ('prior_operator_sha256','base_image_id','base_hashes','game_network','runtime_before')}
    manifest.update(owner_authorization='Push it to server and main. Ensure this is posted in the client notes',binaries=binaries,runtime_after=after,files=files,staging_tables=tables,public_clone_tables=sorted(public&set(tables)),source_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip())
    (stage/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    archive=ART/'last-lantern-release.tar.gz'
    with tarfile.open(archive,'w:gz') as t:
        for p in sorted(stage.rglob('*')):
            if p.is_file():t.add(p,arcname=p.relative_to(stage).as_posix(),recursive=False)
    receipt={'files':len(files)+1,'bytes':archive.stat().st_size,'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'manifest_sha256':hashlib.sha256((stage/'manifest.json').read_bytes()).hexdigest(),'binaries':binaries,'source_revision':manifest['source_revision']}
    (HERE/'package.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))

def stage():
    receipt=json.loads((HERE/'package.json').read_text());archive=ART/'last-lantern-release.tar.gz'
    assert hashlib.sha256(archive.read_bytes()).hexdigest()==receipt['archive_sha256']
    ssh=SSH[:-1];destination=ssh[-1];upload='/home/ubuntu/last-lantern-release-20261107.tar.gz'
    subprocess.run(['C:/Windows/System32/OpenSSH/scp.exe',*ssh[1:-1],str(archive),destination+':'+upload],check=True,timeout=600)
    result=remote(f'''from pathlib import Path
import hashlib,json,os,subprocess,tarfile
archive=Path({upload!r});stage=Path({STAGE!r});assert not stage.exists()
assert hashlib.sha256(archive.read_bytes()).hexdigest()=={receipt['archive_sha256']!r}
os.umask(0o077);stage.mkdir(mode=0o700)
with tarfile.open(archive) as t:
 for member in t.getmembers():
  assert member.isfile() and not member.issym() and not member.islnk()
  target=stage/member.name;assert target.resolve().is_relative_to(stage)
  target.parent.mkdir(parents=True,exist_ok=True)
  with target.open('xb') as f:f.write(t.extractfile(member).read());f.flush();os.fsync(f.fileno())
for n in ('bin/zone','bin/world','bin/shared_memory','cache_check'):(stage/n).chmod(0o755)
assert hashlib.sha256((stage/'manifest.json').read_bytes()).hexdigest()=={receipt['manifest_sha256']!r}
tests=subprocess.run(['python3','-B','-m','unittest','test_publish'],cwd=stage/'client',text=True,capture_output=True,timeout=120)
assert tests.returncode==0,tests.stderr[-2200:]
print(json.dumps({{'status':'staged_not_activated','files':{receipt['files']},'linux_tests':tests.stderr.strip().splitlines()[-1]}}))
''')
    (HERE/'staged.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

def action(name):
    # Detached action owns its locks and immutable attempt receipt. Do not replay.
    result=remote(f'''from pathlib import Path
import json,subprocess
stage=Path({STAGE!r});name={name!r};log=stage/(name+'.log');assert not log.exists(),'Inspect existing one-shot job'
with log.open('xb') as stream:
 p=subprocess.Popen(['python3','-u',str(stage/'rollout.py'),name],stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
print(json.dumps({{'action':name,'pid':p.pid,'log':str(log)}}))
''')
    (HERE/(name+'-job.json')).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('probe','package','stage','preflight','activate','open'))
    name=parser.parse_args().action
    if name in ('probe','package','stage'):globals()[name]()
    else:action(name)
