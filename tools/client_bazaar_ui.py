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
        box(node, 0, 22, 690, 620)
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

    def control(tag, suffix, text, x, y, width, height=30):
        name = 'NCBZ_' + suffix
        node = ET.SubElement(root, tag, item=name)
        for key, setting in [('ScreenID', name), ('RelativePosition', 'true'), ('Font', 4), ('Text', text), ('TooltipReference', text)]:
            value(node, key, setting)
        box(node, x, y, width, height)
        color = ET.SubElement(node, 'TextColor')
        for channel, number in [('R', 255), ('G', 245), ('B', 225)]:
            value(color, channel, number)
        if tag == 'Button':
            value(node, 'Template', 'BDT_Normal'); value(node, 'Style_Checkbox', 'false')
        elif tag == 'Editbox':
            value(node, 'DrawTemplate', 'WDT_Inner'); value(node, 'Style_Border', 'true')
        else:
            value(node, 'NoWrap', 'false' if suffix in ('Help', 'Status', 'Preview') else 'true')
        value(seller, 'Pieces', name)

    control('Label', 'Help', 'In public East Commonlands: pick up an item, enter a price EACH, then click Post Item.', 12, 8, 640, 46)
    control('Label', 'PriceLabel', 'Platinum EACH:', 12, 62, 144)
    control('Editbox', 'Price', '1', 164, 58, 116, 32)
    control('Button', 'Post', 'Post Item', 294, 58, 132, 32)
    control('Label', 'Preview', 'Your item and total price will appear here before posting.', 12, 100, 640, 48)
    control('Button', 'ConfirmPost', 'Confirm Post', 12, 154, 144, 32)
    control('Button', 'Dismiss', 'Never mind', 168, 154, 132, 32)
    control('Label', 'Balance', 'Proceeds: loading', 12, 198, 420)
    control('Button', 'Collect', 'Collect Proceeds', 466, 194, 174, 32)
    control('Label', 'Heading', 'My Listings - select an item to cancel its remaining stock', 12, 236, 640)
    for i in range(8):
        control('Button', 'Row'+str(i), '', 12, 272+i*32, 628, 30)
    control('Button', 'Previous', '< Previous', 12, 536, 112)
    control('Label', 'Page', '', 136, 538, 166)
    control('Button', 'Next', 'Next >', 308, 536, 86)
    control('Button', 'Cancel', 'Cancel Listing', 406, 536, 142)
    control('Button', 'Refresh', 'Refresh', 560, 536, 90)
    control('Label', 'Status', 'Loading your listings...', 12, 578, 628, 48)
    tabs = ET.SubElement(root, 'TabBox', item='NCBZ_Tabs')
    value(tabs, 'ScreenID', 'NCBZ_Tabs'); value(tabs, 'RelativePosition', 'true')
    box(tabs, 0, 0, 694, 646); stretch(tabs)
    value(tabs, 'DrawTemplate', 'WDT_Def')
    # Native CTabWnd::InsertPage dereferences the tab border without a null check.
    # DrawTemplate does not populate either of these separate frame templates.
    value(tabs, 'TabBorderTemplate', 'FT_DefTabBorder')
    value(tabs, 'PageBorderTemplate', 'FT_DefPageBorder')
    value(tabs, 'Pages', 'Page:NCBZ_SearchPage'); value(tabs, 'Pages', 'Page:NCBZ_SellPage')
    # Existing small saved windows retain scrolling; new windows show the larger text.
    height = screen.find('Size/CY')
    if height is not None:
        height.text = str(max(int(height.text), 672))
    value(screen, 'Pieces', 'NCBZ_Tabs')
