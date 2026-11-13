"""Read only the researched public item definitions, cap rules and active release identity."""
import argparse
import csv
import gzip
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from capture_lantern_content import SSH

REMOTE = """
import datetime, gzip, json, re, subprocess, sys
from pathlib import Path
root = Path('/opt/nightcap/deploy/production')
def sql(query):
    cmd = ['docker','compose','exec','-T','db','mariadb','--defaults-extra-file=/run/secrets/db_backup_config','--batch','--raw','--skip-column-names','--default-character-set=utf8mb4','peq']
    return subprocess.check_output(cmd, cwd=root, input=query, text=True, timeout=120).splitlines()
cols=[row.split('\\t')[0] for row in sql('SHOW COLUMNS FROM items')]
assert cols and all(re.fullmatch('[A-Za-z_][A-Za-z_0-9]*',name) for name in cols)
fields=','.join('CAST(`'+name+'` AS CHAR)' for name in cols)
ids=','.join(map(str,IDS))
q='START TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY; SELECT JSON_ARRAY('+fields+') FROM items WHERE id IN ('+ids+') ORDER BY id; ROLLBACK;'
rows=[dict(zip(cols,json.loads(row),strict=True)) for row in sql(q)]
data=dict(columns=cols,rows=rows,captured_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    rules=sql("SELECT ruleset_id,rule_name,rule_value FROM rule_values WHERE rule_name IN ('Character:ItemATKCap','Character:MaxLevel') ORDER BY 1,2"),
    rulesets=sql('SELECT ruleset_id,name FROM rule_sets ORDER BY 1'),active_ruleset=sql("SELECT value FROM variables WHERE varname='RuleSet'"),
    source='OVH production, SELECT-only public items/rules',client_channel_sha256=__import__('hashlib').sha256((root/'data/public/channel.json').read_bytes()).hexdigest(),
    zone_sha256=subprocess.check_output(['docker','compose','exec','-T','game','sha256sum','/opt/nightcap/bin/zone'],cwd=root,text=True).split()[0])
sys.stdout.buffer.write(gzip.compress(json.dumps(data,ensure_ascii=False).encode(),mtime=0))
"""

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    with (HERE/'worksheet-check.csv').open(encoding='utf-8-sig') as f:
        bases={int(r['base_id']) for r in csv.DictReader(f)}
    ids={i+o for i in bases | {11402} for o in (0,200000,400000,600000)} | {820542}
    cp=subprocess.run(SSH,input=('IDS='+repr(sorted(ids))+'\n'+REMOTE).encode(),capture_output=True,timeout=180)
    if cp.returncode:raise RuntimeError(cp.stderr.decode(errors='replace')[-1200:])
    data=json.loads(gzip.decompress(cp.stdout))
    assert len(data['columns'])>=280 and all(int(r['id']) in ids for r in data['rows'])
    with args.output.open('xb') as f:f.write(cp.stdout)
    print(data['captured_utc'],len(data['rows']),'public item rows',data['active_ruleset'],data['rules'])
