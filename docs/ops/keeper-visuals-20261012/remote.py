"""Executed on OVH by run.py; no database or process-lifecycle writes."""
import base64
import fcntl
import hashlib
import json
import os
import subprocess
from pathlib import Path

ROOT = Path('/opt/nightcap/deploy/production')
OUT = Path('/opt/nightcap/backups/keeper-visuals-20261012')
QUEST = ROOT / 'data/server/quests/global/Instance_Keeper.pl'
OLD_SHA = '2d5f6af9dcc015dc222a23b50ea338d594e0420c2570353e6f0e572ff4b86969'
candidate = base64.b64decode(PAYLOAD)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def install(data):
    info = QUEST.stat()
    temporary = QUEST.with_suffix('.pl.keeper-tmp')
    with temporary.open('xb') as f:
        os.fchmod(f.fileno(), info.st_mode)
        os.fchown(f.fileno(), info.st_uid, info.st_gid)
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(temporary, QUEST)

SEND = r'''
import json,socket,struct,sys,time
from pathlib import Path
cfg=json.loads(Path('/srv/nightcap/eqemu_config.json').read_text())['server']['world']
assert cfg['tcp']=={'ip':'127.0.0.1','port':'9001'}
def frame(kind,p):return struct.pack('<IB',len(p),kind)+p
def packet(op,p):return frame(5,struct.pack('<IH',len(p),op)+p)
with socket.create_connection(('127.0.0.1',9001),timeout=5) as s:
 s.sendall(frame(4,b'Zone\0'+cfg['key'].encode()+b'\0'))
 s.sendall(packet(0x4100,struct.pack('<i?3xqiI',22,False,0,0,0)))
 time.sleep(4)
 signal=int(sys.argv[1])
 if signal:
  for npc_id in range(999227,999234):
   s.sendall(packet(0x4506,struct.pack('<Bii64s',6,npc_id,signal,b'')))
  time.sleep(1)
'''

def reload(signal=0):
    subprocess.run(['docker','compose','exec','-T','game','python3','-c',SEND,str(signal)],
                   cwd=ROOT,check=True,capture_output=True,text=True)

RECOVERY = b'''
sub EVENT_SIGNAL {
    return unless $signal == 20261015;
    $npc->SendIllusionPacket({ race => 1, gender => 0, texture => 0,
        helmtexture => 0, size => 6 });
}
'''
os.umask(0o077)
with (ROOT / '.deployment.lock').open('a') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    current = QUEST.read_bytes()
    if ACTION == 'apply':
        assert sha(current) == OLD_SHA, 'Live quest drift: inspect before writing'
        OUT.mkdir(mode=0o700)
        (OUT / 'original.pl').write_bytes(current)
        (OUT / 'candidate.pl').write_bytes(candidate)
        install(candidate)
        reload(20261014)
        expected = candidate
    elif ACTION == 'rollback':
        original = (OUT / 'original.pl').read_bytes()
        saved_candidate = (OUT / 'candidate.pl').read_bytes()
        assert sha(original) == OLD_SHA
        assert current in (saved_candidate, original + RECOVERY, original), 'Live quest drift'
        install(original + RECOVERY)
        reload(20261015)
        install(original)
        reload()
        expected = original
    else:
        raise ValueError(ACTION)
    assert QUEST.read_bytes() == expected
    result = {'action':ACTION,'commit':COMMIT,'sha256':sha(expected),
              'quest_verified':True,'signal_sent':True,'rendered_acceptance':False}
    (OUT / (ACTION + '-result.json')).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
