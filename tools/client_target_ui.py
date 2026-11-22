"""Add the selected NPC detail line to the stock RoF2 target skin."""
from copy import deepcopy
from xml.etree import ElementTree as ET


def add_target_details(root):
    window = root.find("Screen[@item='TargetWindow']")
    buffs = root.find("Screen[@item='Target_BuffWindow']/TopAnchorOffset")
    template = root.find("Label[@item='Target_AggroNameSecondaryLabel']")
    if (window is None or buffs is None or template is None
            or window.findtext('Size/CY') != '110' or buffs.text != '50'
            or template.findtext('BottomAnchorOffset') != '47'
            or 'Target_BuffWindow' not in [p.text for p in window.findall('Pieces')]
            or root.find("*[@item='NC_TargetDetails']") is not None):
        raise ValueError('Unsupported target window layout')

    label = deepcopy(template)
    label.set('item', 'NC_TargetDetails')
    for tag, value in [('ScreenID', 'NC_TargetDetails'), ('EQType', '10040'),
                       ('TopAnchorOffset', '49'), ('BottomAnchorOffset', '64')]:
        label.find(tag).text = value
    root.insert(list(root).index(window), label)
    ET.SubElement(window, 'Pieces').text = 'NC_TargetDetails'
    buffs.text = '67'
    window.find('Size/CY').text = '127'
