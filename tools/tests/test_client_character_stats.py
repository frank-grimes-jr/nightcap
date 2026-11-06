import sys
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from client_gameplay_assets import ui_xml

SOURCE=Path('E:/EQ_Local_Dev/Client_RoF2_Dev/everquest_rof2/uifiles/default/EQUI_Inventory.xml')


class CharacterStatsUI(unittest.TestCase):
    def test_stats_page_contains_visible_server_backed_bonuses(self):
        result=ET.fromstring(ui_xml(SOURCE.read_bytes(),'inventory'))
        page=result.find("Page[@item='IW_StatPage']")
        self.assertIn('Screen:NCST_Bonuses',[n.text for n in page.findall('Pieces')])
        self.assertEqual(page.findtext('Style_VScroll'),'true')
        for text in ('Shield Block','Hunt contribution','Dodge modifier','Item spell haste*','Mana preservation*','Worn Faerune'):
            self.assertTrue(any(n.findtext('Text')==text for n in result.findall('Label')),text)
        for name in ('IWS_CurrentHealAmount','IWS_CurrentSpellDamage','IWS_CurrentClairvoyance'):
            self.assertGreaterEqual(int(result.findtext("Label[@item='"+name+"']/EQType")),10300)
        tile=result.find("TileLayoutBox[@item='IW_Stats']"); section=result.find("Screen[@item='NCST_Bonuses']")
        self.assertGreater(int(section.findtext('Location/Y')),int(tile.findtext('Location/Y'))+int(tile.findtext('Size/CY')))
        self.assertGreaterEqual(int(tile.findtext('Size/CY')),((len(tile.findall('Pieces'))+1)//2)*16)
        self.assertEqual(len(result.findall("Page[@item='NCPA_Page']")),1)
        self.assertEqual(result.findtext("Label[@item='IW_Class']/EQType"),'10001')

    def test_original_stat_pieces_and_inventory_controls_are_retained(self):
        before=ET.fromstring(SOURCE.read_bytes());after=ET.fromstring(ui_xml(SOURCE.read_bytes(),'inventory'))
        for name in ('IW_Stats','IW_Subwindows'):
            b=before.find(".//*[@item='"+name+"']");a=after.find(".//*[@item='"+name+"']")
            self.assertLessEqual({n.text for n in b.findall('Pieces')},{n.text for n in a.findall('Pieces')})
        for tree in (before,after): ET.indent(tree)
        protected={n.get('item'):ET.tostring(n) for n in before if (n.get('item') or '').startswith('InvSlot')}
        self.assertTrue(protected)
        self.assertEqual(protected,{n.get('item'):ET.tostring(n) for n in after if n.get('item') in protected})


if __name__=='__main__':unittest.main()
