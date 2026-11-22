import unittest
from xml.etree import ElementTree as ET
from client_gameplay_assets import ui_xml


class ItemNoteSkinTest(unittest.TestCase):
    stock = b'''<XML ID="EQInterfaceDefinitionLanguage">
      <Schema xmlns="EverQuestData" xmlns:dt="EverQuestDataTypes" />
      <Page item="IDW_ItemLoreTab"><ScreenID>ItemLoreTab</ScreenID><TabText>Lore</TabText>
      <Pieces>IDW_ItemLore</Pieces></Page>
      <TabBox item="IDW_ItemDescriptionTabBox"><Pages>IDW_ItemDescriptionTab</Pages>
      <Pages>IDW_ItemLoreTab</Pages></TabBox></XML>'''

    def test_notes_controls_are_scoped_to_the_new_tab(self):
        result = ui_xml(self.stock, 'item_notes')
        root = ET.fromstring(result)
        self.assertEqual([p.text for p in root.findall('TabBox/Pages')],
                         ['IDW_ItemDescriptionTab', 'IDW_ItemLoreTab', 'NC_NotePage'])
        pieces = [p.text for p in root.findall("Page[@item='NC_NotePage']/Pieces")]
        self.assertEqual(pieces, ['NC_NoteHelp', 'NC_NoteEdit', 'NC_NoteSave', 'NC_NoteReload', 'NC_NoteStatus'])
        for name in pieces:
            self.assertEqual(root.findtext(f"*[@item='{name}']/ScreenID"), name)
        self.assertEqual(root.findtext("Page[@item='IDW_ItemLoreTab']/Pieces"), 'IDW_ItemLore')
        with self.assertRaises(ValueError):
            ui_xml(result, 'item_notes')

    def test_rejects_unknown_layout(self):
        with self.assertRaises(ValueError):
            ui_xml(self.stock.replace(b'>IDW_ItemLoreTab<', b'>Other<'), 'item_notes')
