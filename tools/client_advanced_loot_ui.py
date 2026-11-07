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
            value(node, 'NoWrap', 'false' if suffix == 'Help' else 'true')
        value(node, 'TooltipReference', tooltip or text)
        value(screen, 'Pieces', name)

    for key, setting in [('ScreenID', 'NightcapAdvancedLootWnd'), ('Text', 'Advanced Loot'),
                         ('RelativePosition', 'false'), ('DrawTemplate', 'WDT_Def'),
                         ('Style_Titlebar', 'true'), ('Style_Closebox', 'true'),
                         ('Style_Border', 'true'), ('Style_Sizable', 'false'),
                         ('Style_Minimizebox', 'false'), ('Style_Transparent', 'false'),
                         ('Style_VScroll', 'false'), ('Style_HScroll', 'false')]:
        value(screen, key, setting)
    # Fits the supported 640x480 viewport, including the native title bar.
    # Settings, item rules and extra actions replace the list instead of
    # competing with it. The paired controller owns child visibility.
    box(screen, 12, 4, 588, 472)
    control('Label', 'Status', 'Connecting to loot...', 10, 8, 474, 18)
    control('Button', 'Refresh', 'Refresh', 490, 6, 76, 22)
    control('Button', 'Drops', '< Back to loot', 10, 32, 164)
    control('Button', 'All', 'Loot All', 10, 32, 164, tooltip='Collect eligible drops from your kills throughout this zone')
    control('Button', 'Filters', 'Filters', 180, 32, 116)
    control('Button', 'Options', 'Settings', 466, 32, 100)
    control('Label', 'Page', '', 326, 349, 170, 18)
    control('Button', 'Previous', '<', 502, 346, 30)
    control('Button', 'Next', '>', 536, 346, 30)
    control('Editbox', 'SearchText', '', 10, 62, 374, 22, 'Search item names (32 characters)')
    control('Button', 'Search', 'Search', 390, 62, 88, 22)
    control('Button', 'Clear', 'Clear', 484, 62, 82, 22)
    for index in range(8):
        control('Button', f'Icon{index}', '', 10, 90 + index * 32, 32, 32, 'Select this item')
        icon = root[-1]
        for tag, pairs in [('DecalOffset', [('X', 0), ('Y', 0)]),
                           ('DecalSize', [('CX', 32), ('CY', 32)])]:
            node = ET.SubElement(icon, tag)
            for key, number in pairs:
                value(node, key, number)
        control('Button', f'Row{index}', '', 48, 95 + index * 32, 202, 22, 'Select this item')
        control('Label', f'Source{index}', '', 256, 97 + index * 32, 90, 18)
        control('Button', f'Always{index}', '[ ] Always Loot', 352, 95 + index * 32, 106, 22,
                'Always loot this item when allowed; click again for Ask each time')
        control('Button', f'Never{index}', '[ ] Never Loot', 464, 95 + index * 32, 102, 22,
                'Never loot this item; click again for Ask each time')
        control('Button', f'Ignore{index}', 'Remove', 490, 95 + index * 32, 76, 22,
                'Remove this saved rule and return to Ask each time')
    control('Label', 'Empty', 'No items waiting. Loot from your kills appears here.', 22, 126, 532, 22)
    control('Label', 'Selected', '', 10, 346, 306, 20)
    for suffix, title, x, width in [('Take', 'Loot item', 10, 124), ('Rule', 'Item rule...', 140, 132),
                                   ('More', 'More...', 278, 100), ('Inspect', 'Inspect item', 384, 118)]:
        control('Button', suffix, title, x, 372, width, 28)
    control('Label', 'Help', '', 10, 408, 556, 36)

    # Detail panels share this body; only one panel is visible at a time.
    control('Button', 'Back', '< Back', 10, 62, 92)
    control('Label', 'PanelTitle', '', 112, 66, 454, 20)
    choices = [('Ask each time', 'Show this item so you can choose.'),
               ('Always loot', 'Collect this item automatically when allowed.'),
               ('Never loot', 'Leave this item on the corpse.'),
               ('Always need', 'Choose Need when this item is rolled.'),
               ('Always greed', 'Choose Greed when this item is rolled.')]
    for index, (title, description) in enumerate(choices):
        control('Button', f'Filter{index}', title, 16, 102 + index * 44, 160, 28)
        control('Label', f'FilterHelp{index}', description, 188, 107 + index * 44, 370, 22)
    extras = [('Leave', 'Leave on corpse'), ('Find', 'Find corpse'),
              ('Need', 'Need'), ('Greed', 'Greed'), ('Pass', 'Pass'),
              ('Roll', 'Start group roll'), ('FreeGrab', 'Allow anyone to loot'), ('Assign', 'Give to target')]
    for index, (suffix, title) in enumerate(extras):
        control('Button', suffix, title, 16 + (index % 3) * 184,
                114 + (index // 3) * 56, 176, 34)
    settings = [('Advanced loot', 'Use this window to collect loot.'),
                ('Use saved rules', 'Apply your Always and Never choices.'),
                ('Open on new loot', 'Show this window when new loot arrives.'),
                ('Loot everything', 'Auto-collect all eligible personal loot.'),
                ('Split coin', 'Share collected coin with your group.'),
                ('Unfiltered items only', 'Hide items that already have a saved rule.')]
    for index, (title, description) in enumerate(settings):
        control('Button', f'Setting{index}', title, 16, 100 + index * 42, 208, 28)
        control('Label', f'SettingHelp{index}', description, 236, 105 + index * 42, 330, 22)
    root.append(screen)
