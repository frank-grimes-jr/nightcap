"""Add Craft All/Stop to the native recipe browser, preserving stock controls."""
import copy
import xml.etree.ElementTree as ET


def add_crafting(root):
    def one(tag, name):
        rows = root.findall(f"{tag}[@item='{name}']")
        if len(rows) != 1:
            raise ValueError('Missing or duplicate tradeskill control: ' + name)
        return rows[0]

    craft = one('Button', 'COMBW_CombineButton')
    auto = one('Button', 'COMBW_AutoInvButton')
    area = one('Screen', 'COMBW_CombineArea')
    flags = one('Screen', 'COMBW_FlagsArea')
    window = one('Screen', 'TradeskillWnd')
    if craft.findtext('ScreenID') != 'CombineButton' or auto.findtext('ScreenID') != 'AutoInvButton':
        raise ValueError('Unsupported native tradeskill controls')
    if any(root.findall(f"Button[@item='{name}']") for name in ('NC_CraftAll', 'NC_CraftStop')):
        raise ValueError('Crafting controls already exist')

    def set_value(node, tag, value):
        child = node.find(tag)
        if child is None:
            child = ET.SubElement(node, tag)
        child.text = str(value)

    for name, title, hint, y in (
        ('NC_CraftAll', 'Craft All', 'Repeat this recipe from your inventory stacks until materials run out. Failed attempts still use materials.', 30),
        ('NC_CraftStop', 'Stop', 'Stop after the current attempt. Your materials and completed items are kept.', 60),
    ):
        button = copy.deepcopy(craft)
        button.set('item', name)
        for tag, value in (('ScreenID', name), ('Text', title), ('TooltipReference', hint),
                           ('TopAnchorOffset', y), ('BottomAnchorOffset', y + 26)):
            set_value(button, tag, value)
        root.append(button)
        ET.SubElement(area, 'Pieces').text = name
    set_value(craft, 'Text', 'Craft One')
    set_value(craft, 'BottomAnchorOffset', 26)
    set_value(craft, 'TooltipReference', 'Make one attempt using materials from your inventory stacks.')
    for tag, value in (('TopAnchorToTop', 'true'), ('BottomAnchorToTop', 'true'),
                       ('TopAnchorOffset', 90), ('BottomAnchorOffset', 116)):
        set_value(auto, tag, value)
    set_value(area, 'BottomAnchorOffset', 454)
    set_value(flags, 'TopAnchorOffset', 458)
    size = window.find('Size/CY')
    if size is None:
        raise ValueError('Missing tradeskill window size')
    size.text = str(int(size.text) + 66)
