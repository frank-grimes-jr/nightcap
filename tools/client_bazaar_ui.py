"""Add native Search and Sell / My Listings tabs; preserve every stock control."""
import xml.etree.ElementTree as ET


def add_bazaar_panel(root):
    screens = root.findall("Screen[@item='BazaarSearchWnd']")
    required = ('BZR_QueryButton', 'BZR_ItemList', 'BZR_BuyButton')
    if len(screens) != 1 or any((n.get('item') or '').startswith('NCBZ_') for n in root):
        raise ValueError('Unsupported or already extended Bazaar window')
    screen = screens[0]
    pieces = [n.text for n in screen.findall('Pieces')]
    if any(name not in pieces or root.find("*[@item='"+name+"']") is None for name in required):
        raise ValueError('Missing native search controls')

    def value(node, tag, text):
        ET.SubElement(node, tag).text = str(text)

    def box(node, x, y, width, height):
        for tag, fields in [('Location', [('X', x), ('Y', y)]), ('Size', [('CX', width), ('CY', height)])]:
            child = ET.SubElement(node, tag)
            for name, number in fields:
                value(child, name, number)

    def stretch(node, top=0):
        for tag, text in [('AutoStretch', 'true'), ('TopAnchorToTop', 'true'), ('BottomAnchorToTop', 'false'),
                          ('LeftAnchorToLeft', 'true'), ('RightAnchorToLeft', 'false'),
                          ('TopAnchorOffset', top), ('BottomAnchorOffset', 2),
                          ('LeftAnchorOffset', 2), ('RightAnchorOffset', 2)]:
            value(node, tag, text)

    def page(name, title):
        node = ET.SubElement(root, 'Page', item=name)
        for tag, text in [('ScreenID', name), ('RelativePosition', 'true'), ('DrawTemplate', 'WDT_Def'),
                          ('Style_Transparent', 'false'), ('TabText', title), ('Style_VScroll', 'true'), ('Style_HScroll', 'true')]:
            value(node, tag, text)
        box(node, 0, 22, 690, 548)
        stretch(node, 22)
        for tag in ('TabTextColor', 'TabTextActiveColor'):
            color = ET.SubElement(node, tag)
            for channel, number in [('R', 255), ('G', 240), ('B', 200)]:
                value(color, channel, number)
        return node

    search = page('NCBZ_SearchPage', 'Search')
    for name in pieces:
        value(search, 'Pieces', name)
    for node in screen.findall('Pieces'):
        screen.remove(node)
    seller = page('NCBZ_SellPage', 'Sell / My Listings')

    def control(tag, suffix, text, x, y, width, height=24):
        name = 'NCBZ_' + suffix
        node = ET.SubElement(root, tag, item=name)
        for key, setting in [('ScreenID', name), ('RelativePosition', 'true'), ('Font', 2), ('Text', text), ('TooltipReference', text)]:
            value(node, key, setting)
        box(node, x, y, width, height)
        if tag == 'Button':
            value(node, 'Template', 'BDT_Normal'); value(node, 'Style_Checkbox', 'false')
        elif tag == 'Editbox':
            value(node, 'DrawTemplate', 'WDT_Inner'); value(node, 'Style_Border', 'true')
        else:
            value(node, 'NoWrap', 'false' if suffix in ('Status', 'Preview') else 'true')
        value(seller, 'Pieces', name)

    control('Label', 'Help', 'Pick up an item, enter its price EACH, then click Post Item.', 12, 10, 640)
    control('Label', 'PriceLabel', 'Platinum EACH:', 12, 44, 112)
    control('Editbox', 'Price', '1', 128, 40, 105, 28)
    control('Button', 'Post', 'Post Item', 245, 40, 110, 28)
    control('Label', 'Preview', 'Your exact item and total price will appear here before posting.', 12, 78, 640, 42)
    control('Button', 'ConfirmPost', 'Confirm Post', 12, 124, 120)
    control('Button', 'Dismiss', 'Never mind', 144, 124, 110)
    control('Label', 'Balance', 'Proceeds: loading', 12, 164, 420)
    control('Button', 'Collect', 'Collect Proceeds', 466, 158, 174, 28)
    control('Label', 'Heading', 'My Listings — select an item to cancel its remaining stock', 12, 198, 640)
    for i in range(8):
        control('Button', 'Row'+str(i), '', 12, 226+i*27, 628, 24)
    control('Button', 'Previous', '< Previous', 12, 448, 100)
    control('Label', 'Page', '', 124, 452, 180)
    control('Button', 'Next', 'Next >', 314, 448, 86)
    control('Button', 'Cancel', 'Cancel Listing', 412, 448, 130)
    control('Button', 'Refresh', 'Refresh', 552, 448, 88)
    control('Label', 'Status', 'Loading your listings...', 12, 482, 628, 48)
    tabs = ET.SubElement(root, 'TabBox', item='NCBZ_Tabs')
    value(tabs, 'ScreenID', 'NCBZ_Tabs'); value(tabs, 'RelativePosition', 'true')
    box(tabs, 0, 0, 694, 574); stretch(tabs)
    value(tabs, 'DrawTemplate', 'WDT_Def')
    value(tabs, 'Pages', 'Page:NCBZ_SearchPage'); value(tabs, 'Pages', 'Page:NCBZ_SellPage')
    value(screen, 'Pieces', 'NCBZ_Tabs')
