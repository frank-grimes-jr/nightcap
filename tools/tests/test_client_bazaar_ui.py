import os,unittest,xml.etree.ElementTree as ET
from pathlib import Path
from client_gameplay_assets import ui_xml
from client_bazaar_ui import add_bazaar_panel

STOCK=b'<XML><Button item="BZR_QueryButton"><ScreenID>BZR_QueryButton</ScreenID><Text>Search</Text></Button><Listbox item="BZR_ItemList"><ScreenID>BZR_ItemList</ScreenID></Listbox><Button item="BZR_BuyButton"><ScreenID>BZR_BuyButton</ScreenID></Button><Screen item="BazaarSearchWnd"><Size><CX>700</CX><CY>600</CY></Size><Pieces>BZR_QueryButton</Pieces><Pieces>BZR_ItemList</Pieces><Pieces>BZR_BuyButton</Pieces></Screen></XML>'
class BazaarUI(unittest.TestCase):
 def test_panel_preserves_native_controls_and_uses_separate_owned_rows(self):
  root=ET.fromstring(STOCK);before=[ET.tostring(x) for x in root if x.tag!='Screen'];add_bazaar_panel(root)
  self.assertEqual(before,[ET.tostring(x) for x in root if (x.get('item') or '').startswith('BZR_')])
  self.assertIsNotNone(root.find("Editbox[@item='NCBZ_Price']"));self.assertIsNone(root.find('.//MaxChars'))
  for name in ('Post','ConfirmPost','Cancel','Collect','Refresh','Previous','Next','Dismiss'):
   self.assertIsNotNone(root.find("Button[@item='NCBZ_"+name+"']"))
  self.assertEqual(len([x for x in root if (x.get('item') or '').startswith('NCBZ_Row')]),8)
  for page in root.findall('Page'):
   for piece in page.findall('Pieces'):self.assertIsNotNone(root.find("*[@item='"+piece.text+"']"))
 def test_pinned_native_layout(self):
  path=os.environ.get('NIGHTCAP_BAZAAR_XML')
  if not path:self.skipTest('Set NIGHTCAP_BAZAAR_XML to the read-only stock Bazaar XML')
  raw=Path(path).read_bytes();before=ET.fromstring(raw);after=ET.fromstring(ui_xml(raw,'bazaar'))
  def normalized(node):
   node=ET.fromstring(ET.tostring(node))
   for n in node.iter():
    if n.text and not n.text.strip():n.text=None
    n.tail=None
   return ET.tostring(node)
  for old in before:
   if old.tag=='Screen':continue
   name=old.get('item')
   if name:self.assertEqual(normalized(old),normalized(after.find("*[@item='"+name+"']")),name)
  stock=[n.text for n in before.find("Screen[@item='BazaarSearchWnd']").findall('Pieces')]
  self.assertEqual(stock,[n.text for n in after.find("Page[@item='NCBZ_SearchPage']").findall('Pieces')])
  self.assertEqual([n.text for n in after.find("TabBox[@item='NCBZ_Tabs']").findall('Pages')],['Page:NCBZ_SearchPage','Page:NCBZ_SellPage'])
  for page in after.findall('Page'):
   self.assertEqual(page.findtext('Style_VScroll'),'true');self.assertEqual(page.findtext('Style_HScroll'),'true')
   for piece in page.findall('Pieces'):self.assertIsNotNone(after.find("*[@item='"+piece.text+"']"))
 def test_duplicate_or_wrong_screen_rejected(self):
  with self.assertRaises(ValueError):add_bazaar_panel(ET.fromstring('<XML/>'))
  root=ET.fromstring(STOCK);add_bazaar_panel(root)
  with self.assertRaises(ValueError):add_bazaar_panel(root)
if __name__=='__main__':unittest.main()
