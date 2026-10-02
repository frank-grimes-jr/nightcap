import unittest
import hashlib
import json
from unittest.mock import patch
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
    def test_epic_spells_survive_regeneration_without_widening_eligibility(self):
        from epic05 import client_spells, load_catalog
        native = spell().encode()
        generated = client_spells(native, load_catalog())
        with patch.object(assets, 'SOURCE_SHA256', hashlib.sha256(native).hexdigest()):
            self.assertEqual(assets.restore_spell_classes(generated, native), (generated, []))
            self.assertEqual(assets.restore_spell_classes(native, native), (native, []))
            with self.assertRaises(ValueError):
                assets.restore_spell_classes(generated.replace(b'42800^Awaken the Oath', b'42800^Wrong'), native)

    def test_previously_generated_recall_remains_valid(self):
        fields=spell(3134).strip().split('^')
        fields[16:18]=['0','0'];fields[86:98]=['83']+['254']*11;fields[98]='6'
        native=('^'.join(fields)+'\r\n').encode()
        arrival=json.loads((assets.ROOT/'docs/ecommons-hub/plan.json').read_bytes())['arrival']
        generated=assets.recall_spell(native,arrival)
        with patch.object(assets,'SOURCE_SHA256',hashlib.sha256(native).hexdigest()):
            self.assertEqual(assets.restore_spell_classes(generated,native),(generated,[]))
            with self.assertRaises(ValueError):
                assets.restore_spell_classes(generated.replace(b'42604^Ancient Attunement',b'42604^Wrong spell'),native)

    def test_restore_only_class_fields_and_reject_identity_drift(self):
        native = spell(f105=255,f116=17).encode()
        widened = spell(f105=1,f116=17,f13=0).encode()
        with patch.object(assets,'SOURCE_SHA256',hashlib.sha256(native).hexdigest()):
            result, ids = assets.restore_spell_classes(widened,native)
            self.assertEqual(ids,[1])
            self.assertEqual(result,spell(f105=255,f116=17,f13=0).encode())
            self.assertEqual(assets.restore_spell_classes(result,native),(result,[]))
            for bad in (b'', widened*2, widened.replace(b'Test spell',b'Other'), spell(2).encode()):
                with self.assertRaises(ValueError): assets.restore_spell_classes(bad,native)
        with self.assertRaises(ValueError): assets.restore_spell_classes(widened,native)

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
