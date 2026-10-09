import unittest
import xml.etree.ElementTree as ET

from client_advanced_loot_ui import add_advanced_loot


class AdvancedLootUI(unittest.TestCase):
    def setUp(self):
        self.root = ET.Element('XML')
        add_advanced_loot(self.root)
        self.screen = self.root.find("Screen[@item='NightcapAdvancedLootWnd']")
        self.controls = {n.get('item')[5:]: n for n in self.root if (n.get('item') or '').startswith('NCAL_')}

    def test_complete_unique_control_inventory(self):
        expected = set('Status Selected Help Drops Filters Options Previous Next Page All SearchText Search Clear Refresh Take Rule More Back PanelTitle Empty Leave Need Greed Pass Roll FreeGrab Inspect Assign Find'.split())
        expected |= {f'{prefix}{i}' for prefix in ('Row', 'Source', 'Ignore', 'Always', 'Never') for i in range(8)}
        expected |= {f'{prefix}{i}' for prefix in ('Setting', 'SettingHelp') for i in range(6)}
        expected |= {f'{prefix}{i}' for prefix in ('Filter', 'FilterHelp') for i in range(5)}
        self.assertEqual(set(self.controls), expected)
        pieces = [p.text for p in self.screen.findall('Pieces')]
        self.assertEqual(len(pieces), len(set(pieces)))
        self.assertEqual(set(pieces), {'NCAL_' + name for name in expected})
        for name, node in self.controls.items():
            self.assertEqual(node.findtext('ScreenID'), 'NCAL_' + name)

    def test_fits_smallest_supported_viewport(self):
        width = int(self.screen.findtext('Size/CX'))
        height = int(self.screen.findtext('Size/CY'))
        self.assertLessEqual(int(self.screen.findtext('Location/X')) + width, 640)
        self.assertLessEqual(int(self.screen.findtext('Location/Y')) + height, 480)
        for name, node in self.controls.items():
            x, y, w, h = [int(node.findtext(p)) for p in ('Location/X', 'Location/Y', 'Size/CX', 'Size/CY')]
            self.assertGreaterEqual(min(x, y), 0, name)
            self.assertLessEqual(x + w, width - 12, name)
            self.assertLessEqual(y + h, height - 28, name)

    def test_visible_buttons_do_not_overlap_in_each_panel(self):
        navigation = {'Filters', 'Options', 'Refresh'}
        panels = [
            {'Previous', 'Next', 'Take', 'Rule', 'More', 'All'} | {f'{p}{i}' for p in ('Row', 'Source', 'Always', 'Never') for i in range(8)},
            {'Drops', 'Search', 'Clear', 'Previous', 'Next', 'Rule', 'More'} | {f'{p}{i}' for p in ('Row', 'Ignore') for i in range(8)},
            {'Back'} | {f'Filter{i}' for i in range(5)},
            {'Back'} | {f'Setting{i}' for i in range(6)},
            {'Back', 'Inspect', 'Leave', 'Find', 'Need', 'Greed', 'Pass', 'Roll', 'FreeGrab', 'Assign'},
        ]
        for panel in panels:
            boxes = []
            for name in sorted(panel | navigation):
                node = self.controls[name]
                x, y, w, h = [int(node.findtext(p)) for p in ('Location/X', 'Location/Y', 'Size/CX', 'Size/CY')]
                for other, ox, oy, ow, oh in boxes:
                    self.assertFalse(x < ox + ow and ox < x + w and y < oy + oh and oy < y + h, (name, other))
                boxes.append((name, x, y, w, h))

    def test_inline_rules_are_labeled_and_explain_toggle_behavior(self):
        for i in range(8):
            for prefix, label in [('Always', 'Always Loot'), ('Never', 'Never Loot')]:
                node = self.controls[f'{prefix}{i}']
                self.assertEqual(node.findtext('Text'), '[ ] ' + label)
                self.assertIn('Ask each time', node.findtext('TooltipReference'))

    def test_second_insertion_is_refused(self):
        with self.assertRaises(ValueError):
            add_advanced_loot(self.root)


if __name__ == '__main__':
    unittest.main()
