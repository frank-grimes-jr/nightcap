import unittest
from itertools import combinations
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
        node = ET.SubElement(root, 'Gauge' if 'Gauge' in name else 'Screen', item=name)
        if name == 'PIW_BuffWindow':
            # Actual RoF2 stock layout. Location/Size alone cannot override it.
            for tag, text in {'AutoStretch': 'true', 'LeftAnchorOffset': '112',
                              'TopAnchorOffset': '4', 'RightAnchorOffset': '4',
                              'BottomAnchorOffset': '4', 'LeftAnchorToLeft': 'true',
                              'TopAnchorToTop': 'true', 'RightAnchorToLeft': 'false',
                              'BottomAnchorToTop': 'false'}.items():
                ET.SubElement(node, tag).text = text
            ET.SubElement(node, 'Pieces').text = 'TileLayoutBox:PIW_Buttons'
        ET.SubElement(screen, 'Pieces').text = name
    return ET.tostring(root)


class PetManagementUI(unittest.TestCase):
    def test_effective_native_bounds_do_not_overlap_on_open_or_resize(self):
        root = ET.fromstring(ui_xml(stock(), 'pets'))
        screen = root.find("Screen[@item='PetInfoWindow']")

        def bounds(node, width, height):
            if node.findtext('AutoStretch') == 'true':
                # The native buff panel anchors its leading edges to the top/left
                # and trailing edges to the bottom/right of the client rectangle.
                self.assertEqual(node.findtext('LeftAnchorToLeft'), 'true')
                self.assertEqual(node.findtext('TopAnchorToTop'), 'true')
                self.assertEqual(node.findtext('RightAnchorToLeft'), 'false')
                self.assertEqual(node.findtext('BottomAnchorToTop'), 'false')
                x, y, right, bottom = [int(node.findtext(p)) for p in (
                    'LeftAnchorOffset', 'TopAnchorOffset', 'RightAnchorOffset', 'BottomAnchorOffset')]
                return x, y, width-right, height-bottom
            x, y, w, h = [int(node.findtext(p)) for p in ('Location/X', 'Location/Y', 'Size/CX', 'Size/CY')]
            return x, y, x+w, y+h

        # Minimum size, current owner's saved size, old tall window and a resize.
        for width, height in [(350, 326), (360, 348), (350, 434), (700, 700)]:
            with self.subTest(client=(width, height)):
                boxes = {}
                for piece in screen.findall('Pieces'):
                    name = piece.text
                    if name.startswith('PIW_Pet') and name.endswith('_Button'):
                        continue
                    # Pet-name labels intentionally sit on their own row buttons.
                    if name.startswith('NCPM_Pet') and name.endswith('Name'):
                        continue
                    node = next(n for n in root if n.get('item') == name)
                    rect = bounds(node, width, height)
                    self.assertTrue(0 <= rect[0] < rect[2] <= width, (name, rect))
                    self.assertTrue(0 <= rect[1] < rect[3] <= height, (name, rect))
                    boxes[name] = rect
                for (a, ar), (b, br) in combinations(boxes.items(), 2):
                    overlap = min(ar[2], br[2]) > max(ar[0], br[0]) and min(ar[3], br[3]) > max(ar[1], br[1])
                    self.assertFalse(overlap, (a, b, ar, br))
        buff = root.find("Screen[@item='PIW_BuffWindow']")
        self.assertEqual(buff.findtext('Pieces'), 'TileLayoutBox:PIW_Buttons')

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
            self.assertLessEqual(x+w, 350)
            self.assertLessEqual(y+h, 326) # title/border allowance
        self.assertIn('PIW_Pet0_Button', pieces) # existing native hotbuttons keep their backing controls

    def test_rejects_wrong_or_already_transformed_window(self):
        with self.assertRaises(ValueError):
            ui_xml(b'<XML/>', 'pets')
        with self.assertRaises(ValueError):
            ui_xml(ui_xml(stock(), 'pets'), 'pets')


if __name__ == '__main__': unittest.main()
