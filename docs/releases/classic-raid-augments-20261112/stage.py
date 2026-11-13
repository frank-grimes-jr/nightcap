"""Stage an independently checked, immutable raid payload for an explicit later action."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile
from probe import HERE, ROOT, SSH, remote

STAGE = 'classic-raid-augments-20261112-v2'
ART = ROOT/'artifacts'/STAGE
BUILD = '/tmp/nightcap-raid-augments-shipping-20261112-v3'
REVISION = '25219aac32db57982a2a925879b078d930292f4c'

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def main():
    ART.mkdir(parents=True,exist_ok=True)
    proof=json.loads(subprocess.check_output(['docker','exec','akk-stack-eqemu-server-1','cat',BUILD+'/inventory-shipping.json']))
    assert proof['base_zone']=='b737e641008b0816706a14478e7d2fde5b5930829f7e1bba4b6954b3c4fda598'
    source='#include "common/item_data.h"\n#include <cstddef>\n#include <cstdio>\nint main(){printf("%zu",sizeof(EQ::ItemData));'
    fields=['ID','LoreGroup','LoreFlag','Slots','AugType','ReqLevel','NoPet']
    source+=''.join('printf(" %zu",offsetof(EQ::ItemData,'+n+'));' for n in fields)+'puts("");}'
    command='cd '+BUILD+' && clang++ -std=c++20 -Isource -xc++ - -o layout && ./layout'
    layout=subprocess.check_output(['docker','exec','-i','akk-stack-eqemu-server-1','sh','-c',command],input=source.encode())
    proof['layout']=dict(zip(['size']+fields,map(int,layout.split()),strict=True))
    assert proof['layout']['size']==1332 and proof['layout']['ID']==440
    (HERE/'native.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf8')
    before=json.loads((HERE/'production-before.json').read_bytes())
    assert before['base_hashes']['bin/zone']==proof['base_zone'] and before['reserved_count']==before['procedure_count']=='0'
    assert before['services']['gateway']['running']
    payload={'content.sql':(ROOT/'docs/items/classic-raid-augments/content.sql').read_bytes().replace(b'\r\n',b'\n'),
        'rollout.py':(HERE/'rollout.py').read_bytes().replace(b'\r\n',b'\n'),'native.json':(HERE/'native.json').read_bytes()}
    for n,pin in proof['shipping'].items():
        target=ART/n
        subprocess.run(['docker','cp','akk-stack-eqemu-server-1:'+BUILD+'/bin/'+n,str(target)],check=True)
        data=target.read_bytes()
        assert digest(data)==pin
        payload['bin/'+n]=data
    pins={k:digest(v) for k,v in payload.items()}
    manifest=dict(authorization='Merge to test and then to main/production once your tests pass.',source_revision=REVISION,
        names=[row['name'] for row in json.loads((ROOT/'config/classic-raid-augments.json').read_bytes())],
        files=pins,binaries=proof['shipping'],base_image_id=before['services']['game']['image_id'],base_hashes=before['base_hashes'],
        prior_sha256=before['prior_sha256'],client_channel_sha256=before['client_channel_sha256'],wiki_pointer=before['public_wiki'])
    payload['manifest.json']=(json.dumps(manifest,indent=2)+'\n').encode()
    archive=ART/(STAGE+'.tar.gz')
    with tarfile.open(archive,'w:gz') as tar:
        for name,raw in payload.items():
            entry=tarfile.TarInfo(name);entry.size=len(raw);entry.mode=0o755 if name.startswith('bin/') else 0o600
            tar.addfile(entry,io.BytesIO(raw))
    upload='/home/ubuntu/'+STAGE+'.tar.gz'
    script="""from pathlib import Path
import tarfile,hashlib,fcntl,os
root=Path('/opt/nightcap/deploy/production');stage=Path('/opt/nightcap/releases')/NAME;upload=Path(UPLOAD);os.umask(0o077)
with (root/'.deployment.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not stage.exists() and hashlib.sha256(upload.read_bytes()).hexdigest()==ARCHIVE
 stage.mkdir(mode=0o700)
 with tarfile.open(upload) as tar:
  members=tar.getmembers();assert len(members)==len(PINS) and {m.name for m in members}==set(PINS)
  for m in members:
   path=stage/m.name;assert m.isfile() and path.resolve().is_relative_to(stage)
   raw=tar.extractfile(m).read();assert hashlib.sha256(raw).hexdigest()==PINS[m.name]
   path.parent.mkdir(exist_ok=True);path.write_bytes(raw);path.chmod(0o755 if m.name.startswith('bin/') else 0o600)
 upload.unlink()
 print(stage)
"""
    ssh=SSH[:-1]
    subprocess.run(ssh+['test ! -e '+upload+' && test ! -e /opt/nightcap/releases/'+STAGE],check=True)
    subprocess.run(['C:/Windows/System32/OpenSSH/scp.exe',*ssh[1:-1],str(archive),ssh[-1]+':'+upload],check=True,timeout=600)
    values=dict(NAME=STAGE,UPLOAD=upload,ARCHIVE=digest(archive.read_bytes()),PINS={k:digest(v) for k,v in payload.items()})
    print(remote('\n'.join(k+'='+repr(v) for k,v in values.items())+'\n'+script))
    (HERE/'staged.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')

if __name__=='__main__':main()
