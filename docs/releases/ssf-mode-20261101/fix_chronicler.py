"""Move the SSF oath to the spawned East Commonlands Chronicler; restore the PoK copy.

Quest-only: exact preimages, atomic replacement, global Quest reload with twelve
acknowledgments. No restart, SQL or access change. Run once from the repo root:
`python docs/releases/ssf-mode-20261101/fix_chronicler.py`.

Production's ecommons script equals the original PoK one (777d5793), not main's
mirror (which carries the unreleased Epic 0.5 journal hook). So the new ecommons
file is exactly the SSF script the first rollout put at PoK (78f0a5c2), and PoK
gets its original back. Nothing is uploaded.
"""
from pathlib import Path
import hashlib,subprocess,sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
ECOMMONS='quests/ecommons/The_Ancient_Chronicler.pl'
PREIMAGES={ECOMMONS:'777d57939ab1a813f502e1b389c7665f9da2febdb51a049a22bcd0e25a11413e',
           'quests/poknowledge/The_Ancient_Chronicler.pl':'78f0a5c20ae80cd0c749eef413ef041f616227d1fd74bd9dc9c364cfd4679bea'}
POK_ORIGINAL='777d57939ab1a813f502e1b389c7665f9da2febdb51a049a22bcd0e25a11413e'

REMOTE=r'''
from pathlib import Path
import datetime,fcntl,hashlib,json,os,shutil,struct,subprocess,time
ROOT=Path('/opt/nightcap/deploy/production');STAGE=Path('/opt/nightcap/releases/ssf-mode-20261101-v1')
OUT=STAGE/'evidence/chronicler-fix';ECOMMONS=__ECOMMONS__;PREIMAGES=__PREIMAGES__
POK='quests/poknowledge/The_Ancient_Chronicler.pl';POK_ORIGINAL=__POK__
def sha(b):return hashlib.sha256(b).hexdigest()
def cmd(*a):return subprocess.check_output(a,cwd=ROOT,text=True,timeout=60)
def save(n,v):
    with (OUT/n).open('x') as f:json.dump(v,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
def put(name,data):
    path=ROOT/'data/server'/name;st=path.stat();tmp=path.with_name(path.name+'.ssf-fix-'+str(time.time_ns()))
    with tmp.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
    os.chmod(tmp,st.st_mode);os.chown(tmp,st.st_uid,st.st_gid);os.replace(tmp,path)
SEND="""
import json,socket,struct,time
from pathlib import Path
cfg=json.loads(Path('/srv/nightcap/eqemu_config.json').read_text())['server']['world']
assert cfg['tcp']=={'ip':'127.0.0.1','port':'9001'}
def frame(kind,p):return struct.pack('<IB',len(p),kind)+p
with socket.create_connection(('127.0.0.1',9001),timeout=5) as s:
 s.sendall(frame(4,b'Zone\\0'+cfg['key'].encode()+b'\\0'))
 p=struct.pack('<i?3xqiI',22,False,0,0,0)
 s.sendall(frame(5,struct.pack('<IH',len(p),0x4100)+p))
 time.sleep(1)
"""
os.umask(0o077)
with (ROOT/'.deployment.lock').open('a') as lock,open('/var/lock/nightcap-gm.lock','a') as gm:
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(gm,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not (ROOT/'private/gm-maintenance.json').exists()
    deployed=json.loads((STAGE/'evidence/activation/deployed.json').read_text())
    game=json.loads(cmd('docker','inspect',cmd('docker','compose','ps','-q','game').strip()))[0]
    assert game['Image']==deployed['runtime']['image_id'] and game['State']['Health']['Status']=='healthy'
    assert game['State']['StartedAt']==deployed['runtime']['started_at'],'Game restarted since SSF activation'
    for name,digest in PREIMAGES.items():assert sha((ROOT/'data/server'/name).read_bytes())==digest,name+' drift'
    previous=(STAGE/'evidence/activation/chronicler-previous.pl').read_bytes();assert sha(previous)==POK_ORIGINAL
    new=(ROOT/'data/server'/POK).read_bytes();assert sha(new)==PREIMAGES[POK]
    if OUT.exists():assert not any(OUT.iterdir()),'Inspect prior attempt'
    else:OUT.mkdir(mode=0o700)
    check=STAGE/'chronicler-ecommons.pl';check.write_bytes(new);check.chmod(0o644)
    subprocess.run(['docker','run','--rm','--network','none','-v',str(check)+':/q.pl:ro','--entrypoint','perl',game['Image'],'-c','/q.pl'],check=True,capture_output=True)
    for name in PREIMAGES:shutil.copy2(ROOT/'data/server'/name,OUT/(name.split('/')[1]+'-before.pl'))
    save('started.json',{'ecommons_new':sha(new),'pok_restore':POK_ORIGINAL})
    put(ECOMMONS,new);put(POK,previous)
    since=datetime.datetime.now(datetime.timezone.utc).isoformat()
    cmd('docker','compose','exec','-T','game','python3','-c',SEND)
    for attempt in range(30):
        logs=cmd('docker','compose','logs','--no-color','--since',since,'game')
        if logs.count('Reloaded [Quest] (22)')>=12:break
        time.sleep(1)
    (OUT/'reload.log').write_text(logs)
    acks=[l for l in logs.splitlines() if 'Reloaded [Quest] (22)' in l]
    assert len(acks)==12,'Need twelve quest reload acknowledgments'
    assert not any(s in logs.lower() for s in ('quest error','perl error','error compiling','syntax error','failed to compile'))
    after={n:sha((ROOT/'data/server'/n).read_bytes()) for n in PREIMAGES}
    assert after=={ECOMMONS:sha(new),POK:POK_ORIGINAL}
    save('verified.json',{'files':after,'reload_acknowledgments':len(acks),'restart':False})
    print(json.dumps({'captured_at':since,'files':after,'acks':len(acks)}))
'''

if __name__=='__main__':
    code=(REMOTE.replace('__ECOMMONS__',repr(ECOMMONS)).replace('__PREIMAGES__',repr(PREIMAGES))
          .replace('__POK__',repr(POK_ORIGINAL)))
    script=HERE/'.fix_chronicler_remote.py';script.write_text(code,encoding='utf-8')
    try:subprocess.run([sys.executable,str(ROOT/'docs/quests/camil-chapterhouse/deployment/remote.py'),str(script)],check=True)
    finally:script.unlink()
