"""Verify the complete hosted signed release and bind the admission-open receipt."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
from inventory_release_support import ROOT,HERE,ART,STAGE,remote,save


def main():
    env=os.environ|{'GOCACHE':str(ART/'go-cache')}
    args=['go','run','./cmd/inventory-verify','-previous',str(ART/'channel.json'),
          '-expected',str(ART/'signed/channel.json'),'-hosted']
    p=subprocess.run(args,cwd=ROOT/'eq-launcher',env=env,capture_output=True,text=True,timeout=1800)
    (ART/'hosted-client-verifier.log').write_text(p.stdout+'\n'+p.stderr,encoding='utf-8')
    if p.returncode:raise RuntimeError('Hosted verification failed; admissions remain closed. '+p.stderr[-1500:])
    result=json.loads(p.stdout)
    expected=hashlib.sha256((ART/'signed/channel.json').read_bytes()).hexdigest()
    assert result['hosted'] and result['release']==2026111202 and result['channel_sha256']==expected
    assert result['managed_files']==148 and result['changed_assets']==3 and result['existing_assets_preserved']==145
    save(HERE/'client-public-verification.json',result)
    binding=remote('PROOF='+repr(result)+'\nSTAGE_NAME='+repr(STAGE)+'''\nfrom pathlib import Path
import fcntl,hashlib,json,os
root=Path('/opt/nightcap/deploy/production');stage=Path(STAGE_NAME)
with (root/'.deployment.lock').open('a') as lock:
 # Asset downloads can overlap the publisher's final preservation reads. Bind
 # the receipt only after that action releases the deployment lock.
 fcntl.flock(lock,fcntl.LOCK_EX)
 assert hashlib.sha256((root/'data/public/channel.json').read_bytes()).hexdigest()==PROOF['channel_sha256']
 publication=json.loads((stage/'client/published.json').read_text())
 assert publication['channel_sha256']==PROOF['channel_sha256']
 with (stage/'public-client-verified.json').open('x') as out:
  json.dump(PROOF,out,indent=2);out.write(chr(10));out.flush();os.fsync(out.fileno())
print(json.dumps({'status':'bound_exact_hosted_signature','release':PROOF['release'],'files':PROOF['managed_files']}))
''',timeout=600)
    print(json.dumps(binding))


if __name__=='__main__':main()
