"""Check native purchase ledgers against exact requested ranks and budgets."""
import argparse
import hashlib
import json
from pathlib import Path


def key(row):
    return row['profile'], row['tier'], row['aa_stage'], row['aa_policy']


def verify(inputs, report, catalog):
    expected = {key(b): b for b in inputs['builds']}
    actual = {key(b): b for b in report['builds']}
    if len(expected) != len(inputs['builds']) or len(actual) != len(report['builds']) or expected.keys() != actual.keys():
        raise ValueError('Missing, duplicate, or unexpected AA scenario')
    catalogs = {b['profile']: {r['rank_id']: r for r in b['aa_catalog']} for b in catalog['builds']}
    failures = []
    for k, b in expected.items():
        r = actual[k]
        problems = []
        ids = [p['rank_id'] for p in r['aa_purchases']]
        if ids != b['aa_rank_ids']:
            problems.append('purchase_order')
        spent = 0
        for purchase in r['aa_purchases']:
            rank = catalogs[b['profile']].get(purchase['rank_id'])
            if not rank:
                problems.append('rank_not_in_catalog')
                continue
            spent += rank['cost']
            if any(purchase[field] != rank[field] for field in ('ability_id','rank','cost','name')):
                problems.append('purchase_details')
            if purchase['points_spent'] != spent:
                problems.append('cumulative_cost')
        if (r['aa_budget'],r['aa_spent'],r['aa_remaining']) != (b['aa_budget'],spent,b['aa_budget']-spent) or spent > b['aa_budget']:
            problems.append('budget_accounting')
        if problems:
            failures.append({'scenario':k,'problems':sorted(set(problems))})
    return failures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('inputs','native','catalog','output'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    inputs, native, catalog = [json.loads(p.read_text()) for p in (args.inputs,args.native,args.catalog)]
    failures = verify(inputs,native,catalog)
    report = {'scenarios':len(inputs['builds']),
              'purchase_steps':sum(len(b['aa_purchases']) for b in native['builds']),
              'failures':failures,'scope':'Native purchase acceptance and ledger identity/cost; no AA activation or fight certification',
              'sha256':{name:hashlib.sha256(getattr(args,name).read_bytes()).hexdigest() for name in ('inputs','native','catalog')}}
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    return int(bool(failures))


if __name__ == '__main__':
    raise SystemExit(main())
