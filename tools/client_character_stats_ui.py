"""Extend the existing Stats page; stage outside the read-only client reference."""
import xml.etree.ElementTree as ET
from copy import deepcopy
import re

PAIRS=['Shielding','SpellShield','DamageShielding','DoTShielding','DamageShieldMitigation',
       'Avoidance','Accuracy','StunResist','StrikeThrough','HealAmount','SpellDamage','Clairvoyance','CombatEffects']
SHIELD_BLOCK_TIP='Total shield-block chance, including equipped augment bonuses. Requires a shield; facing and attack counters still apply. Only the strongest augment shield-block bonus applies.'


def add_inventory_heroics(root):
    """Expose RoF2's native heroic labels in the main Inventory stat column."""
    page=root.find("Page[@item='IW_InvPage']")
    if page is None:raise ValueError('Missing Inventory page')
    stats=[('STR','Strength'),('STA','Stamina'),('AGI','Agility'),
           ('DEX','Dexterity'),('WIS','Wisdom'),('INT','Intelligence'),('CHA','Charisma')]
    # Check the complete input before mutation; the shipped skin owns this layout.
    for short,full in stats:
        if root.find("Label[@item='IW_Heroic"+full+"']") is not None:
            raise ValueError('Inventory heroic labels already present')
        total=root.find("Label[@item='IW_"+short+"Number']")
        native=root.find("Label[@item='IWS_Heroic"+full+"']")
        if total is None or native is None:raise ValueError('Missing native stat: '+short)
        if int(total.findtext('Location/X'))+int(total.findtext('Size/CX'))>81:
            raise ValueError('Unsupported Inventory stat column: '+short)
    for short,full in stats:
        total=root.find("Label[@item='IW_"+short+"Number']")
        native=root.find("Label[@item='IWS_Heroic"+full+"']")
        for suffix,x,width in [('Plus',81,8),('',89,31)]:
            node=deepcopy(native)
            name='IW_Heroic'+full+suffix
            node.set('item',name)
            screen=node.find('ScreenID')
            if screen is None:screen=ET.SubElement(node,'ScreenID')
            screen.text=name
            node.find('Location/X').text=str(x)
            node.find('Location/Y').text=total.findtext('Location/Y')
            node.find('Size/CX').text=str(width)
            if suffix:
                node.remove(node.find('EQType'))
                node.find('Text').text='+'
            tip=ET.SubElement(node,'TooltipReference')
            tip.text='Heroic '+full+' from usable equipped items and augments. Included in the total to the left; also raises the stat cap.'
            root.append(node)
            ET.SubElement(page,'Pieces').text=name


def inventory_heroics_xml(raw):
    """Add labels to published XML while preserving every existing source byte."""
    root=ET.fromstring(raw)
    add_inventory_heroics(root)
    labels=[n for n in root.findall('Label') if n.get('item','').startswith('IW_Heroic')]
    if len(labels)!=14:raise ValueError('Unexpected heroic label inventory')
    pages=list(re.finditer(rb'<Page\s+item="IW_InvPage">.*?</Page>',raw,re.DOTALL))
    if len(pages)!=1 or raw.count(b'</XML>')!=1:raise ValueError('Unsupported XML layout')
    pieces=b''.join(b'\n\t\t<Pieces>'+n.get('item').encode('ascii')+b'</Pieces>' for n in labels)
    offset=pages[0].end()-len(b'</Page>')
    result=raw[:offset]+pieces+b'\n\t'+raw[offset:]
    rendered=[]
    for node in labels:
        node.tail=None
        ET.indent(node,space='\t')
        rendered.append(ET.tostring(node,encoding='utf-8'))
    result=result.replace(b'</XML>',b'\n'+b'\n'.join(rendered)+b'\n</XML>')
    ET.fromstring(result)
    return result


def show_total_shield_block(root):
    """Keep a single total; remove the redundant augment-only breakdown row."""
    tile=root.find("TileLayoutBox[@item='IW_Stats']")
    section=root.find("Screen[@item='NCST_Bonuses']")
    if tile is None or section is None:raise ValueError('Missing Stats layout')
    for node in list(root):
        if node.get('item') in ('NCST_Row1','NCST_Name1','NCST_Value1'):root.remove(node)
    for piece in tile.findall('Pieces'):
        if piece.text=='Screen:NCST_Row1':tile.remove(piece)
    for name in ('NCST_Name0','NCST_Value0'):
        root.find("Label[@item='"+name+"']/TooltipReference").text=SHIELD_BLOCK_TIP
    root.find("Label[@item='NCST_Name0']/Text").text='Shield Block'
    height=max(400,((len(tile.findall('Pieces'))+1)//2)*16+2)
    tile.find('Size/CY').text=str(height)
    section.find('Location/Y').text=str(height+20)


def match_character_stats_font(root):
    """Use the stock stat font, including its inherited default when unspecified."""
    reference=root.find("Label[@item='IWS_Shielding']")
    if reference is None:raise ValueError('Missing native stat label')
    font=reference.findtext('Font')
    height=reference.findtext('Size/CY')
    for node in root.findall('Label'):
        if not (node.get('item') or '').startswith('NCST_'):continue
        current=node.find('Font')
        if current is not None:node.remove(current)
        if font is not None:ET.SubElement(node,'Font').text=font
        node.find('Size/CY').text=height
    for index in (0,2):
        root.find("Label[@item='NCST_Value"+str(index)+"']/Size/CX").text='75'


def add_character_stats(root):
    page=root.find("Page[@item='IW_StatPage']")
    tile=root.find("TileLayoutBox[@item='IW_Stats']")
    if page is None or tile is None or root.find("Screen[@item='NCST_Bonuses']") is not None:
        raise ValueError('Unsupported or already updated Stats page')
    add_inventory_heroics(root)
    def put(node,tag,text):
        child=node.find(tag)
        if child is None:child=ET.SubElement(node,tag)
        child.text=str(text)
    # Keep native column order/size. A separate section below the native tile
    # creates an explicit scroll extent, including with a saved 500px window.
    put(page,'Style_VScroll','true')
    put(page,'Style_HScroll','true')
    put(tile,'AutoStretch','false')
    for tag in ('LeftAnchorOffset','RightAnchorOffset','TopAnchorOffset','BottomAnchorOffset','BottomAnchorToTop','RightAnchorToLeft'):
        child=tile.find(tag)
        if child is not None:tile.remove(child)
    location=ET.SubElement(tile,'Location');put(location,'X',5);put(location,'Y',5)
    native_height=max(400,((len(tile.findall('Pieces'))+1)//2)*16+2)
    size=ET.SubElement(tile,'Size');put(size,'CX',365);put(size,'CY',native_height)
    for index,name in enumerate(PAIRS):
        current=root.find("Label[@item='IWS_Current"+name+"']")
        maximum=root.find("Label[@item='IWS_Max"+name+"']")
        if current is None:raise ValueError('Missing native stat: '+name)
        if maximum is None:
            put(current,'EQType',10300+index)
        else:
            put(current,'EQType',10100+7+2*index);put(maximum,'EQType',10100+8+2*index)
        put(current,'Text','--')
        if maximum is not None:put(maximum,'Text','--')
    section=ET.SubElement(root,'Screen',item='NCST_Bonuses')
    for tag,text in [('ScreenID','NCST_Bonuses'),('RelativePosition','true'),('Style_Transparent','true'),('Style_VScroll','false')]:put(section,tag,text)
    loc=ET.SubElement(section,'Location');put(loc,'X',5);put(loc,'Y',native_height+20)
    size=ET.SubElement(section,'Size');put(size,'CX',365);put(size,'CY',180)
    def label(name,text,x,y,width,eqtype=None,tooltip=None,parent=None):
        node=ET.SubElement(root,'Label',item=name)
        for tag,value in [('ScreenID',name),('RelativePosition','true'),('Font',2),('Text',text),('NoWrap','true')]:put(node,tag,value)
        loc=ET.SubElement(node,'Location');put(loc,'X',x);put(loc,'Y',y)
        size=ET.SubElement(node,'Size');put(size,'CX',width);put(size,'CY',16)
        color=ET.SubElement(node,'TextColor')
        for c in ('R','G','B'):put(color,c,255)
        if eqtype is not None:put(node,'EQType',eqtype)
        if tooltip:put(node,'TooltipReference',tooltip)
        ET.SubElement(section if parent is None else parent,'Pieces').text=name
    label('NCST_Title','Item focus and utility',0,0,360)
    rows=[(0,'Shield Block',SHIELD_BLOCK_TIP),
          (2,'Dodge modifier','Relative modifier to Dodge skill, not a flat chance to avoid all attacks.'),
          (3,'Item spell haste*','Best worn item focus potential before spell limits. Buffs/AAs and cast/level limits affect an actual cast.'),
          (4,'Mana preservation*','Best worn item focus potential before spell limits; copies do not add. Actual reduction depends on the spell and active rules.'),
          (5,'Worn Faerune','A usable equipped item/augment supplies Faerune. Copies do not multiply its utility effects.')]
    for i,text,tip in rows:
        if i<3:
            row=ET.SubElement(root,'Screen',item='NCST_Row'+str(i))
            put(row,'RelativePosition','true');put(row,'Style_Transparent','true')
            size=ET.SubElement(row,'Size');put(size,'CX',175);put(size,'CY',14)
            label('NCST_Name'+str(i),text,0,0,105,tooltip=tip,parent=row)
            label('NCST_Value'+str(i),'--',105,0,70,10200+i,tip,parent=row)
            after='Screen:IWS_ShieldingScreen' if i<2 else 'Screen:IWS_AvoidanceScreen'
            previous=next(n for n in tile.findall('Pieces') if n.text==after)
            piece=ET.Element('Pieces');piece.text='Screen:NCST_Row'+str(i)
            tile.insert(list(tile).index(previous)+1,piece)
        else:
            label('NCST_Name'+str(i),text,0,22+(i-3)*19,150,tooltip=tip)
            label('NCST_Value'+str(i),'--',154,22+(i-3)*19,205,10200+i,tip)
    native_height=max(400,((len(tile.findall('Pieces'))+1)//2)*16+2)
    tile.find('Size/CY').text=str(native_height)
    section.find('Location/Y').text=str(native_height+20)
    section.find('Size/CY').text='125'
    label('NCST_Status','Updating server totals...',0,84,360,10400)
    label('NCST_FocusHelp','*Focus potential; spell limits still apply.',0,103,360)
    ET.SubElement(page,'Pieces').text='Screen:NCST_Bonuses'
    show_total_shield_block(root)
    match_character_stats_font(root)
