"""Run isolated native earned-AA load/save controls; never access live PEQ."""
import argparse
import json

from aa_owned_core_controls import cases, verify
from aa_policy_preflight import read_json
import run_aa_projection as io


def counts():
    tables = ('account', 'character_data', 'character_alternate_abilities', 'inventory')
    return {table: int(io.sql('SELECT COUNT(*) FROM ' + table + ';').strip()) for table in tables}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', required=True)
    args = parser.parse_args()
    if args.runtime != '/tmp/nightcap-balance-owned-core-20260913':
        raise ValueError('Only the dedicated core runtime is allowed')
    if io.DATABASE != 'nightcap_balance_20260912':
        raise ValueError('Only the empty balance clone is allowed')
    io.RUNTIME = args.runtime
    if any(counts().values()):
        raise ValueError('Clone contains character fixtures; inspect before proceeding')
    original = io.digest(io.dump_tables())
    build = json.loads(io.command(['docker', 'exec', io.SERVER, 'cat',
                                  io.RUNTIME + '/native-build-manifest.json']))
    actual_binary = io.command(['docker', 'exec', io.SERVER, 'sha256sum',
                               io.RUNTIME + '/balance-zone']).decode().split()[0]
    if actual_binary != build['binary_sha256']:
        raise ValueError('Native binary differs from its build manifest')
    controls = cases(read_json(io.DOCS / 'gear-source-inputs.json'))
    results = []
    for case in controls:
        if any(counts().values()):
            raise ValueError('Unexpected fixtures between native cases')
        row = case['stored']
        if row:
            values = ','.join(str(int(row[k])) for k in ('id', 'aa_id', 'aa_value', 'charges'))
            io.sql('INSERT INTO character_alternate_abilities (id,aa_id,aa_value,charges) VALUES (' + values + ');')
        try:
            native = io.native(case['input'])
            result = {'id': case['id'], **native}
            results.append(result)
            result['check'] = verify(case, native['report'])
        finally:
            # Delete only an exact known fixture; preserve unexpected rows for diagnosis.
            observed = io.sql('SELECT id,aa_id,aa_value,charges FROM character_alternate_abilities ORDER BY id,aa_id;').strip()
            expected = '\t'.join(str(row[k]) for k in ('id', 'aa_id', 'aa_value', 'charges')) if row else ''
            if observed != expected:
                io.write(io.DOCS / 'aa-owned-core-unexpected.json', {'case': case, 'rows': observed, 'results': results})
                raise ValueError('Unexpected owned rows preserved for inspection')
            if row:
                predicate = ' AND '.join(k + '=' + str(int(row[k])) for k in ('id', 'aa_id', 'aa_value', 'charges'))
                io.sql('DELETE FROM character_alternate_abilities WHERE ' + predicate + ';')
    final = {'remaining_rows': counts(), 'full_catalog_unchanged': io.digest(io.dump_tables()) == original,
             'original_tables_sha256': original}
    if any(final['remaining_rows'].values()) or not final['full_catalog_unchanged']:
        raise ValueError('Native core cleanup or catalog verification failed')
    io.write(io.DOCS / 'aa-owned-core-inputs.json', {'cases': controls})
    io.write(io.DOCS / 'aa-owned-core-build.json', build)
    io.write(io.DOCS / 'aa-owned-core-native.json.gz', {
        'binary_sha256': actual_binary, 'cases': results, 'final': final,
        'scope': 'Native load/save, usable-prefix and purchase-gate readouts only. Refund/reset/class release/charge consumption remain unimplemented.'})
    print(json.dumps({'checks': [r['check'] for r in results], 'final': final}, indent=2))


if __name__ == '__main__':
    main()
