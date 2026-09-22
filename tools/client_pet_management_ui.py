"""Extend Pet Info with a complete roster and server-routed command controls."""
import xml.etree.ElementTree as ET

COMMANDS = ('Attack', 'Follow', 'Guard', 'Taunt', 'Sit / Stand', 'Stop',
            'Regroup', 'Back off', 'Hold', 'Greater hold', 'Focus', 'Spell hold',
            'Health', 'Dismiss')


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

    def control(tag, name, text, x, y, width, height, eqtype=None):
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
            value(node, 'TooltipReference', text or 'Select this pet; click again for All pets')
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
    value(screen, 'MinHSize', 330)
    value(screen, 'MinVSize', 458)
    box(screen, 50, 160, 330, 458)
    for index in range(3):
        control('Button', f'NCPM_Pet{index}', '', 6, 6+index*28, 310, 26)
        control('Label', f'NCPM_Pet{index}Name', 'Pets loading', 12, 11+index*28, 298, 20, 10031+index)
    control('Label', 'NCPM_Scope', 'Commands: All pets', 8, 95, 228, 20, 10030)
    control('Button', 'NCPM_All', 'All pets', 244, 90, 72, 26)
    for name, bounds in [('PIW_PetHPGauge', (6, 122, 152, 26)),
                         ('PIW_PetTargetHPGauge', (6, 153, 152, 28)),
                         ('PIW_BuffWindow', (172, 122, 144, 280))]:
        node = next((node for node in root if node.get('item') == name), None)
        if node is None:
            raise ValueError('Missing native pet status widget')
        box(node, *bounds)
    for index, title in enumerate(COMMANDS):
        control('Button', f'NCPM_Command{index}', title, 6+(index%2)*78, 188+(index//2)*30, 74, 27)
    control('Label', 'NCPM_Help', 'Select a name or pet. Clear target for All pets.', 6, 409, 312, 20)
