import unittest
import thj_behavior_content as content
import thj_behavior_client as client
class ClientPairing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        data=content.snapshot();cols=data['schemas']['spells_new']
        cls.base=('\r\n'.join('^'.join('' if r[c] is None else str(r[c]) for c in cols) for r in data['tables']['spells_new'])+'\r\n').encode('latin1')
        cls.result,cls.audit=client.spells(cls.base)
        cls.rows={int(f[0]):f for f in (line.split('^') for line in cls.result.decode('latin1').splitlines())}
    def test_new_identity_and_exact_mage_focus(self):
        self.assertEqual(self.rows[43220][1],'Dimensional Shielding')
        self.assertEqual(self.rows[5915][20:21],['100']);self.assertEqual(self.rows[11064][20:21],['150'])
        self.assertEqual(self.rows[2775][98],'41')
        self.assertTrue(all(len(row)==237 for row in self.rows.values()))
    def test_classes_and_unrelated_spell_identity_preserved(self):
        for old in self.base.decode('latin1').splitlines():
            f=old.split('^');new=self.rows[int(f[0])]
            self.assertEqual(f[104:120],new[104:120]);self.assertEqual(f[1],new[1])
    def test_new_aa_title_and_descriptions_do_not_erase_other_strings(self):
        result=client.strings(b'99^1^Keep me\r\n')
        self.assertIn(b'99^1^Keep me',result);self.assertIn(b'43220^1^Dimensional Shielding',result);self.assertIn(b'43220^4^Protects spellcasting',result)
if __name__=='__main__':unittest.main()
