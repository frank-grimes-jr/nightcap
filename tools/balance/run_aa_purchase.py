"""Clone-only AA purchase/grant persistence controls with injected SQL failures."""
import argparse
import json

from aa_purchase_controls import assess, cases
from aa_policy_preflight import read_json
from run_aa_owned_core import counts
import run_aa_projection as io


TRIGGER = 'nightcap_aa_purchase_test_failure'


def trigger_count():
    return int(io.sql("SELECT COUNT(*) FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA='"
                      + io.DATABASE + "' AND TRIGGER_NAME='" + TRIGGER + "';").strip())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', required=True, choices=('before', 'after'))
    parser.add_argument('--release-candidate', action='store_true', help='Verify purchases against the isolated release candidate')
    args = parser.parse_args()
    if io.DATABASE != 'nightcap_balance_20260912' or any(counts().values()) or trigger_count():
        raise ValueError('Only the empty isolated balance clone without a failure trigger is allowed')
    io.RUNTIME = '/tmp/nightcap-balance-aa-purchase-' + args.phase + '-20260913'
    if args.release_candidate:
        if args.phase != 'after': raise ValueError('Release candidate requires after expectations')
        io.RUNTIME = '/tmp/nightcap-balance-aa-release-after-20260913'
    original = io.digest(io.dump_tables())
    build = json.loads(io.command(['docker', 'exec', io.SERVER, 'cat', io.RUNTIME + '/native-build-manifest.json']))
    binary = io.command(['docker', 'exec', io.SERVER, 'sha256sum', io.RUNTIME + '/balance-zone']).decode().split()[0]
    if binary != build['binary_sha256']:
        raise ValueError('Native binary differs from its build manifest')
    controls = cases(read_json(io.DOCS / 'gear-source-inputs.json'))
    results = []
    for case in controls:
        if any(counts().values()):
            raise ValueError('Unexpected fixtures between purchase controls')
        character_id = int(case['input']['builds'][0]['test_character_id'])
        probe = case['input']['aa_ownership_probe']
        values = ','.join('(' + ','.join(str(int(row[k])) for k in ('id', 'aa_id', 'aa_value', 'charges')) + ')' for row in case['rows'])
        io.sql("START TRANSACTION; INSERT INTO character_data (id,name,aa_points,aa_points_spent,e_expended_aa_spent) VALUES ("
               + str(character_id) + ",'AA_Lifecycle_Probe'," + str(case['initial_wallet']) + ','
               + str(probe['initial_spent_points']) + ',5);'
               + ('INSERT INTO character_alternate_abilities (id,aa_id,aa_value,charges) VALUES ' + values + ';' if values else '')
               + 'COMMIT;')
        injected = False
        try:
            if case['fail_character_update']:
                io.sql('CREATE TRIGGER ' + TRIGGER + ' BEFORE UPDATE ON character_data FOR EACH ROW '
                       "SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='injected AA character update failure';")
                injected = True
            native = io.native(case['input'])
            results.append({'id': case['id'], **native, 'assessment': assess(case, native['report'])})
        finally:
            if injected:
                io.sql('DROP TRIGGER ' + TRIGGER + ';')
            observed = io.sql('SELECT id,aa_id,aa_value,charges FROM character_alternate_abilities ORDER BY id,aa_id;').strip()
            charges = 1 if probe['first_rank_id'] == 4702 else 0
            expected = {str(character_id) + '\t' + str(probe['first_rank_id']) + '\t' + str(n) + '\t' + str(charges) for n in range(1, 7)}
            wallets = {case['initial_wallet']} | {s['unspent_points'] for s in case['expected']}
            character = io.sql('SELECT id,name,aa_points FROM character_data ORDER BY id;').strip()
            if not set(observed.splitlines()).issubset(expected) or character not in {str(character_id) + '\tAA_Lifecycle_Probe\t' + str(w) for w in wallets}:
                io.write(io.DOCS / 'aa-purchase-unexpected.json', {'case': case, 'owned': observed, 'character': character, 'results': results})
                raise ValueError('Unexpected fixture state preserved for inspection')
            predicate = 'id=' + str(character_id) + ' AND aa_id=' + str(probe['first_rank_id']) + ' AND aa_value BETWEEN 1 AND 6 AND charges=' + str(charges)
            io.sql('START TRANSACTION; DELETE FROM character_alternate_abilities WHERE ' + predicate + ';'
                   + 'DELETE FROM character_data WHERE id=' + str(character_id)
                   + " AND name='AA_Lifecycle_Probe' AND aa_points IN (" + ','.join(str(w) for w in sorted(wallets)) + '); COMMIT;')
    final = {'remaining_rows': counts(), 'full_catalog_unchanged': io.digest(io.dump_tables()) == original,
             'original_tables_sha256': original, 'failure_trigger_remaining': trigger_count()}
    if any(final['remaining_rows'].values()) or not final['full_catalog_unchanged'] or final['failure_trigger_remaining']:
        raise ValueError('Purchase cleanup or catalog verification failed')
    stem = 'aa-release-purchase-regression' if args.release_candidate else 'aa-purchase-' + args.phase
    io.write(io.DOCS / (stem + '-inputs.json'), {'cases': controls})
    io.write(io.DOCS / (stem + '-build.json'), build)
    io.write(io.DOCS / (stem + '.json.gz'), {'binary_sha256': binary, 'cases': results, 'final': final,
             'scope': 'Native purchase, explicit and silent grant persistence with synthetic rows and SQL update failures. No network-loss, full reconnect, auto-grant loop or class-release simulation.'})
    if any(r['assessment']['passed'] != (args.phase == 'after' or case['expected_before_pass']) for case, r in zip(controls, results)):
        raise ValueError('Native controls differ from expected before/after state; evidence preserved')
    print(json.dumps({'phase': args.phase, 'cases': [{'id': r['id'], 'passed': r['assessment']['passed'],
          'differences': len(r['assessment']['differences'])} for r in results], 'final': final}, indent=2))


if __name__ == '__main__':
    main()
