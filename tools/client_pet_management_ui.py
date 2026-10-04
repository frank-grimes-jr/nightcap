"""Extend Pet Info with a complete roster and server-routed command controls."""
import xml.etree.ElementTree as ET

COMMANDS = ('Attack', 'Follow', 'Guard', 'Taunt', 'Sit / Stand', 'Stop',
            'Regroup', 'Back off', 'Hold', 'Greater hold', 'Focus', 'Spell hold',
            'Health', 'Dismiss')
COMMAND_LABELS = ('Attack', 'Follow', 'Guard', 'Taunt', 'Sit/Up', 'Stop',
                  'Group', 'Back', 'Hold', 'G.Hold', 'Focus', 'S.Hold',
                  'Health', 'Remove')


def add_pet_management(root):
    screen = root.find("Screen[@item='PetInfoWindow']")
    if screen is None or root.find("Button[@item='NCPM_All']") is not None:
        raise ValueError('Unsupported pet window')

    def value(node, tag, text):
        child = node.find(tag)
        if child is None:
            child = ET.SubElement(node, tag)
        child.text = str(text)

    def box(node, x, y, width, height):
        for tag, fields in [('Location', [('X', x), ('Y', y)]), ('Size', [('CX', width), ('CY', height)])]:
            parent = node.find(tag)
            if parent is None:
                parent = ET.SubElement(node, tag)
            for name, number in fields:
                value(parent, name, number)

    def control(tag, name, text, x, y, width, height, eqtype=None, tooltip=None):
        node = ET.SubElement(root, tag, item=name)
        for key, setting in [('ScreenID', name), ('RelativePosition', 'true'), ('Font', 2), ('Text', text)]:
            value(node, key, setting)
        box(node, x, y, width, height)
        color = ET.SubElement(node, 'TextColor')
        for name_, number in [('R', 240), ('G', 230), ('B', 200)]:
            value(color, name_, number)
        if eqtype is not None:
            value(node, 'EQType', eqtype)
        if tag == 'Button':
            value(node, 'Template', 'BDT_Normal')
            value(node, 'Style_Checkbox', 'false')
            value(node, 'TooltipReference', tooltip or text or 'Select this pet; click again for All pets')
        else:
            value(node, 'NoWrap', 'true')
        ET.SubElement(screen, 'Pieces').text = name

    # Native pet hotbuttons retain pointers to the original configurable slots.
    # Keep those controls outside the clipped window and bridge their notifications;
    # deleting them would also disable existing pet hotbuttons.
    for index in range(14):
        name = f'PIW_Pet{index}_Button'
        button = root.find(f"Button[@item='{name}']")
        if button is None:
            raise ValueError('Missing native pet command button')
        box(button, -10000, -10000, 1, 1)
    value(screen, 'Text', 'Pets')
    value(screen, 'MinHSize', 350)
    value(screen, 'MinVSize', 350)
    box(screen, 50, 160, 350, 350)
    for index in range(3):
        control('Button', f'NCPM_Pet{index}', '', 6, 6+index*28, 338, 26)
        control('Label', f'NCPM_Pet{index}Name', 'Pets loading', 12, 11+index*28, 326, 20, 10031+index)
    control('Label', 'NCPM_Scope', 'Commands: All pets', 8, 95, 230, 20, 10030)
    control('Button', 'NCPM_All', 'All pets', 244, 90, 96, 26,
            tooltip='Command all pets. Clearing your target also selects all pets.')
    for name, bounds in [('PIW_PetHPGauge', (6, 122, 152, 26)),
                         ('PIW_PetTargetHPGauge', (6, 153, 152, 28)),
                         ('PIW_BuffWindow', (180, 122, 164, 200))]:
        node = next((node for node in root if node.get('item') == name), None)
        if node is None:
            raise ValueError('Missing native pet status widget')
        box(node, *bounds)
        if name == 'PIW_BuffWindow':
            # RoF2 uses these stock AutoStretch anchors instead of Location/Size.
            # Keep buffs below the full-width roster and beside the command grid;
            # resizing should expand only the buff area into the available space.
            for tag, setting in [('AutoStretch', 'true'),
                                 ('LeftAnchorOffset', 180), ('TopAnchorOffset', 122),
                                 ('RightAnchorOffset', 6), ('BottomAnchorOffset', 4),
                                 ('LeftAnchorToLeft', 'true'), ('TopAnchorToTop', 'true'),
                                 ('RightAnchorToLeft', 'false'), ('BottomAnchorToTop', 'false')]:
                value(node, tag, setting)
    for index, title in enumerate(COMMANDS):
        label = COMMAND_LABELS[index]
        control('Button', f'NCPM_Command{index}', label,
                6+(index%3)*56, 184+(index//3)*28, 54, 25,
                tooltip=title)
