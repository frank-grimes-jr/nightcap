import unittest
import xml.etree.ElementTree as ET
from client_gameplay_assets import ui_xml


STOCK = b'''<XML><Schema xmlns="EverQuestData"/>
<Button item="MW_Sell_Button"><ScreenID>MW_Sell_Button</ScreenID>
<RelativePosition>true</RelativePosition><AutoStretch>true</AutoStretch>
<TopAnchorToTop>false</TopAnchorToTop><BottomAnchorToTop>false</BottomAnchorToTop>
<LeftAnchorToLeft>true</LeftAnchorToLeft><RightAnchorToLeft>true</RightAnchorToLeft>
<LeftAnchorOffset>10</LeftAnchorOffset><RightAnchorOffset>74</RightAnchorOffset>
<TopAnchorOffset>69</TopAnchorOffset><BottomAnchorOffset>31</BottomAnchorOffset>
<Text>Sell</Text><Template>BDT_Normal</Template></Button>
<Screen item="MerchantWnd"><Pieces>MW_Sell_Button</Pieces></Screen></XML>'''


class MerchantUI(unittest.TestCase):
    def test_button_is_shared_by_all_merchants_and_preserves_stock_sell(self):
        result = ui_xml(STOCK, 'merchant')
        root = ET.fromstring(result)
        fields = lambda tree: [(node.tag, node.attrib, (node.text or '').strip())
                               for node in tree.find("Button[@item='MW_Sell_Button']").iter()]
        self.assertEqual(fields(root), fields(ET.fromstring(STOCK)))
        button = root.find("Button[@item='NC_MerchantSellAll']")
        self.assertEqual(button.findtext('Text'), 'Sell All')
        self.assertEqual(button.findtext('ScreenID'), 'NC_MerchantSellAll')
        self.assertEqual(button.findtext('TopAnchorToTop'), 'false')
        self.assertLess(int(button.findtext('TopAnchorOffset')), 31)
        self.assertEqual(root.find("Screen[@item='MerchantWnd']").findall('Pieces')[-1].text,
                         'NC_MerchantSellAll')
        self.assertIn(b'<Schema xmlns="EverQuestData" xmlns:dt="EverQuestDataTypes"', result)
        self.assertNotIn(b'ns0:', result)

    def test_rejects_unsupported_or_duplicate_controls(self):
        for raw in (b'<XML/>', STOCK.replace(b'MW_Sell_Button', b'Missing'),
                    ui_xml(STOCK, 'merchant')):
            with self.subTest(raw=raw[:60]), self.assertRaises(ValueError):
                ui_xml(raw, 'merchant')


if __name__ == '__main__':
    unittest.main()
