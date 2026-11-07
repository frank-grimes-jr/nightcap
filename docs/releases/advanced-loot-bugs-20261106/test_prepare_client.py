import hashlib
import unittest
import xml.etree.ElementTree as ET

from prepare_client import refresh_xml
from client_advanced_loot_ui import add_advanced_loot


class PrepareClient(unittest.TestCase):
    def setUp(self):
        root = ET.Element('XML')
        add_advanced_loot(root)
        ET.indent(root, space='\t')
        self.raw = ET.tostring(root, encoding='us-ascii').replace(
            b'<XML>', b'<XML>\n<!-- preserve me -->\n<Schema xmlns="EverQuestData" />\n<Screen item="PetInfoWindow"><Text>Keep &amp; protect</Text></Screen>')
        self.raw = self.raw.replace(b'<CX>32</CX>', b'<CX>20</CX>')

    def refresh(self, raw):
        return refresh_xml(raw, hashlib.sha256(raw).hexdigest())

    def test_preserves_non_loot_bytes_and_restores_geometry(self):
        for raw in (self.raw, self.raw.replace(b'\n', b'\r\n')):
            result = self.refresh(raw)
            self.assertIn(b'<!-- preserve me -->', result)
            self.assertIn(b'<Schema xmlns="EverQuestData" />', result)
            self.assertIn(b'<Screen item="PetInfoWindow"><Text>Keep &amp; protect</Text></Screen>', result)
            self.assertEqual(ET.fromstring(result).findtext("Button[@item='NCAL_Icon0']/DecalSize/CX"), '32')
            self.assertEqual(self.refresh(result), result)

    def test_rejects_baseline_drift(self):
        with self.assertRaisesRegex(ValueError, 'drift'):
            refresh_xml(self.raw, '0' * 64)

    def test_rejects_missing_or_duplicate_controls(self):
        for raw in (self.raw.replace(b'item="NCAL_Icon0"', b'item="OtherIcon"'),
                    self.raw.replace(b'</XML>', b'<Label item="NCAL_Icon0"><Text>duplicate</Text></Label></XML>')):
            with self.assertRaisesRegex(ValueError, 'inventory'):
                self.refresh(raw)


if __name__ == '__main__':
    unittest.main()
