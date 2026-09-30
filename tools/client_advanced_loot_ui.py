"""Add a native advanced-loot screen to an already included SIDL document.

The Pet Info file is always loaded by EQUI.xml, so this additional top-level
screen needs no replacement of the client's complete EQUI include inventory.
Its controls share only the NCAL_ namespace with the paired proxy.
"""
import xml.etree.ElementTree as ET


def add_advanced_loot(root):
    if any((node.get('item') or '').startswith('NCAL_') or
           node.get('item') == 'NightcapAdvancedLootWnd' for node in root):
        raise ValueError('Advanced loot screen is already present')

    screen = ET.Element('Screen', item='NightcapAdvancedLootWnd')

    def value(node, tag, text):
        ET.SubElement(node, tag).text = str(text)

    def box(node, x, y, width, height):
        for tag, pairs in [('Location', [('X', x), ('Y', y)]), ('Size', [('CX', width), ('CY', height)])]:
            parent = ET.SubElement(node, tag)
            for name, number in pairs:
                value(parent, name, number)

    def control(tag, suffix, text, x, y, width, height=24, tooltip=None):
        name = 'NCAL_' + suffix
        node = ET.SubElement(root, tag, item=name)
        for key, setting in [('ScreenID', name), ('RelativePosition', 'true'), ('Font', 2), ('Text', text)]:
            value(node, key, setting)
        box(node, x, y, width, height)
        color = ET.SubElement(node, 'TextColor')
        for channel, number in [('R', 240), ('G', 230), ('B', 200)]:
            value(color, channel, number)
        if tag == 'Button':
            value(node, 'Template', 'BDT_Normal')
            value(node, 'Style_Checkbox', 'false')
        elif tag == 'Editbox':
            value(node, 'DrawTemplate', 'WDT_Inner')
            value(node, 'Style_Border', 'true')
        else:
            value(node, 'NoWrap', 'true')
        value(node, 'TooltipReference', tooltip or text)
        value(screen, 'Pieces', name)

    for key, setting in [('ScreenID', 'NightcapAdvancedLootWnd'), ('Text', 'Advanced Loot'),
                         ('RelativePosition', 'false'), ('DrawTemplate', 'WDT_Def'),
                         ('Style_Titlebar', 'true'), ('Style_Closebox', 'true'),
                         ('Style_Border', 'true'), ('Style_Sizable', 'false'),
                         ('Style_Minimizebox', 'false'), ('Style_Transparent', 'false'),
                         ('Style_VScroll', 'false'), ('Style_HScroll', 'false')]:
        value(screen, key, setting)
    box(screen, 40, 40, 720, 578)
    control('Label', 'Status', 'Connecting to advanced loot...', 8, 8, 692, 20)
    control('Button', 'Drops', 'Loot', 8, 32, 58)
    control('Button', 'Filters', 'Filters', 70, 32, 62)
    control('Editbox', 'SearchText', '', 140, 32, 228, tooltip='Search item names, up to 32 characters')
    control('Button', 'Search', 'Search', 372, 32, 64)
    control('Button', 'Clear', 'Clear', 440, 32, 54)
    control('Button', 'Previous', '<', 510, 32, 30)
    control('Button', 'Next', '>', 544, 32, 30)
    control('Button', 'Refresh', 'Refresh', 578, 32, 122)
    for index in range(8):
        control('Button', f'Row{index}', '', 8, 66 + index * 29, 374, 26, 'Select this item')
        control('Label', f'Source{index}', '', 390, 71 + index * 29, 310, 20)
    control('Label', 'Selected', 'Select an item to loot, share or change its saved filter.', 8, 306, 692, 20)
    for suffix, title, x, width in [('Take', 'Loot', 8, 114), ('Leave', 'Leave', 126, 88),
                                   ('Inspect', 'Inspect', 218, 88), ('Find', 'Find corpse', 310, 122),
                                   ('All', 'Loot all personal', 436, 264)]:
        control('Button', suffix, title, x, 332, width, 26)
    shared = [('Need', 'Need'), ('Greed', 'Greed'), ('Pass', 'Pass'),
              ('Roll', 'Ask to roll'), ('FreeGrab', 'Free grab'), ('Assign', 'Assign target')]
    for index, (suffix, title) in enumerate(shared):
        tooltip = 'Master looter: assign to your currently targeted group or raid member' if suffix == 'Assign' else title
        control('Button', suffix, title, 8 + index * 116, 364, 112, 26, tooltip)
    for index, title in enumerate(['Ask', 'Always loot', 'Never', 'Always need', 'Always greed']):
        control('Button', f'Filter{index}', title, 8 + index * 139, 402, 135, 26,
                'Save this preference for this item on this character: ' + title)
    settings = ['Advanced loot', 'Apply filters', 'Auto show', 'Auto loot all', 'Split coin', 'New items only']
    for index, title in enumerate(settings):
        control('Button', f'Setting{index}', '[ ] ' + title, 8 + (index % 3) * 232,
                442 + (index // 3) * 30, 228, 26)
    control('Label', 'Help', 'Never leaves items on the corpse. Shared loot keeps the group\'s loot permissions.',
            8, 516, 692, 22)
    root.append(screen)
