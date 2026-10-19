import gzip
import json
import os
from pathlib import Path
import unittest
import rabid_bear as policy

ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = json.loads(gzip.decompress((ROOT / 'tools/fixtures/rabid-bear-20261018.json.gz').read_bytes()))
ROWS = SNAPSHOT['tables']['spells_new']


class RabidBear(unittest.TestCase):
    def test_client_and_server_share_two_independent_visible_permanent_buffs(self):
        raw = ('\r\n'.join('^'.join('' if v is None else str(v) for v in r.values()) for r in ROWS) + '\r\n').encode('latin1')
        after = policy.client_spells(raw)
        self.assertEqual(policy.client_spells(after), after)
        for before, line in zip(ROWS, after.decode('latin1').splitlines()):
            result = dict(zip(before, line.split('^')))
            expected = {**before, **policy.changes(before['id'])}
            self.assertEqual(result, {k: '' if v is None else str(v) for k, v in expected.items()})
            self.assertEqual(result['short_buff_box'], '0')
            self.assertEqual(result['goodEffect'], '1')
            self.assertEqual(result['buffdurationformula'], '50')
            if before['id'] in policy.ROOTS:
                self.assertEqual(result['effectid2'], '374')
                self.assertEqual(result['effect_limit_value2'], str(policy.ILLUSION))
                self.assertNotIn('58', [result[f'effectid{i}'] for i in range(1, 13)])
            else:
                self.assertEqual(result['name'], policy.ILLUSION_NAME)
                self.assertEqual(result['effectid1'], '58')
        with self.assertRaises(ValueError):
            policy.client_spells(b'1^bad\n')
        with self.assertRaisesRegex(ValueError, 'missing'):
            policy.client_spells(b'\n'.join(raw.splitlines()[:-1]) + b'\n')

    def test_generated_migrations_are_current_and_preserve_other_fields(self):
        for rollback in (False, True):
            name = 'rabid-rollback.sql' if rollback else 'rabid-forward.sql'
            self.assertEqual((ROOT / 'docs/releases/thj-pet-scaling-20261018/content' / name).read_text(), policy.migration(ROWS, rollback))
        changed = {k for row in ROWS for k in policy.changes(row['id'])}
        self.assertEqual(changed, {'name', 'buffdurationformula', 'buffduration', 'short_buff_box'})

    @unittest.skipUnless(os.environ.get('NIGHTCAP_DB_TESTS') == '1', 'local DB rehearsal opt-in')
    def test_real_mariadb_forward_idempotence_and_rollback(self):
        from pok_hub_migration import read_sql
        statements = ['CREATE TEMPORARY TABLE nightcap_spell_template LIKE peq.spells_new;',
                      'CREATE TEMPORARY TABLE spells_new LIKE nightcap_spell_template;']
        for row in ROWS:
            statements.append('INSERT INTO spells_new (' + ','.join('`'+k+'`' for k in row) + ') VALUES (' +
                              ','.join(policy.sql_value(v) for v in row.values()) + ');')
        statements += [policy.migration(ROWS), policy.migration(ROWS)]
        statements.append("SELECT 'AFTER', COUNT(*) FROM spells_new WHERE buffdurationformula=50 AND short_buff_box=0;")
        statements.append(policy.migration(ROWS, rollback=True))
        for row in ROWS:
            statements.append(f"SELECT 'RESTORED_{row['id']}', COUNT(*) FROM spells_new WHERE {policy.predicate(row)};")
        output = read_sql('\n'.join(statements))
        values = dict(line.split('\t', 1) for line in output.splitlines() if '\t' in line)
        self.assertEqual(values['AFTER'], '9')
        for row in ROWS:
            self.assertEqual(values[f"RESTORED_{row['id']}"], '1')


if __name__ == '__main__':
    unittest.main()
