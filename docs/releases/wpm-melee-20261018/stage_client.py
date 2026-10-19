"""Generate only this candidate's paired spell/pet-window files; never install."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools'))
from client_gameplay_assets import restore_spell_classes,instant_dots,ui_xml
from rabid_bear import client_spells as rabid
from pet_support_spells import client_spells as support
from pet_content import client_spells as fragments
from wpm_content import client_spells as wpm
from wpm_aa import client_strings


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--client',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();client=args.client.resolve();out=args.output.resolve()
    if out.exists() or out==client or client in out.parents or out in client.parents:
        raise ValueError('Output must be a new separate staging tree')
    raw=(client/'spells_us.txt').read_bytes()
    original=(client/'Downloads/spells_us.txt').read_bytes()
    spells,restored=restore_spell_classes(raw,original)
    spells,_=instant_dots(spells)
    spells=wpm(fragments(support(rabid(spells))))
    assert wpm(fragments(support(rabid(spells))))==spells
    files={'spells_us.txt':spells,
           'dbstr_us.txt':client_strings((client/'dbstr_us.txt').read_bytes()),
           'uifiles/nightcap/equi_inventory.xml':ui_xml((client/'uifiles/default/EQUI_Inventory.xml').read_bytes(),'inventory'),
           'uifiles/nightcap/equi_petinfowindow.xml':ui_xml((client/'uifiles/default/EQUI_PetInfoWindow.xml').read_bytes(),'pets'),
           'dinput8.dll':(ROOT/'eq-client-dll/build/dinput8.dll').read_bytes()}
    out.mkdir(parents=True)
    for name,data in files.items():
        target=out/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    audit={'status':'generated_not_installed_or_signed','package_type':'delta_requiring_current_signed_base',
           'source_client':str(client),'source_spells_sha256':hashlib.sha256(raw).hexdigest(),
           'restored_classes':len(restored),'protocol':'NCPA2','proxy_version':'0.11.0',
           'files':{name:{'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()} for name,data in files.items()},
           'release_gate':'Reconcile with the current signed client manifest and retain all unrelated files before signing; native client QA pending.'}
    (out/'manifest.json').write_text(json.dumps(audit,indent=2)+'\n')
    print(json.dumps(audit))


if __name__=='__main__':main()
