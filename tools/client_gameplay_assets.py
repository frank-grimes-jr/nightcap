"""Generate client spell/UI assets in a separate staging directory; never install.

RoF2 field indices are verified against the spells_new repository/export schema.
The input client remains read-only. The signed launcher installs the output later.
"""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from client_pet_armor_ui import add_pet_page
from client_hub_models import add_models, MODELS
from client_ecommons_hub import recall_spell, hub_files, ROOT


def instant_dots(raw):
    output, changed, seen = [], [], set()
    for number, line in enumerate(raw.decode('latin1').splitlines(keepends=True), 1):
        ending = '\r\n' if line.endswith('\r\n') else '\n' if line.endswith('\n') else ''
        body = line[:-len(ending)] if ending else line
        fields = body.split('^')
        if len(fields) != 237:
            raise ValueError(f'Expected 237 RoF2 fields at line {number}')
        try:
            spell_id, cast, formula, duration, good = [int(fields[i]) for i in (0,13,16,17,83)]
            effects = [int(v) for v in fields[86:98]]
            bases = [int(v) for v in fields[20:32]]
        except ValueError as error:
            raise ValueError(f'Non-numeric spell policy field at line {number}') from error
        if spell_id < 0 or spell_id in seen or cast < 0:
            raise ValueError(f'Invalid or duplicate spell at line {number}')
        seen.add(spell_id)
        # CalcBuffDuration_formula treats buffduration=0 as no duration cap.
        timed = 1 <= formula <= 15 or formula in (50,51) or formula >= 200
        dot = not good and timed and any(effect in (0,334) and base < 0 for effect,base in zip(effects,bases))
        if dot and cast:
            fields[13] = '0'
            changed.append(spell_id)
        output.append('^'.join(fields) + ending)
    if not seen:
        raise ValueError('Empty spell file')
    return ''.join(output).encode('latin1'), changed


def ui_xml(raw, kind):
    parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))
    root = ET.fromstring(raw, parser=parser)
    if kind == 'inventory':
        labels = root.findall("Label[@item='IW_Class']")
        if len(labels) != 1 or labels[0].findtext('EQType') != '3':
            raise ValueError('Unsupported inventory class label')
        labels[0].find('EQType').text = '10001'
        labels[0].find('Text').text = 'Classes loading'
        add_pet_page(root)
    elif kind == 'aa':
        for name in ('AAW_GeneralList','AAW_ArchList','AAW_ClassList','AAW_SpecialList'):
            matches = root.findall(f"Listbox[@item='{name}']")
            if len(matches) != 1:
                raise ValueError('Missing or duplicate AA list')
            node = matches[0]
            headings = [column.findtext('Heading') for column in node.findall('Columns')]
            if headings != ['Title','Cur/Max','Cost','Category']:
                raise ValueError('Unsupported AA column layout')
            column = ET.SubElement(node, 'Columns')
            ET.SubElement(column, 'Width').text = '300'
            ET.SubElement(column, 'Heading').text = 'Class'
            scroll = node.find('Style_HScroll')
            if scroll is None:
                scroll = ET.SubElement(node,'Style_HScroll')
            scroll.text = 'true'
        screens = root.findall("Screen[@item='AAWindow']")
        if len(screens) != 1:
            raise ValueError('Missing AA window')
        # Widen the lists' actual containers, not just the outer window.
        tab = root.find("TabBox[@item='AAW_Subwindows']")
        pages = [root.find(f"Page[@item='{name}']") for name in
                 ('AAW_GeneralPage','AAW_ArchetypePage','AAW_ClassPage','AAW_SpecialPage')]
        if tab is None or any(page is None for page in pages):
            raise ValueError('Unsupported AA tab/page layout')
        for node in [screens[0], tab, *pages, root.find("STMLbox[@item='AAW_Description']")]:
            if node is None or node.find('Size/CX') is None:
                raise ValueError('Missing AA container size')
            size = node.find('Size/CX')
            size.text = str(int(size.text) + 300)
        for node in root:
            x = node.find('Location/X')
            if x is not None and (int(x.text) >= 490 or node.get('item') in ('AAW_Timer','AAW_Count')):
                x.text = str(int(x.text) + 300)
    else:
        raise ValueError('Unknown UI asset')
    # RoF2's reader needs the stock lexical Schema declaration. ElementTree
    # otherwise emits ns0:Schema and drops xmlns:dt, which made the game reject
    # the entire skin and silently fall back to Default.
    for schema in root.findall('{EverQuestData}Schema'):
        schema.tag = 'Schema'
        schema.set('xmlns', 'EverQuestData')
        schema.set('xmlns:dt', 'EverQuestDataTypes')
    ET.indent(root, space='\t')
    return b'<?xml version="1.0" encoding="us-ascii" ?>\n' + ET.tostring(root, encoding='us-ascii', xml_declaration=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    client, output = args.client.resolve(), args.output.resolve()
    if output == client or client in output.parents or output in client.parents:
        raise ValueError('Output and original client must be separate trees')
    if output.exists():
        raise ValueError('Refusing to overwrite an existing asset generation')
    raw = (client/'spells_us.txt').read_bytes()
    spells, ids = instant_dots(raw)
    plan=json.loads((ROOT/'docs/ecommons-hub/plan.json').read_bytes())
    files = {'spells_us.txt': recall_spell(spells,plan['arrival'])}
    files.update(hub_files(client,plan))
    for filename, kind in [('EQUI_Inventory.xml','inventory'),('EQUI_AAWindow.xml','aa')]:
        files['uifiles/nightcap/'+filename.lower()] = ui_xml((client/'uifiles/default'/filename).read_bytes(),kind)
    files['poknowledge_chr.txt'] = add_models((client/'poknowledge_chr.txt').read_bytes())
    for model in MODELS.values():
        archive = client/model['archive']
        if not archive.is_file() or not 0 < archive.stat().st_size < 32*1024*1024:
            raise ValueError('Missing or unsupported model archive: '+model['archive'])
        files[model['archive']] = archive.read_bytes()
    # Validate all inputs before creating any output. Existing user skins stay intact.
    output.mkdir(parents=True)
    for name, data in files.items():
        target = output/name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    audit = {'schema':1, 'features':['three_classes','aa_class_column','instant_dots','pet_armor','compact_hub_models','ecommons_tunnel_hub','ancient_attunement_recall','classic_nektulos'],
             'status':'generated_not_installed',
             'source_spells_sha256':hashlib.sha256(raw).hexdigest(),
             'instant_dot_ids':ids, 'skin_activation':'automatic_at_native_ui_load',
             'files':{name:{'size':len(data),'sha256':hashlib.sha256(data).hexdigest()} for name,data in files.items()}}
    (output/'audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    print(json.dumps({'status':audit['status'],'instant_dots':len(ids),'files':list(files)}))


if __name__ == '__main__':
    main()
