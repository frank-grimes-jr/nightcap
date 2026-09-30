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
from client_pet_management_ui import add_pet_management
from client_advanced_loot_ui import add_advanced_loot
from client_hub_models import add_models, MODELS
from client_ecommons_hub import recall_spell, hub_files, ROOT
from client_lavastorm import lavastorm_files
from generate_pet_spell_catalog import SOURCE_SHA256


def restore_spell_classes(raw, original):
    if hashlib.sha256(original).hexdigest() != SOURCE_SHA256:
        raise ValueError('Unreviewed original spell eligibility source')
    if any(line.startswith(b'42604^') for line in raw.splitlines()):
        # Accept only the exact independently generated recall afterimage; its
        # custom ID is not part of the original class catalog.
        arrival = json.loads((ROOT/'docs/ecommons-hub/plan.json').read_bytes())['arrival']
        recall_spell(raw, arrival)
    native = {}
    for line in original.decode('latin1').splitlines():
        fields = line.split('^')
        if len(fields) == 230 and fields[:2] == ['99001', 'Ancient Attunement']:
            continue
        if len(fields) != 237 or fields[0] in native:
            raise ValueError('Malformed original spell catalog')
        native[fields[0]] = fields
    output, changed, seen = [], [], set()
    for line in raw.decode('latin1').splitlines(keepends=True):
        ending = '\r\n' if line.endswith('\r\n') else '\n' if line.endswith('\n') else ''
        fields = (line[:-len(ending)] if ending else line).split('^')
        if len(fields) != 237 or fields[0] in seen:
            raise ValueError('Malformed or duplicate packaged spell')
        seen.add(fields[0])
        if fields[0] == '42604':
            output.append('^'.join(fields)+ending)
            continue
        source = native.get(fields[0])
        # The generated hub recall is independently reviewed and applied after
        # this transform. Every ordinary packaged spell must match native identity.
        if not source or fields[1] != source[1]:
            raise ValueError('Packaged spell identity differs from the original: '+fields[0])
        if fields[104:120] != source[104:120]:
            changed.append(int(fields[0]))
            fields[104:120] = source[104:120]
        output.append('^'.join(fields)+ending)
    if not seen:
        raise ValueError('Empty packaged spell file')
    return ''.join(output).encode('latin1'), changed


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
    elif kind == 'pets':
        add_pet_management(root)
        add_advanced_loot(root)
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
    parser.add_argument('--lavastorm', required=True, type=Path, help='reviewed Classic lavastorm.s3d (read only)')
    parser.add_argument('--spell-source', type=Path, help='pinned original spells_us.txt; defaults to client Downloads')
    args = parser.parse_args()
    client, output = args.client.resolve(), args.output.resolve()
    if output == client or client in output.parents or output in client.parents:
        raise ValueError('Output and original client must be separate trees')
    if output.exists():
        raise ValueError('Refusing to overwrite an existing asset generation')
    raw = (client/'spells_us.txt').read_bytes()
    original = (args.spell_source or client/'Downloads/spells_us.txt').read_bytes()
    spells, restored = restore_spell_classes(raw, original)
    spells, ids = instant_dots(spells)
    plan=json.loads((ROOT/'docs/ecommons-hub/plan.json').read_bytes())
    files = {'spells_us.txt': recall_spell(spells,plan['arrival'])}
    files.update(hub_files(client,plan))
    files.update(lavastorm_files(args.lavastorm,client))
    for filename, kind in [('EQUI_Inventory.xml','inventory'),('EQUI_AAWindow.xml','aa'),('EQUI_PetInfoWindow.xml','pets')]:
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
    audit = {'schema':1, 'features':['three_classes','aa_class_column','instant_dots','pet_armor','advanced_loot','compact_hub_models','ecommons_tunnel_hub','ancient_attunement_recall','classic_nektulos','classic_lavastorm'],
             'status':'generated_not_installed',
             'source_spells_sha256':hashlib.sha256(raw).hexdigest(),
             'canonical_spell_source_sha256':SOURCE_SHA256, 'restored_spell_class_ids':restored,
             'instant_dot_ids':ids, 'skin_activation':'automatic_at_native_ui_load',
             'files':{name:{'size':len(data),'sha256':hashlib.sha256(data).hexdigest()} for name,data in files.items()}}
    (output/'audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    print(json.dumps({'status':audit['status'],'instant_dots':len(ids),'files':list(files)}))


if __name__ == '__main__':
    main()
