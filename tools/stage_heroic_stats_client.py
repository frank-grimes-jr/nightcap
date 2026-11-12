"""Stage a one-file Inventory delta from the captured current signed channel."""
import base64
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from client_character_stats_ui import inventory_heroics_xml

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'artifacts/heroic-stats'


def main():
    raw=(ART/'channel.json').read_bytes()
    manifest=json.loads(base64.b64decode(json.loads(raw)['manifest']))
    if manifest['release']!=2026110701:raise ValueError('Review changed baseline before staging')
    descriptor=next(f for f in manifest['files'] if f['path']=='uifiles/nightcap/equi_inventory.xml')
    before=(ART/'equi_inventory.xml').read_bytes()
    if len(before)!=descriptor['size'] or hashlib.sha256(before).hexdigest()!=descriptor['sha256']:
        raise ValueError('Baseline XML drift')
    after=inventory_heroics_xml(before)
    # Verify existing control definitions and page references independently.
    a=ET.fromstring(before);b=ET.fromstring(after)
    for n in list(b):
        if n.get('item','').startswith('IW_Heroic'):b.remove(n)
    page=b.find("Page[@item='IW_InvPage']")
    for p in list(page.findall('Pieces')):
        if p.text.startswith('IW_Heroic'):page.remove(p)
    ET.indent(a);ET.indent(b)
    assert ET.tostring(a)==ET.tostring(b),'Existing control changed'
    dest=ART/'candidate/uifiles/nightcap/equi_inventory.xml'
    dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(after)
    receipt={'status':'unsigned_candidate_not_published','baseline_release':manifest['release'],
        'baseline_channel_sha256':hashlib.sha256(raw).hexdigest(),
        'baseline_xml_sha256':descriptor['sha256'],'candidate_xml_sha256':hashlib.sha256(after).hexdigest(),
        'candidate_size':len(after),'changed_assets':1,'retained_descriptors':len(manifest['files'])-1,
        'native_eqtypes':[251,252,254,253,255,256,257],'added_controls':14,
        'existing_controls_preserved':True,'server_rule_changes':False,'native_visual_qa':'pending'}
    (ART/'candidate-verification.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':main()
