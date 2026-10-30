import unittest
from pathlib import Path
import csv
import client_spell_cast_times as timing
import client_gameplay_assets as assets


def row(spell_id, name, cast, ending='\r\n'):
    fields = ['0'] * 237
    fields[0:2] = [str(spell_id), name]
    fields[13] = str(cast)
    fields[86:98] = ['254'] * 12
    return '^'.join(fields).encode() + ending.encode()


class CastTimes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (Path(__file__).resolve().parents[2] / 'assets/spell-cast-times.csv').open(newline='') as f:
            cls.catalog = list(csv.DictReader(f))
        cls.raw = b''.join(row(r['id'], r['name'], 50) for r in cls.catalog)

    def test_level_one_wizard_nukes_use_server_duration(self):
        fixed, changed = timing.repair_cast_times(self.raw)
        spells = {int(r[0]): r for r in (line.split(b'^') for line in fixed.splitlines())}
        for spell_id, duration in [(54, 1000), (372, 1500), (374, 1000)]:
            self.assertEqual(int(spells[spell_id][13]), duration)
            self.assertIn(spell_id, changed)

    def test_only_reviewed_timing_fields_change_and_repeat_is_noop(self):
        fixed, changed = timing.repair_cast_times(self.raw)
        self.assertEqual(len(changed), 638)
        for before, after, entry in zip(self.raw.splitlines(keepends=True), fixed.splitlines(keepends=True), self.catalog):
            expected = before.split(b'^')
            expected[13] = entry['cast_time'].encode()
            self.assertEqual(after, b'^'.join(expected))
        self.assertEqual(timing.repair_cast_times(fixed), (fixed, []))

    def test_preserves_bard_custom_spells_instant_dots_and_unknown_50ms(self):
        extras = row(7, 'Hymn of Restoration', 2500) + row(42604, 'Ancient Attunement', 10000)
        extras += row(99990, 'Future intentional short cast', 50, '\n')
        dot = row(99991, 'DoT', 0).split(b'^')
        dot[16], dot[20], dot[86] = b'1', b'-10', b'0'
        extras += b'^'.join(dot)
        fixed, _ = timing.repair_cast_times(self.raw + extras)
        self.assertTrue(fixed.endswith(extras))
        self.assertEqual(assets.instant_dots(fixed)[0], fixed)

    def test_rejects_missing_duplicate_malformed_identity_and_timing_drift(self):
        first = self.raw.splitlines(keepends=True)[0]
        fields = first.split(b'^')
        wrong_name = list(fields); wrong_name[1] = b'Unexpected identity'
        wrong_time = list(fields); wrong_time[13] = b'999'
        for raw in (b'', self.raw[len(first):], self.raw + first, self.raw + b'1^short\n',
                    b'^'.join(wrong_name) + self.raw[len(first):],
                    b'^'.join(wrong_time) + self.raw[len(first):]):
            with self.subTest(raw=raw[:60]), self.assertRaises(ValueError):
                timing.repair_cast_times(raw)


if __name__ == '__main__':
    unittest.main()
