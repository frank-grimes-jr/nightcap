"""Main Inventory summary using authoritative server values and native AC."""
from copy import deepcopy
import re
import xml.etree.ElementTree as ET

STATS=[('STR','Strength'),('STA','Stamina'),('AGI','Agility'),('DEX','Dexterity'),
       ('WIS','Wisdom'),('INT','Intelligence'),('CHA','Charisma')]


def put(node,tag,value):
    child=node.find(tag)
    if child is None:child=ET.SubElement(node,tag)
    child.text=str(value)


def add_inventory_summary(root):
    page=root.find("Page[@item='IW_InvPage']")
    window=root.find("Screen[@item='InventoryWindow']")
    if page is None or window is None or root.find("Label[@item='IW_MIT']") is not None:
        raise ValueError('Unsupported or already updated Inventory summary')
    originals={n.get('item'):n for n in root if n.get('item')}
    required=['IW_AC','IW_ACNumber','IW_ATK','IW_ATKNumber']
    required += ['IW_'+short+suffix for short,_ in STATS for suffix in ('','Number')]
    if any(name not in originals for name in required):raise ValueError('Incomplete Inventory stat layout')
    refs={p.text.split(':')[-1] for p in page.findall('Pieces')}
    # Make room for four combat rows and long current/cap/heroic values without
    # shrinking the stock font. Equipment semantics and other tabs are retained.
    for name in refs:
        node=originals.get(name)
        if node is None:raise ValueError('Missing Inventory piece: '+name)
        x=node.find('Location/X');y=node.find('Location/Y')
        if x is not None and y is not None:
            old_x,old_y=int(x.text),int(y.text)
            if old_x>=120:x.text=str(old_x+40)
            if (old_x<120 and old_y>=122) or (node.tag=='Button' and old_y>=398):
                y.text=str(old_y+56)
        if name.startswith('Inv_Seperator') and node.findtext('Size/CX')=='120':
            node.find('Size/CX').text='160'
    for node in (page,window):
        for axis,delta in [('CX',40),('CY',56)]:
            size=node.find('Size/'+axis)
            if size is None:raise ValueError('Missing Inventory bounds')
            size.text=str(int(size.text)+delta)
    put(page,'Style_VScroll','true');put(page,'Style_HScroll','true')
    template=originals['IW_ACNumber']
    def label(name,text,x,y,width,eqtype,color,tip):
        node=deepcopy(template);node.set('item',name);node.tail=None
        for tag,value in [('ScreenID',name),('Text',text),('Location/X',x),('Location/Y',y),
                          ('Size/CX',width),('AlignRight','false'),('AlignLeft','true'),('AlignCenter','false'),
                          ('NoWrap','true'),('TooltipReference',tip)]:put(node,tag,value)
        if eqtype is None:
            current=node.find('EQType')
            if current is not None:node.remove(current)
        else:put(node,'EQType',eqtype)
        for c,value in zip(('R','G','B'),color):put(node,'TextColor/'+c,value)
        root.append(node);ET.SubElement(page,'Pieces').text=name
        return node
    green=(0,255,0);gold=(214,178,40);white=(255,255,255)
    rows=[('MIT',10500,104,'Server mitigation AC used by combat, before opponent-specific armor penetration and PvP adjustments.'),
          ('AVD',10501,118,'Server total defense rating for the hit check, not item Avoidance or a percentage. Auto means an automatic-avoidance effect; sitting and other attack checks still apply.'),
          ('DMG',10503,146,'Server Spell Damage stat bonus, not damage per cast. Spell limits and scaling still apply.'),
          ('HEAL',10504,160,'Server Healing Amount stat bonus, not healing per cast. Spell limits and scaling still apply.')]
    for name,eqtype,y,tip in rows:
        label('IW_'+name,name,1,y,28,None,white,tip)
        label('IW_'+name+'Number','--',33,y,127,eqtype,green,tip)
    for name in ('IW_ATK','IW_ATKNumber'):put(originals[name],'Location/Y',132)
    put(originals['IW_ATKNumber'],'EQType',10502);put(originals['IW_ATKNumber'],'Text','--')
    put(originals['IW_ATKNumber'],'TooltipReference','Server conventional attack rating, not damage or DPS.')
    put(originals['IW_ACNumber'],'TooltipReference','Conventional client-displayed armor class. MIT and AVD show the separate authoritative server combat ratings.')
    for index,(short,full) in enumerate(STATS):
        total=originals['IW_'+short+'Number'];name=originals['IW_'+short]
        tip='Current '+full+' / actual server cap, including heroic allowance. The yellow heroic component is already included; do not add it again.'
        for tag,value in [('EQType',10600+index),('Text','--'),('Location/X',30),('Size/CX',40),
                          ('AlignRight','true'),('AlignLeft','false'),('AlignCenter','false'),('TooltipReference',tip)]:put(total,tag,value)
        put(name,'Size/CX',28)
        for c,value in zip(('R','G','B'),green):put(total,'TextColor/'+c,value)
        y=int(total.findtext('Location/Y'))
        label('IW_Cap'+full,'--',70,y,45,10800+index,white,tip)
        label('IW_Heroic'+full,'--',115,y,45,10700+index,gold,tip)


def inventory_summary_xml(raw):
    """Replace only owning controls in the actual published XML; retain other bytes."""
    parser=ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))
    root=ET.fromstring(raw,parser=parser)
    before={n.get('item'):ET.tostring(n,encoding='utf-8') for n in root if n.get('item')}
    add_inventory_summary(root)
    result=raw;added=[]
    for node in root:
        name=node.get('item')
        if not name:continue
        current=ET.tostring(node,encoding='utf-8')
        if name not in before:
            node.tail=None;ET.indent(node,space='\t');added.append(ET.tostring(node,encoding='utf-8'))
        elif current!=before[name]:
            pattern=rb'<'+node.tag.encode()+rb'\s+item="'+re.escape(name.encode())+rb'">.*?</'+node.tag.encode()+rb'>'
            node.tail=None;ET.indent(node,space='\t')
            replacement=ET.tostring(node,encoding='utf-8')
            result,count=re.subn(pattern,lambda _:replacement,result,flags=re.DOTALL)
            if count!=1:raise ValueError('Ambiguous Inventory control: '+name)
    if result.count(b'</XML>')!=1:raise ValueError('Unsupported XML root')
    result=result.replace(b'</XML>',b'\n'+b'\n'.join(added)+b'\n</XML>')
    ET.fromstring(result)
    return result
