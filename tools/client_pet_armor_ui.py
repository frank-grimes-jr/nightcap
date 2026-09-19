"""Add an eight-slot pet armor page to the existing inventory tabs."""
import xml.etree.ElementTree as ET


def add_pet_page(root):
    tabs = root.findall("TabBox[@item='IW_Subwindows']")
    if len(tabs) != 1 or root.find("Page[@item='NCPA_Page']") is not None:
        raise ValueError('Unsupported inventory tabs')
    page = ET.Element('Page', item='NCPA_Page')
    def value(node, tag, text):
        ET.SubElement(node, tag).text = str(text)
    def box(node, x, y, width, height):
        location = ET.SubElement(node, 'Location')
        value(location, 'X', x); value(location, 'Y', y)
        size = ET.SubElement(node, 'Size')
        value(size, 'CX', width); value(size, 'CY', height)
    def color(node, tag, blue=255):
        target = ET.SubElement(node, tag)
        for name, number in [('R',255),('G',255),('B',blue)]:
            value(target, name, number)
    def control(tag, name, text, x, y, width, height, eqtype=None):
        node = ET.Element(tag, item=name)
        value(node, 'ScreenID', name)
        value(node, 'RelativePosition', 'true')
        value(node, 'Font', 2)
        box(node, x, y, width, height)
        value(node, 'Text', text)
        color(node, 'TextColor')
        if eqtype is not None:
            value(node, 'EQType', eqtype)
        if tag == 'Button':
            value(node, 'Template', 'BDT_Normal')
            value(node, 'Style_Checkbox', 'false')
            value(node, 'TooltipReference', text)
        else:
            value(node, 'NoWrap', 'true')
        root.append(node)
        value(page, 'Pieces', name)
    value(page, 'ScreenID', 'NCPA_Page')
    value(page, 'RelativePosition', 'true')
    value(page, 'Style_VScroll', 'false')
    value(page, 'Style_HScroll', 'false')
    value(page, 'Style_Transparent', 'false')
    value(page, 'DrawTemplate', 'WDT_Def')
    value(page, 'TabText', 'Pet Armor')
    color(page, 'TabTextColor'); color(page, 'TabTextActiveColor', 0)
    box(page, 0, 22, 388, 401)
    control('Button','NCPA_Previous','<',6,8,24,22)
    control('Label','NCPA_Selected','Pet armor loading',36,12,302,18,10020)
    control('Button','NCPA_Next','>',350,8,24,22)
    control('Label','NCPA_Help','Equip from cursor. Remove to empty cursor.',6,38,370,18)
    for index, name in enumerate(('Head','Chest','Arms','Wrist','Hands','Legs','Feet','Waist')):
        y = 66 + index * 33
        control('Label',f'NCPA_Item{index}',f'{name}: Empty',6,y+4,205,20,10021+index)
        for action, x, width in [('Equip',214,47),('Remove',264,56),('Inspect',323,55)]:
            control('Button',f'NCPA_{action}{index}',action,x,y,width,25)
    control('Button','NCPA_Refresh','Refresh',6,341,65,24)
    control('Label','NCPA_Notice','8 armor slots per pet. Change gear out of combat.',6,372,373,18)
    root.append(page)
    value(tabs[0], 'Pages', 'Page:NCPA_Page')
