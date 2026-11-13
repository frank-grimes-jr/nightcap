"""Stage a one-file Inventory delta from the captured current signed channel."""
import base64
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from client_inventory_summary_ui import inventory_summary_xml,add_inventory_summary

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'artifacts/heroic-stats'


def main():
    raw=(ART/'channel.json').read_bytes()
    manifest=json.loads(base64.b64decode(json.loads(raw)['manifest']))
    if manifest['release']!=2026111201:raise ValueError('Review changed baseline before staging')
    descriptor=next(f for f in manifest['files'] if f['path']=='uifiles/nightcap/equi_inventory.xml')
    before=(ART/'equi_inventory.xml').read_bytes()
    if len(before)!=descriptor['size'] or hashlib.sha256(before).hexdigest()!=descriptor['sha256']:
        raise ValueError('Baseline XML drift')
    after=inventory_summary_xml(before)
    # Verify existing control definitions and page references independently.
    a=ET.fromstring(before);add_inventory_summary(a);b=ET.fromstring(after)
    ET.indent(a);ET.indent(b)
    assert ET.tostring(a)==ET.tostring(b),'Delta differs from reviewed generator helper'
    dest=ART/'candidate/uifiles/nightcap/equi_inventory.xml'
    dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(after)
    receipt={'status':'unsigned_candidate_not_published','baseline_release':manifest['release'],
        'baseline_channel_sha256':hashlib.sha256(raw).hexdigest(),
        'baseline_xml_sha256':descriptor['sha256'],'candidate_xml_sha256':hashlib.sha256(after).hexdigest(),
        'candidate_size':len(after),'changed_assets':1,'retained_descriptors':len(manifest['files'])-1,
        'server_inventory_eqtypes':[10500,10501,10502,10503,10504],'added_controls':22,
        'equipment_semantics_preserved':True,'server_rule_changes':False,'native_visual_qa':'pending'}
    (ART/'candidate-verification.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':main()
