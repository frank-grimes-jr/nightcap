"""Add the shared merchant sell-all control without altering native controls."""
from copy import deepcopy
import xml.etree.ElementTree as ET


def add_sell_all(root):
    screens = root.findall("Screen[@item='MerchantWnd']")
    buttons = root.findall("Button[@item='MW_Sell_Button']")
    if len(screens) != 1 or len(buttons) != 1 or any(
            node.get('item') == 'NC_MerchantSellAll' for node in root):
        raise ValueError('Unsupported or already extended merchant window')
    # The stock action row ends 31 pixels above the bottom. Use its spare footer
    # with the same native skin template and bottom anchors on every merchant.
    stock = buttons[0]
    expected = {'TopAnchorToTop': 'false', 'BottomAnchorToTop': 'false',
                'LeftAnchorToLeft': 'true', 'RightAnchorToLeft': 'true',
                'BottomAnchorOffset': '31'}
    if any(stock.findtext(key) != value for key, value in expected.items()):
        raise ValueError('Unsupported merchant footer layout')
    button = deepcopy(stock)
    button.set('item', 'NC_MerchantSellAll')
    for key, value in {
        'ScreenID': 'NC_MerchantSellAll', 'Text': 'Sell All',
        'LeftAnchorOffset': '10', 'RightAnchorOffset': '110',
        'TopAnchorOffset': '27', 'BottomAnchorOffset': '5',
        'TooltipReference': 'Run #sellall: sell eligible carried loot using the server sell-all rules.',
    }.items():
        child = button.find(key)
        if child is None:
            child = ET.SubElement(button, key)
        child.text = value
    root.append(button)
    ET.SubElement(screens[0], 'Pieces').text = 'NC_MerchantSellAll'
