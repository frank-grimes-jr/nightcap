import unittest
import xml.etree.ElementTree as ET
from client_gameplay_assets import ui_xml


def stock():
    root = ET.Element('XML', ID='EQInterfaceDefinitionLanguage')
    ET.SubElement(root, '{EverQuestData}Schema')
    screen = ET.SubElement(root, 'Screen', item='PetInfoWindow')
    for index in range(14):
        name = f'PIW_Pet{index}_Button'
        ET.SubElement(root, 'Button', item=name)
        ET.SubElement(screen, 'Pieces').text = name
    for name in ('PIW_PetHPGauge', 'PIW_PetTargetHPGauge', 'PIW_BuffWindow'):
        ET.SubElement(root, 'Gauge' if 'Gauge' in name else 'Screen', item=name)
        ET.SubElement(screen, 'Pieces').text = name
    return ET.tostring(root)


class PetManagementUI(unittest.TestCase):
    def test_roster_and_commands_are_visible_and_bounded(self):
        raw = ui_xml(stock(), 'pets')
        self.assertIn(b'<Schema xmlns="EverQuestData" xmlns:dt="EverQuestDataTypes"', raw)
        self.assertNotIn(b'ns0:', raw)
        root = ET.fromstring(raw)
        screen = root.find("Screen[@item='PetInfoWindow']")
        pieces = [n.text for n in screen.findall('Pieces')]
        self.assertEqual(len(pieces), len(set(pieces)))
        for index in range(3):
            self.assertIn(f'NCPM_Pet{index}', pieces)
            label = root.find(f"Label[@item='NCPM_Pet{index}Name']")
            self.assertEqual(label.findtext('EQType'), str(10031+index))
        self.assertIn('NCPM_All', pieces)
        self.assertEqual(len([n for n in pieces if n.startswith('NCPM_Command')]), 14)
        for name in pieces:
            node = next(n for n in root if n.get('item') == name)
            x, y, w, h = [int(node.findtext(p)) for p in ('Location/X', 'Location/Y', 'Size/CX', 'Size/CY')]
            if name.startswith('PIW_Pet') and name.endswith('_Button'):
                self.assertEqual((x,y,w,h), (-10000,-10000,1,1))
                continue
            self.assertGreaterEqual(min(x,y), 0)
            self.assertLessEqual(x+w, 330)
            self.assertLessEqual(y+h, 434) # title/border allowance
        self.assertIn('PIW_Pet0_Button', pieces) # existing native hotbuttons keep their backing controls

    def test_rejects_wrong_or_already_transformed_window(self):
        with self.assertRaises(ValueError):
            ui_xml(b'<XML/>', 'pets')
        with self.assertRaises(ValueError):
            ui_xml(ui_xml(stock(), 'pets'), 'pets')


if __name__ == '__main__': unittest.main()
