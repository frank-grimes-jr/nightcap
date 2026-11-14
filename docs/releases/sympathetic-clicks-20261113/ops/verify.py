"""Recheck public gameplay service state and publish only non-player receipts."""
import argparse
import json
from pathlib import Path
from probe import STAGE, call, write

LOAD="""
from pathlib import Path
import json,sys
d=Path('/opt/nightcap/releases')/STAGE
sys.path.insert(0,str(d))
import release as op
op.initialize()
"""

def main(action):
    if action=='preflight':
        report=json.loads(call(LOAD+"""
rec=op.read(op.EVIDENCE/'preflight.json')
print(json.dumps(dict(source=op.m['source'],image=rec['image'],rehearsal=rec['rehearsal'],manifest=rec['manifest'],
                      original_game=op.r.compact('game')==rec['services']['game'],gateway_open=op.r.compact('gateway')['running'])))
""",STAGE=STAGE))
    else:
        report=json.loads(call(LOAD+"""
dep=op.read(op.ACTIVE/'deployed.json')
before=op.read(op.EVIDENCE/'preflight.json')
current=op.native(before)
assert dep['source']==op.m['source'] and dep['image']==current['image_id'] and dep['gateway_open']
assert current['started_at']==dep['runtime']['started_at'] and op.r.compact('gateway')['running']
op.preserved(before,True,True,True)
checks=op.p.contract()
backup=op.read(op.ACTIVE/'backup.json')
assert backup['gzip_integrity'] and op.sha(Path(backup['path']))==backup['sha256']==dep['backup_sha256']
rows=op.sql('SELECT id,Name,clickeffect,clicktype,clicklevel,clicklevel2,casttime,casttime_,maxcharges,focuseffect FROM items WHERE id IN (610150,610338) ORDER BY id').splitlines()
spells=op.sql('SELECT id,name,buffdurationformula FROM spells_new WHERE id IN (44379,44380) ORDER BY id').splitlines()
descriptions=op.sql('SELECT id,type FROM db_str WHERE id IN (44379,44380) AND type=6 ORDER BY id').splitlines()
assert len(rows)==len(spells)==len(descriptions)==2
out=dict(result='PASS',source=dep['source'],image=dep['image'],client_release=dep['client_release'],
   client_channel_sha256=dep['client_channel_sha256'],gateway_open=True,started_at=current['started_at'],
   workers=sum(row[0]=='zone' for row in current['processes']),restarts=current['restart_count'],
   errors=current['errors'],binaries=op.binaries(True),cache=dep['cache'],backup_sha256=backup['sha256'],
   backup_integrity=True,items=rows,spells=spells,descriptions=descriptions,contract=checks,owner_gameplay_accepted=False,
   receipt_sha256={n:op.sha(op.ACTIVE/n) for n in ('deployed.json','verified-closed.json','backup.json','sql-installed.json')})
print(json.dumps(out))
""",STAGE=STAGE))
    write('preflight.json' if action=='preflight' else 'production-verified.json',report)
    print(json.dumps(report,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('phase',choices=('preflight','deployed'))
    main(parser.parse_args().phase)
