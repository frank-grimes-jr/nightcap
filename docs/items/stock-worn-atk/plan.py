"""Generate the reviewed ATK-only delta and reverse for existing databases."""
import argparse
import csv
import gzip
import io
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT/'tools'))
import thj_stock_scaling as scaling
from thj_item_migration import migration

def plan(data):
    current = {int(r['id']):r for r in data['rows']}
    changes, guards, summary = [], [], []
    for ident in sorted(scaling.worksheet_atk_targets()):
        base = scaling.stock()[ident]
        normal = current[ident]
        if normal['Name'] != base['Name'] or any(int(normal[f]) != int(base[f]) for f in scaling.FIELDS):
            raise ValueError(f'Normal stock mismatch: {ident}')
        family_changes=[]
        for offset, label, tier in scaling.TIERS:
            row = current[ident+offset]
            if row['Name'] != base['Name']+' ('+label+')':
                raise ValueError(f'Unexpected family member: {ident+offset}')
            attack = scaling.tier_target(base, tier)['attack']
            before = int(row['attack'])
            if before == attack:
                continue
            if before != int(base['attack']):
                raise ValueError(f'Unreviewed current ATK: {ident+offset}')
            family_changes.append((row, dict(row,attack=str(attack))))
            summary.append((ident, base['Name'], int(row['id']), label, before, attack))
        if family_changes:
            guards.append(normal)
            changes.extend(family_changes)
    return changes, guards, summary

def artifacts(data):
    changes, guards, summary=plan(data)
    results={}
    for name,pairs in [('forward',changes),('rollback',[(b,a) for a,b in changes])]:
        sql=migration(pairs,data['columns'],guard_rows=guards,procedure='nightcap_stock_worn_atk_20261113')
        results[name+'.sql.gz']=gzip.compress(sql.encode(),mtime=0)
    stream=io.StringIO(newline='')
    writer=csv.writer(stream,lineterminator='\n')
    writer.writerow(('base_id','name','item_id','tier','before_atk','after_atk'))
    writer.writerows(summary)
    results['changes.csv']=stream.getvalue().encode()
    return results

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args=parser.parse_args()
    data=json.loads(gzip.decompress((HERE/'production-items.json.gz').read_bytes()))
    for name,raw in artifacts(data).items():
        dest=HERE/name
        if args.check:
            # Gzip headers can differ across Python/zlib platforms.
            expected=dest.read_bytes()
            if name.endswith('.gz'):expected,raw=gzip.decompress(expected),gzip.decompress(raw)
            else:expected=expected.replace(b'\r\n',b'\n')
            if raw!=expected:raise SystemExit('Generated output differs: '+name)
        else:dest.write_bytes(raw)
