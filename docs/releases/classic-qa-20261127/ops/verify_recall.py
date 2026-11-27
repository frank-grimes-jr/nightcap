"""Check the General tab's read-only list, ownership packet and persisted rank on LocalDev."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

from build_preview import OUT


def main(stage):
    account=os.environ['NIGHTCAP_QA_ACCOUNT']
    character=os.environ['NIGHTCAP_QA_CHARACTER']
    assert re.fullmatch('ncqa[a-z]{5}',account) and re.fullmatch('Tor[a-z]{5}',character)
    assert os.environ['NIGHTCAP_QA_PASSWORD']
    pins=json.loads((OUT/'build.json').read_bytes())
    import hashlib
    probe=OUT/'recall_probe.exe'
    assert hashlib.sha256(probe.read_bytes()).hexdigest()==pins['recall_probe.exe']
    command=['docker','exec','akk-stack-mariadb-1','mariadb','--defaults-extra-file=/run/local-secrets/client.cnf','-NB','peq','-e']
    identity=f"FROM character_data c JOIN account a ON a.id=c.account_id WHERE c.name='{character}' AND a.name='{account}' AND c.class=17 AND c.race=8"
    query='SELECT c.aa_points, c.aa_points_spent, (SELECT COUNT(*) FROM character_alternate_abilities ca WHERE ca.id=c.id AND ca.aa_id=22200 AND ca.aa_value=1) '+identity
    def state():
        return list(map(int,subprocess.check_output([*command,query]).split()))
    initial=state()
    rows=[]
    for _ in range(2):
        with tempfile.TemporaryDirectory(prefix='recall-preview-') as tmp:
            args=[str(probe),'127.0.0.1:5998',account,'--password-env','--char',character,
                  '--plugins',tmp,'--seconds','8']
            env=dict(os.environ,EQ_GAME_DIR='E:/Nightcap_QA',HAILSTONE_DATA_DIR=tmp)
            p=subprocess.run(args,cwd=tmp,env=env,capture_output=True,text=True,errors='replace',timeout=160)
            output=p.stdout+p.stderr
        row=next((line.strip() for line in output.splitlines() if line.startswith('NIGHTCAP_RECALL ')),None)
        assert p.returncode==0 and row and 'Camped out.' in output, 'Client did not complete diagnostic login and camp'
        assert 'zone profile: race 8 class 17 level 1' in output
        print(row,flush=True)
        if stage=='candidate':
            assert 'class=17 catalog=1 owned=1 general=1 family=2220 spell=42604' in row
            assert 'title=Ancient Attunement hotkey_string=Nightcap Recall preview_label=Ancient Attunement' in row
        rows.append(row)
    after=state()
    assert initial[:2]==after[:2] and len(after)==3
    if stage=='candidate':
        assert after[2]==1
    report=dict(stage=stage,source='local disposable primary class 17, two fresh authenticated camps',
                rank_before=initial[2],rank_after=after[2],aa_points_unchanged=True,
                results=rows,hailstone_probe=pins['recall_probe.exe'],mouse_hotbar_test='open')
    (OUT/('local-recall-'+stage+'.json')).write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('stage',choices=['baseline','candidate'])
    main(p.parse_args().stage)

