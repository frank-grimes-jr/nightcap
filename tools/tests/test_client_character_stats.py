import sys
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from client_gameplay_assets import ui_xml
from client_character_stats_ui import inventory_heroics_xml

SOURCE=Path('E:/EQ_Local_Dev/Client_RoF2_Dev/everquest_rof2/uifiles/default/EQUI_Inventory.xml')


class CharacterStatsUI(unittest.TestCase):
    def test_published_delta_preserves_all_existing_controls(self):
        raw=SOURCE.read_bytes()
        before=ET.fromstring(raw);after=ET.fromstring(inventory_heroics_xml(raw))
        added={n.get('item') for n in after}-{n.get('item') for n in before}
        self.assertEqual(len(added),14)
        self.assertTrue(all(n.startswith('IW_Heroic') for n in added))
        for node in before:
            other=after.find(node.tag+"[@item='"+node.get('item')+"']") if node.get('item') else after.find(node.tag)
            self.assertIsNotNone(other)
            if node.get('item')=='IW_InvPage':
                for piece in list(other.findall('Pieces')):
                    if piece.text in added:other.remove(piece)
            left=ET.fromstring(ET.tostring(node));right=ET.fromstring(ET.tostring(other))
            ET.indent(left);ET.indent(right)
            self.assertEqual(ET.tostring(left),ET.tostring(right),node.get('item'))

    def test_published_delta_rejects_reapplication_and_missing_stat(self):
        raw=SOURCE.read_bytes()
        with self.assertRaises(ValueError):inventory_heroics_xml(inventory_heroics_xml(raw))
        root=ET.fromstring(raw)
        root.remove(root.find("Label[@item='IWS_HeroicStrength']"))
        with self.assertRaises(ValueError):inventory_heroics_xml(ET.tostring(root))

    def test_inventory_heroics_use_native_values_beside_totals(self):
        result=ET.fromstring(ui_xml(SOURCE.read_bytes(),'inventory'))
        page=result.find("Page[@item='IW_InvPage']")
        pieces=[n.text for n in page.findall('Pieces')]
        for short,full,eqtype in [('STR','Strength',251),('STA','Stamina',252),
                ('AGI','Agility',254),('DEX','Dexterity',253),('WIS','Wisdom',255),
                ('INT','Intelligence',256),('CHA','Charisma',257)]:
            total=result.find("Label[@item='IW_"+short+"Number']")
            heroic=result.find("Label[@item='IW_Heroic"+full+"']")
            self.assertIsNotNone(heroic,short+' has no Inventory heroic total')
            plus=result.find("Label[@item='IW_Heroic"+full+"Plus']")
            self.assertEqual(heroic.findtext('EQType'),str(eqtype))
            self.assertEqual(plus.findtext('Text'),'+')
            self.assertEqual(heroic.findtext('Location/Y'),total.findtext('Location/Y'))
            self.assertGreaterEqual(int(plus.findtext('Location/X')),int(total.findtext('Location/X'))+int(total.findtext('Size/CX')))
            self.assertGreaterEqual(int(heroic.findtext('Location/X')),int(plus.findtext('Location/X'))+int(plus.findtext('Size/CX')))
            self.assertLessEqual(int(heroic.findtext('Location/X'))+int(heroic.findtext('Size/CX')),120)
            for node in (heroic,plus):
                self.assertEqual([node.findtext('TextColor/'+c) for c in ('R','G','B')],['214','178','40'])
                self.assertIn(node.get('item'),pieces)
            self.assertIn('Included in the total',heroic.findtext('TooltipReference'))

    def test_stats_page_contains_visible_server_backed_bonuses(self):
        result=ET.fromstring(ui_xml(SOURCE.read_bytes(),'inventory'))
        page=result.find("Page[@item='IW_StatPage']")
        self.assertIn('Screen:NCST_Bonuses',[n.text for n in page.findall('Pieces')])
        self.assertEqual(page.findtext('Style_VScroll'),'true')
        for text in ('Shield Block','Dodge modifier','Item spell haste*','Mana preservation*','Worn Faerune'):
            self.assertTrue(any(n.findtext('Text')==text for n in result.findall('Label')),text)
        self.assertEqual(sum(n.findtext('Text')=='Shield Block' for n in result.findall('Label')),1)
        self.assertIsNone(result.find("Screen[@item='NCST_Row1']"))
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
