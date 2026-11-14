"""Stage exact main SQL, current shipping zone and signed RoF2 assets in a sealed directory."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import tarfile

from probe import HERE, ROOT, STAGE, call, transport, write
sys.path.insert(0,str(ROOT/'tools'))
import sympathetic_content as content

def digest(data):
    return hashlib.sha256(data).hexdigest()

def lf(path):
    return path.read_bytes().replace(b'\r\n',b'\n')

def unused_inverse():
    lines=['DELIMITER //','BEGIN NOT ATOMIC',' DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;',
           ' SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;',' START TRANSACTION;']
    for table,key,_,rows in content.groups(True):
        test=content.equal_group(table,key,rows)
        lines.append(f" IF NOT ({test}) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Inverse preimage mismatch'; END IF;")
    for table,fields in (content.REFERENCE_FIELDS|content.SAVED_SPELL_FIELDS).items():
        lines.append(content.reference_check(table,fields,saved=False))
    lines.extend([' DELETE FROM db_str WHERE id IN (44379,44380) AND type=6;',
                  ' DELETE FROM spells_new WHERE id IN (44379,44380);',' COMMIT;','END//','DELIMITER ;',''])
    return '\n'.join(lines).encode()

def main(args):
    assert re.fullmatch('[0-9a-f]{40}',args.source)
    assert len(args.layout)==8 and args.layout[:2]==[1332,440]
    before=json.loads((HERE/'production-before.json').read_bytes())
    client=ROOT/'artifacts/sympathetic-client/signed'
    forward=lf(ROOT/'eq-solo-gm/scripts/sympathetic-clicks.sql')
    disable=lf(ROOT/'docs/items/sympathetic-clicks/content/disable.sql')
    assert forward==content.migration().encode() and disable==content.migration(True).encode()
    files={'forward.sql':forward,'disable.sql':disable,'remove-unused.sql':unused_inverse(),
           'bin/zone':(ROOT/'artifacts/sympathetic-prod/zone').read_bytes(),'native.json':args.native.read_bytes(),
           'client/publish.py':lf(args.publisher)}
    for name in ('release.py','cache.py'):
        files[name]=lf(HERE/name)
    for name in ('spells_us.txt','dbstr_us.txt','channel.json','previous-channel.json','verification.json'):
        files['client/'+name]=(client/name).read_bytes()
    pins={k:digest(v) for k,v in files.items()}
    assert pins['bin/zone']==args.zone and args.zone!=before['base_hashes']['bin/zone']
    assert args.zone in files['native.json'].decode() and before['base_hashes']['bin/zone'] in files['native.json'].decode()
    assert pins['client/channel.json']=='1740eedf5ed7153fb5e2f262a147d0ffd8fb8574476963ac617912490def05ae'
    assert pins['client/publish.py']=='90361a515140b3cd30b1f4a8f65f6e18356422239ce04b32782fae7dc382c019'
    assert pins['client/previous-channel.json']==before['channel']
    assert pins['client/spells_us.txt']=='63067836b4b903dab1804d15bf1a1f73502ddc998a1a8ab9fdd5675b2780498b'
    assert pins['client/dbstr_us.txt']=='c8d8cc97e88a4256090e7c41192f909f6651b79e97b4f484140f3075b426501c'
    manifest=dict(source=args.source,authorization='Push to main and server',files=pins,
                  prior_operator=before['prior_operator'],prior_receipt=before['prior_receipt'],
                  base_image_id=before['services']['game']['image_id'],base_hashes=before['base_hashes'],
                  baseline_services=before['services'],binaries={'zone':args.zone},client_release=2026111301,
                  client_before=before['channel'],layout=args.layout,
                  reference_tables=sorted(content.REFERENCE_FIELDS|content.SAVED_SPELL_FIELDS))
    files['manifest.json']=(json.dumps(manifest,indent=2)+'\n').encode()
    archive=ROOT/'artifacts/sympathetic-prod'/(STAGE+'.tar.gz')
    with tarfile.open(archive,'w:gz') as tar:
        for name,data in files.items():
            entry=tarfile.TarInfo(name)
            entry.size=len(data)
            tar.addfile(entry,io.BytesIO(data))
    upload='/home/ubuntu/'+STAGE+'.tar.gz'
    ssh=transport.SSH[:-1]
    subprocess.run(ssh+['test ! -e '+upload+' && test ! -e /opt/nightcap/releases/'+STAGE],check=True)
    subprocess.run(['C:/Windows/System32/OpenSSH/scp.exe',*ssh[1:-1],str(archive),ssh[-1]+':'+upload],
                   check=True,timeout=600)
    print(call("""
import fcntl,hashlib,os,tarfile
from pathlib import Path
os.umask(0o077)
def sha(path):
 with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
dest=Path('/opt/nightcap/releases')/NAME
source=Path(UPLOAD)
with Path('/opt/nightcap/deploy/production/.deployment.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not dest.exists() and sha(source)==SHA
 with tarfile.open(source) as archive:
  members=archive.getmembers()
  assert len(members)==len(PINS) and set(PINS)=={m.name for m in members}
  dest.mkdir(mode=0o700)
  for m in members:
   path=dest/m.name
   assert m.isfile() and path.resolve().is_relative_to(dest)
   data=archive.extractfile(m).read()
   assert hashlib.sha256(data).hexdigest()==PINS[m.name]
   path.parent.mkdir(exist_ok=True)
   with path.open('xb') as f:f.write(data); f.flush(); os.fsync(f.fileno())
   path.chmod(0o755 if m.name=='bin/zone' else 0o600)
 source.unlink()
 print(dest)
""",NAME=STAGE,UPLOAD=upload,SHA=digest(archive.read_bytes()),PINS={k:digest(v) for k,v in files.items()}))
    write('staged.json',manifest)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',required=True)
    parser.add_argument('--native',type=Path,required=True)
    parser.add_argument('--zone',required=True)
    parser.add_argument('--layout',nargs=8,type=int,required=True)
    parser.add_argument('--publisher',type=Path,required=True)
    main(parser.parse_args())
