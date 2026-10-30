"""Read-only current client/wiki/services baseline; fetch verified public assets."""
import base64,datetime,hashlib,json,subprocess
from pathlib import Path
from urllib.request import Request,urlopen

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
PRIVATE=ROOT/'.local/cast-bar/release'
SSH=['C:/Windows/System32/OpenSSH/ssh.exe','-i','C:/Users/verre/.ssh/nightcap_ovh','-o','BatchMode=yes','-o','ConnectTimeout=10','-o','StrictHostKeyChecking=yes','ubuntu@135.148.47.202']

def remote(code,timeout=240):
    p=subprocess.run(SSH+['sudo -n python3 -'],input=code,text=True,capture_output=True,timeout=timeout)
    if p.returncode:raise RuntimeError((p.stdout+p.stderr)[-4000:])
    return json.loads(p.stdout)

def main():
    PRIVATE.mkdir(parents=True,exist_ok=True)
    result=remote('''from pathlib import Path
import base64,datetime,hashlib,json,shutil,subprocess
base=Path('/opt/nightcap/deploy/production');public=base/'data/public'
raw=(public/'channel.json').read_bytes()
manifest=json.loads(base64.b64decode(json.loads(raw)['manifest'],validate=True))
services={}
for name in ['game','gateway','db','web','tunnel']:
 cid=subprocess.check_output(['docker','compose','ps','-aq',name],cwd=base,text=True).strip()
 row=json.loads(subprocess.check_output(['docker','inspect',cid],text=True))[0];state=row['State']
 assert state['Running'] and not state['OOMKilled']
 if name in ['game','db']:assert state['Health']['Status']=='healthy'
 services[name]={k:row[k] for k in ['Id','Image','RestartCount']}
 services[name]['state']={k:state[k] for k in ['Running','StartedAt','OOMKilled']}
pointer=public/'wiki/current';assert pointer.is_symlink()
wiki=pointer.readlink().name
print(json.dumps(dict(observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),channel_b64=base64.b64encode(raw).decode(),channel_sha256=hashlib.sha256(raw).hexdigest(),release=manifest['release'],services=services,wiki_release=wiki,wiki_manifest=json.loads((base/'website-history'/wiki/'manifest.json').read_text()),config_sha256=hashlib.sha256((base/'nginx.conf').read_bytes()).hexdigest(),disk_free=shutil.disk_usage(base).free)))
''')
    assert result['release']==2026103001,'New client release: reconcile before proceeding'
    assert result['wiki_release']=='20261030-public-cazic-v1','New wiki release: reconcile before proceeding'
    channel=base64.b64decode(result.pop('channel_b64'),validate=True)
    assert hashlib.sha256(channel).hexdigest()==result['channel_sha256']=='fa9488d44023362d7d8e792fdd5eae6af2c9e8cdc0a26f3d31a6d734ba578f6b'
    (PRIVATE/'previous-channel.json').write_bytes(channel)
    manifest=json.loads(base64.b64decode(json.loads(channel)['manifest'],validate=True))
    assert len(manifest['files'])==148
    wanted={'dinput8.dll','nightcap-patch-sites.json','nightcap-patches.cfg','dbstr_us.txt','spells_us.txt'}
    for f in manifest['files']:
        if f['path'] not in wanted:continue
        assert f['url'].startswith('https://play.nightcapgame.org/release/')
        with urlopen(Request(f['url'],headers={'User-Agent':'NightcapLauncher/0.6.0','Accept-Encoding':'identity'}),timeout=60) as response:
            raw=response.read(f['size']+1)
        assert len(raw)==f['size'] and hashlib.sha256(raw).hexdigest()==f['sha256'],f['path']
        dest=PRIVATE/'baseline-assets'/f['path'];dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
        wanted.remove(f['path'])
    assert not wanted,wanted
    (HERE/'baseline.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ['release','wiki_release','disk_free','channel_sha256']}))

if __name__=='__main__':main()
