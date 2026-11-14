"""Record the independently verified canonical client while the gateway is closed."""
import json
from probe import HERE, STAGE, call

def main():
    receipt=json.loads((HERE.parent/'client/public-verification.json').read_bytes())
    expected={'hosted':True,'release':2026111301,'signature':'valid against shipped production key',
             'channel_sha256':'1740eedf5ed7153fb5e2f262a147d0ffd8fb8574476963ac617912490def05ae',
             'managed_files':148,'changed_assets':2,'existing_assets_preserved':146,'verified_bytes':300643471}
    assert all(receipt[k]==v for k,v in expected.items())
    print(call("""
import fcntl,os,sys
from pathlib import Path
stage=Path('/opt/nightcap/releases')/NAME
sys.path.insert(0,str(stage))
import release as op
os.umask(0o077)
with (op.ROOT/'.deployment.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 op.initialize()
 assert not op.r.compact('gateway')['running'] and op.a.prior.players()==0
 assert op.r.compact('game')==op.read(op.ACTIVE/'verified-closed.json')['game']
 assert DATA['channel_sha256']==op.read(stage/'client/published.json')['channel_sha256']==op.sha(op.ROOT/'data/public/channel.json')
 op.save(stage/'public-client-verified.json',DATA)
 print('Paired HTTPS receipt verified and recorded.')
""",NAME=STAGE,DATA=receipt))

if __name__=='__main__':
    main()
