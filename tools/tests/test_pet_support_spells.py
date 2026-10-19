"""Prove paired data, reversible migration and cross-class buff coexistence."""
import os
import unittest
import pet_support_spells as policy
from rabid_bear import predicate, sql_value
from test_pet_equipment import ROOT


class PetSupportSpells(unittest.TestCase):
    def test_paired_client_data_and_effect_conservation(self):
        rows = policy.fixture_rows()
        raw = ('\r\n'.join('^'.join('' if v is None else str(v) for v in r.values()) for r in rows) + '\r\n').encode('latin1')
        result = policy.client_spells(raw)
        self.assertEqual(policy.client_spells(result), result)
        for before, line in zip(rows, result.decode('latin1').splitlines()):
            expected = policy.afterimage(before) if before['id'] in policy.IDS else before
            self.assertEqual(line.split('^'), ['' if v is None else str(v) for v in expected.values()])
            def effects(row):
                return sorted(tuple(row[f'{f}{i}'] for f in policy.FIELDS) for i in range(1, 13)
                              if row[f'effectid{i}'] not in (10, 254))
            self.assertEqual(effects(before), effects(expected))
        with self.assertRaises(ValueError):
            policy.client_spells(raw.replace(b'Augment Death', b'Altered Death'))

    def test_cross_class_slots_do_not_conflict_and_same_line_still_conflicts(self):
        rows = {r['id']: policy.afterimage(r) if r['id'] in policy.IDS else r for r in policy.fixture_rows()}
        # Native stacking arbitrates equal SPAs at equal slots; real native
        # execution is covered separately in the extracted C++ fixture.
        def overlap(a, b):
            return [i for i in range(1, 13) if a[f'effectid{i}'] == b[f'effectid{i}']
                    and a[f'effectid{i}'] not in (10, 254)]
        for mage in (327, 106, 107, 1472, 2119, 3237):
            for nec in policy.NECRO:
                for bst in policy.BEASTLORD:
                    self.assertEqual(overlap(rows[mage], rows[nec]), [])
                    self.assertEqual(overlap(rows[mage], rows[bst]), [])
                    self.assertEqual(overlap(rows[nec], rows[bst]), [])
        self.assertEqual(overlap(rows[661], rows[1414]), [7, 8, 9])
        self.assertEqual(overlap(rows[1430], rows[2619]), [10, 11, 12])

    def test_generated_migrations_current(self):
        for rollback in (False, True):
            name = 'pet-support-rollback.sql' if rollback else 'pet-support-forward.sql'
            self.assertEqual((ROOT / 'docs/releases/thj-pet-scaling-20261018/content' / name).read_text(),
                             policy.migration(policy.fixture_rows(), rollback))

    @unittest.skipUnless(os.environ.get('NIGHTCAP_DB_TESTS') == '1', 'local DB rehearsal opt-in')
    def test_real_mariadb_round_trip(self):
        from pok_hub_migration import read_sql
        rows = policy.fixture_rows()
        sql = ['CREATE TEMPORARY TABLE nightcap_spell_template LIKE peq.spells_new;',
               'CREATE TEMPORARY TABLE spells_new LIKE nightcap_spell_template;']
        for row in rows:
            sql.append('INSERT INTO spells_new (' + ','.join('`'+k+'`' for k in row) + ') VALUES (' +
                       ','.join(sql_value(v) for v in row.values()) + ');')
        sql += [policy.migration(rows), policy.migration(rows)]
        for row in rows:
            after = policy.afterimage(row) if row['id'] in policy.IDS else row
            sql.append(f"SELECT 'AFTER_{row['id']}', COUNT(*) FROM spells_new WHERE {predicate(after)};")
        sql.append(policy.migration(rows, rollback=True))
        for row in rows:
            sql.append(f"SELECT 'RESTORED_{row['id']}', COUNT(*) FROM spells_new WHERE {predicate(row)};")
        values = dict(line.split('\t', 1) for line in read_sql('\n'.join(sql)).splitlines() if '\t' in line)
        for row in rows:
            self.assertEqual(values[f"AFTER_{row['id']}"], '1')
            self.assertEqual(values[f"RESTORED_{row['id']}"], '1')


if __name__ == '__main__':
    unittest.main()
