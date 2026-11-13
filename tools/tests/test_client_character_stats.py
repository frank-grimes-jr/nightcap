import sys
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from client_gameplay_assets import ui_xml
from client_inventory_summary_ui import add_inventory_summary,inventory_summary_xml,STATS

SOURCE=Path('E:/EQ_Local_Dev/Client_RoF2_Dev/everquest_rof2/uifiles/default/EQUI_Inventory.xml')


def canonical(node):
    node=ET.fromstring(ET.tostring(node));ET.indent(node)
    return ET.tostring(node)


class CharacterStatsUI(unittest.TestCase):
    def test_inventory_layout_has_ordered_combat_rows_caps_and_heroics(self):
        result=ET.fromstring(ui_xml(SOURCE.read_bytes(),'inventory'))
        page=result.find("Page[@item='IW_InvPage']");pieces=[n.text for n in page.findall('Pieces')]
        ys=[]
        for name in ('AC','MIT','AVD','ATK','DMG','HEAL'):
            node=result.find("Label[@item='IW_"+name+"Number']")
            ys.append(int(node.findtext('Location/Y')))
            if name!='AC':self.assertEqual(node.findtext('EQType'),str({'MIT':10500,'AVD':10501,'ATK':10502,'DMG':10503,'HEAL':10504}[name]))
        self.assertEqual(ys,[90,104,118,132,146,160])
        for i,(short,full) in enumerate(STATS):
            total=result.find("Label[@item='IW_"+short+"Number']")
            cap=result.find("Label[@item='IW_Cap"+full+"']")
            heroic=result.find("Label[@item='IW_Heroic"+full+"']")
            self.assertEqual([n.findtext('EQType') for n in (total,cap,heroic)],list(map(str,(10600+i,10800+i,10700+i))))
            self.assertEqual(len({n.findtext('Location/Y') for n in (total,cap,heroic)}),1)
            self.assertEqual([total.findtext(x) for x in ('AlignLeft','AlignCenter','AlignRight')],['false','false','true'])
            for node in (cap,heroic):
                self.assertEqual([node.findtext(x) for x in ('AlignLeft','AlignCenter','AlignRight')],['true','false','false'])
            right=0
            for node in (total,cap,heroic):
                x=int(node.findtext('Location/X'));self.assertGreaterEqual(x,right)
                right=x+int(node.findtext('Size/CX'));self.assertLessEqual(right,160)
                self.assertIn(node.get('item'),pieces)
            self.assertEqual([heroic.findtext('TextColor/'+c) for c in ('R','G','B')],['214','178','40'])
            self.assertIn('already included',heroic.findtext('TooltipReference'))
        self.assertEqual(page.findtext('Style_VScroll'),'true')
        self.assertEqual(result.findtext("Screen[@item='InventoryWindow']/Size/CX"),'468')
        self.assertEqual(result.findtext("Screen[@item='InventoryWindow']/Size/CY"),'556')

    def test_scoped_delta_equals_generator_helper_and_retains_unrelated_controls(self):
        raw=SOURCE.read_bytes();expected=ET.fromstring(raw);add_inventory_summary(expected)
        actual=ET.fromstring(inventory_summary_xml(raw));self.assertEqual(canonical(expected),canonical(actual))
        before=ET.fromstring(raw)
        refs={p.text.split(':')[-1] for p in before.find("Page[@item='IW_InvPage']").findall('Pieces')}
        self.assertEqual(len(actual)-len(before),22)
        for node in before:
            name=node.get('item')
            if not name or name in refs or name in ('IW_InvPage','InventoryWindow'):continue
            self.assertEqual(canonical(node),canonical(actual.find(node.tag+"[@item='"+name+"']")),name)

    def test_delta_rejects_reapplication_and_missing_stat(self):
        raw=SOURCE.read_bytes()
        with self.assertRaises(ValueError):inventory_summary_xml(inventory_summary_xml(raw))
        root=ET.fromstring(raw);root.remove(root.find("Label[@item='IW_STRNumber']"))
        with self.assertRaises(ValueError):inventory_summary_xml(ET.tostring(root))

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
        tile=result.find("TileLayoutBox[@item='IW_Stats']");section=result.find("Screen[@item='NCST_Bonuses']")
        self.assertGreater(int(section.findtext('Location/Y')),int(tile.findtext('Location/Y'))+int(tile.findtext('Size/CY')))
        self.assertEqual(len(result.findall("Page[@item='NCPA_Page']")),1)
        self.assertEqual(result.findtext("Label[@item='IW_Class']/EQType"),'10001')

    def test_equipment_semantics_preserved_while_column_moves(self):
        before=ET.fromstring(SOURCE.read_bytes());after=ET.fromstring(ui_xml(SOURCE.read_bytes(),'inventory'))
        for name in ('IW_Stats','IW_Subwindows'):
            b=before.find(".//*[@item='"+name+"']");a=after.find(".//*[@item='"+name+"']")
            self.assertLessEqual({n.text for n in b.findall('Pieces')},{n.text for n in a.findall('Pieces')})
        for node in before:
            name=node.get('item') or ''
            if not name.startswith('InvSlot'):continue
            expected=ET.fromstring(ET.tostring(node))
            x=expected.find('Location/X')
            if x is not None and int(x.text)>=120:x.text=str(int(x.text)+40)
            self.assertEqual(canonical(expected),canonical(after.find(node.tag+"[@item='"+name+"']")),name)


if __name__=='__main__':unittest.main()
