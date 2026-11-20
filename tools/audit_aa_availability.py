"""Read-only AA availability audit; never modifies content or player ownership."""
import datetime
import gzip
import itertools
import json
from pathlib import Path
import subprocess
import sys

from aa_tbs_policy import compile_policy, digest

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/audits/aa-availability-20261120'


def capture():
    config = json.loads((ROOT / 'config/aa-policy.json').read_text())
    reference = json.loads(gzip.decompress((ROOT / config['catalog']).read_bytes()))
    queries = {}
    for table, rows in reference.items():
        if table not in ('aa_ability', 'aa_ranks', 'aa_rank_effects', 'aa_rank_prereqs'):
            continue
        cols = sorted(rows[0])
        pairs = ','.join(repr(c) + ',`' + c + '`' for c in cols)
        queries[table] = 'SELECT JSON_OBJECT(' + pairs + ') FROM `' + table + '`'
    code = '''import importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('operator',Path('/opt/nightcap/releases/stock-worn-atk-20261113-v1/release.py'))
m=importlib.util.module_from_spec(s);s.loader.exec_module(m);m.initialize()
tables={name:[json.loads(line) for line in m.op.sql(query).splitlines()] for name,query in QUERIES.items()}
rules=m.op.sql("SELECT rule_name,rule_value FROM rule_values WHERE rule_name IN ('Expansion:CurrentExpansion','Expansion:UseCurrentExpansionAAOnly','World:UseClientBasedExpansionSettings','World:ExpansionSettings') ORDER BY ruleset_id,rule_name")
print(json.dumps({'tables':tables,'rules':rules,'game':m.r.compact('game')}))
'''
    ssh = ['C:/Windows/System32/OpenSSH/ssh.exe', '-i', 'C:/Users/verre/.ssh/nightcap_ovh',
           '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', '-o', 'StrictHostKeyChecking=yes',
           'ubuntu@135.148.47.202', 'sudo -n python3 -']
    result = subprocess.run(ssh, input='QUERIES='+repr(queries)+'\n'+code,
                            text=True, encoding='utf-8', capture_output=True, timeout=120)
    if result.returncode:
        raise RuntimeError(result.stderr[-2000:])
    live = json.loads(result.stdout)
    live['captured_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'production-catalog.json.gz').write_bytes(gzip.compress(json.dumps(live, sort_keys=True).encode(), mtime=0))
    print(json.dumps({'captured_utc':live['captured_utc'], 'tables':{k:len(v) for k,v in live['tables'].items()},'rules':live['rules']}))


def analyze():
    config = json.loads((ROOT / 'config/aa-policy.json').read_text())
    reference = json.loads(gzip.decompress((ROOT / config['catalog']).read_bytes()))
    live = json.loads(gzip.decompress((OUT / 'production-catalog.json.gz').read_bytes()))
    tables = live['tables']
    comparison = {}
    for name, rows in tables.items():
        canonical = lambda values: sorted(values, key=lambda v: json.dumps(v, sort_keys=True))
        comparison[name] = dict(rows=len(rows), matches_fixture=canonical(rows)==canonical(reference[name]),
                                sha256=digest(canonical(rows)))
    assert all(x['matches_fixture'] for x in comparison.values())
    rows = compile_policy(tables, config)
    by_key = {(r['ability_id'], r['ordinal']):r for r in rows}
    abilities = {a['id']:a for a in tables['aa_ability']}
    blocked = {}
    combinations = 0
    for count in (1, 2, 3):
        for classes in itertools.combinations(range(1, 17), count):
            combinations += 1
            mask = sum(1 << (c-1) for c in classes)
            for row in rows:
                if not row['classes'] & mask:
                    continue
                for aid, ordinal in row['prereqs'].items():
                    if not by_key[aid, ordinal]['classes'] & mask:
                        key = (row['ability_id'], aid)
                        item = blocked.setdefault(key, dict(ability=row['ability_id'], name=row['name'],
                            prerequisite=aid, prerequisite_name=abilities[aid]['name'], ranks=set(), builds=[]))
                        item['ranks'].add(row['ordinal'])
                        if list(classes) not in item['builds']:
                            item['builds'].append(list(classes))
    defects = [{**v,'ranks':sorted(v['ranks'])} for v in blocked.values()]
    assert set(blocked)=={(150,26)}
    result = dict(captured_utc=live['captured_utc'],tables=comparison,
        policy_sha256=digest(config),families=len({r['ability_id'] for r in rows}),
        ranks=len(rows),class_combinations=combinations,prerequisite_class_mismatches=defects,
        scope='Catalog/structural availability; native packet and purchase tests are separate; not player acceptance')
    (OUT / 'audit.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('tables','prerequisite_class_mismatches')}))


if __name__ == '__main__':
    if sys.argv[1:]==['--analyze']:analyze()
    elif sys.argv[1:]==['--capture']:capture()
    else:raise SystemExit('Use --capture for read-only SSH or --analyze for offline evidence')
