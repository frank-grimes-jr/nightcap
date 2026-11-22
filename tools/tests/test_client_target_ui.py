import sys
import unittest
from pathlib import Path
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from client_gameplay_assets import ui_xml


class TargetWindowTest(unittest.TestCase):
    stock = b'''<XML ID="EQInterfaceDefinitionLanguage">
      <Schema xmlns="EverQuestData" xmlns:dt="EverQuestDataTypes" />
      <Label item="Target_AggroNameSecondaryLabel"><ScreenID>aggro</ScreenID><EQType>304</EQType>
      <TopAnchorOffset>33</TopAnchorOffset><BottomAnchorOffset>47</BottomAnchorOffset></Label>
      <Screen item="Target_BuffWindow"><TopAnchorOffset>50</TopAnchorOffset></Screen>
      <Screen item="TargetWindow"><Size><CY>110</CY></Size><Pieces>Target_BuffWindow</Pieces></Screen></XML>'''

    def test_layout_preserves_aggro_and_buff_space(self):
        generated = ui_xml(self.stock, 'target')
        root = ET.fromstring(generated)
        label = root.find("Label[@item='NC_TargetDetails']")
        self.assertEqual('10040', label.findtext('EQType'))
        self.assertEqual('NC_TargetDetails', label.findtext('ScreenID'))
        self.assertEqual('304', root.findtext("Label[@item='Target_AggroNameSecondaryLabel']/EQType"))
        top = int(root.findtext("Screen[@item='Target_BuffWindow']/TopAnchorOffset"))
        height = int(root.findtext("Screen[@item='TargetWindow']/Size/CY"))
        self.assertEqual(110 - 50, height - top)
        self.assertLess(47, int(label.findtext('TopAnchorOffset')))
        self.assertLess(int(label.findtext('BottomAnchorOffset')), top)
        self.assertEqual(['Target_BuffWindow', 'NC_TargetDetails'],
                         [p.text for p in root.findall("Screen[@item='TargetWindow']/Pieces")])
        with self.assertRaises(ValueError):
            ui_xml(generated, 'target')

    def test_unknown_layout_rejected(self):
        with self.assertRaises(ValueError):
            ui_xml(self.stock.replace(b'>50<', b'>35<'), 'target')
