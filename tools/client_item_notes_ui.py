"""Add a private Notes tab while keeping the native item description and lore pages."""
from copy import deepcopy
from xml.etree import ElementTree as ET


def add_item_notes(root):
    tabs = root.find("TabBox[@item='IDW_ItemDescriptionTabBox']")
    lore = root.find("Page[@item='IDW_ItemLoreTab']")
    if (tabs is None or lore is None or [p.text for p in tabs.findall('Pages')] !=
            ['IDW_ItemDescriptionTab', 'IDW_ItemLoreTab'] or any(
                (node.get('item') or '').startswith('NC_Note') for node in root)):
        raise ValueError('Unsupported item inspection layout')
    page = deepcopy(lore)
    page.set('item', 'NC_NotePage')
    page.find('ScreenID').text = 'NC_NotePage'
    page.find('TabText').text = 'Notes'
    for piece in page.findall('Pieces'):
        page.remove(piece)
    index = list(root).index(tabs)
    for tag, suffix, text, x, y, width, height in [
        ('Label', 'Help', 'Private to this Windows account. Save a blank note to remove it.', 7, 5, 330, 32),
        ('Editbox', 'Edit', '', 7, 42, 325, 25),
        ('Button', 'Save', 'Save', 7, 76, 80, 26),
        ('Button', 'Reload', 'Reload', 94, 76, 80, 26),
        ('Label', 'Status', '', 7, 110, 330, 36),
    ]:
        name = 'NC_Note' + suffix
        node = ET.Element(tag, item=name)
        for key, value in [('ScreenID', name), ('RelativePosition', 'true'), ('Font', '3'), ('Text', text)]:
            ET.SubElement(node, key).text = value
        for parent, fields in [('Location', [('X', x), ('Y', y)]), ('Size', [('CX', width), ('CY', height)])]:
            child = ET.SubElement(node, parent)
            for key, value in fields:
                ET.SubElement(child, key).text = str(value)
        color = ET.SubElement(node, 'TextColor')
        for channel in ('R', 'G', 'B'):
            ET.SubElement(color, channel).text = '255'
        if tag == 'Editbox':
            ET.SubElement(node, 'DrawTemplate').text = 'WDT_Inner'
            ET.SubElement(node, 'Style_Border').text = 'true'
        elif tag == 'Button':
            ET.SubElement(node, 'Template').text = 'BDT_Normal'
            ET.SubElement(node, 'Style_Checkbox').text = 'false'
        else:
            ET.SubElement(node, 'NoWrap').text = 'false'
        root.insert(index, node)
        index += 1
        ET.SubElement(page, 'Pieces').text = name
    root.insert(index, page)
    ET.SubElement(tabs, 'Pages').text = 'NC_NotePage'
