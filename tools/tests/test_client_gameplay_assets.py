import unittest
import client_gameplay_assets as assets


def spell(spell_id=1, **changes):
    fields = ['0'] * 237
    fields[0] = str(spell_id)
    fields[1] = 'Test spell'
    fields[13:18] = ['3000', '2500', '6000', '1', '10']
    fields[20] = '-10'
    for key, value in changes.items():
        fields[int(key[1:])] = str(value)
    return '^'.join(fields) + '\r\n'


class SpellAssets(unittest.TestCase):
    def test_only_cast_time_changes(self):
        source = spell()
        output, ids = assets.instant_dots(source.encode('latin1'))
        self.assertEqual(ids, [1])
        before, after = source.strip().split('^'), output.decode().strip().split('^')
        self.assertEqual([i for i in range(237) if before[i] != after[i]], [13])
        self.assertEqual(after[13], '0')
        self.assertTrue(output.endswith(b'\r\n'))
        self.assertEqual(assets.instant_dots(output)[0], output)

    def test_scope_and_duration_formulas(self):
        for kwargs, expected in [({}, True), ({'f17':0}, True), ({'f17':1}, True),
                                 ({'f83':1}, False), ({'f16':0}, False),
                                 ({'f16':16}, False), ({'f16':200}, True),
                                 ({'f86':334}, True), ({'f86':99}, False),
                                 ({'f20':10}, False)]:
            with self.subTest(kwargs=kwargs):
                output, ids = assets.instant_dots(spell(**kwargs).encode())
                self.assertEqual(bool(ids), expected)

    def test_refuses_malformed_or_duplicate_spell_rows(self):
        for source in (b'1^short\n', (spell()+spell()).encode(), spell(f13='bad').encode()):
            with self.subTest(source=source[:40]):
                with self.assertRaises(ValueError):
                    assets.instant_dots(source)


if __name__ == '__main__':
    unittest.main()
