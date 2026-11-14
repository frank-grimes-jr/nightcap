"""Reconcile the single independent documentation release observed before any maintenance."""
from probe import STAGE, call, write
import json

OLD='releases/20261113-stock-worn-atk-v1'
NEW='releases/20261113-wiki-simple-ste-v1'

def main():
    result=json.loads(call("""
from pathlib import Path
import copy,fcntl,json,os,sys
stage=Path('/opt/nightcap/releases')/NAME
sys.path.insert(0,str(stage))
import release as op
os.umask(0o077)
with (op.ROOT/'.deployment.lock').open('a') as lock,open('/var/lock/nightcap-gm.lock','a') as gm:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 fcntl.flock(gm,fcntl.LOCK_EX|fcntl.LOCK_NB)
 op.initialize()
 before_path=op.EVIDENCE/'preflight.json'
 before=op.read(before_path)
 assert not op.ACTIVE.exists() and not (op.EVIDENCE/'preflight-before-wiki-release.json').exists()
 assert op.sha(stage/'manifest.json')==before['manifest'] and before['publication']['wiki']==OLD
 assert all(op.r.compact(n)==v for n,v in before['services'].items())
 assert not (op.ROOT/'private/gm-maintenance.json').exists() and op.sql("SELECT IS_FREE_LOCK('nightcap_gm_writes')").strip()=='1'
 new=op.h.publication()
 assert new=={**before['publication'],'wiki':NEW}
 wiki=op.ROOT/'data/public/wiki'
 assert (wiki/'current').resolve()==(wiki/NEW).resolve() and (wiki/NEW/'index.html').is_file()
 log=(stage/'activate.log').read_text()
 assert 'AssertionError: Public dependencies drifted' in log and 'preserved(before,False)' in log
 after=copy.deepcopy(before)
 after['publication']=new
 op.preserved(after,False)
 op.r.running(op.m['base_image_id'],op.binaries(False),before['services']['game']['restarts'])
 op.base.health()
 op.p.contract()
 op.r.closed_ports()
 assert op.a.prior.players()==0 and not op.ACTIVE.exists() and op.h.publication()==new
 # Keep the original preflight receipt, then atomically select the complete recheck.
 oldcopy=op.EVIDENCE/'preflight-before-wiki-release.json'
 os.link(before_path,oldcopy)
 newpath=op.EVIDENCE/'preflight-wiki-rechecked.json'
 op.save(newpath,after)
 os.replace(newpath,before_path)
 evidence=dict(old_wiki=OLD,new_wiki=NEW,old_receipt=op.sha(oldcopy),new_receipt=op.sha(before_path),
               original_game_and_gateway=True,players=0,all_other_controls_unchanged=True,sql_cache_rehearsal_preserved=True)
 op.save(op.EVIDENCE/'wiki-reconciliation.json',evidence)
 print(json.dumps(evidence))
""",NAME=STAGE,OLD=OLD,NEW=NEW))
    write('wiki-reconciliation.json',result)
    print(json.dumps(result))

if __name__=='__main__':
    main()
