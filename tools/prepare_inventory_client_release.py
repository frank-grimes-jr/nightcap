"""Prepare pinned signer/verifier/publisher programs and three reviewed assets."""
import hashlib
import json
from pathlib import Path
import re
import shutil
from inventory_release_support import ROOT,HERE,ART

RELEASE=2026111202


def main():
    old=ART/'channel.json';baseline=json.loads((ART/'release-baseline.json').read_text())
    assert baseline['client_release']==2026111201
    assert hashlib.sha256(old.read_bytes()).hexdigest()==baseline['client_channel_sha256']
    assets=ART/'candidate'
    shutil.copyfile(ROOT/'eq-client-dll/build/dinput8.dll',assets/'dinput8.dll')
    shutil.copyfile(ROOT/'eq-client-dll/config/patch-sites.json',assets/'nightcap-patch-sites.json')
    names=['dinput8.dll','nightcap-patch-sites.json','uifiles/nightcap/equi_inventory.xml']
    pins={n:hashlib.sha256((assets/n).read_bytes()).hexdigest() for n in names}
    source=(ROOT/'docs/releases/advanced-loot-bugs-20261106/prepare.go').read_text(encoding='utf-8')
    source=source.replace('advanced-loot-sign','inventory-sign').replace('LauncherVersion: "0.6.0"','LauncherVersion: "0.7.0"')
    source=source.replace('ee56323a1780ef5481c3c55e195ec4831969b82f3aed839b81ec3300b31d4dd0',baseline['client_channel_sha256'])
    source=source.replace('2026110604','2026111201').replace('2026110605',str(RELEASE))
    source=re.sub(r'\tpins := map\[string\]string\{[^\n]+\}', '\tpins := map[string]string{'+','.join(json.dumps(n)+':'+json.dumps(pin) for n,pin in pins.items())+'}',source)
    start=source.index('\tm.PatchNotes = append(');end=source.index('\n\n\tchanged :=',start)
    note='Adds Inventory combat ratings, stat caps and yellow heroic totals. MIT/AVD use server combat values. Fully exit EverQuest and press Play. Live testing; visual QA remains open.'
    line='\tm.PatchNotes = append([]manifest.PatchNote{{Release: m.Release, Date: "2026-11-12", Changes: []manifest.PatchChange{{Kind: "feature", Text: '+json.dumps(note)+'}}}}, old.PatchNotes...)'
    source=source[:start]+line+source[end:];source=source.replace('Advanced-loot','Inventory')
    (HERE/'prepare_client.go').write_text(source,encoding='utf-8',newline='\n')
    command=ROOT/'eq-launcher/cmd/inventory-sign';command.mkdir(exist_ok=True)
    (command/'main.go').write_text(source,encoding='utf-8',newline='\n')
    verify=(ROOT/'docs/releases/advanced-loot-bugs-20261106/verify.go').read_text(encoding='utf-8')
    verify=verify.replace('LauncherVersion: "0.6.0"','LauncherVersion: "0.7.0"').replace('2026110604','2026111201').replace('2026110605',str(RELEASE))
    verify=re.sub(r'\tpins := map\[string\]string\{[^\n]+\}', '\tpins := map[string]string{'+','.join(json.dumps(n)+':'+json.dumps(pin) for n,pin in pins.items())+'}',verify)
    # Retain the actual current signed Quick Buff strings, rather than an older
    # recall-only release's hash embedded in this historical verifier template.
    verify=verify.replace('"ad2c20c6bf1f8bb855d3ccb2f0de0c2fec97ca3e5c01b3a4f8db0681fba1bddc"','before[f.Path].SHA256')
    (HERE/'verify_client.go').write_text(verify,encoding='utf-8',newline='\n')
    command=ROOT/'eq-launcher/cmd/inventory-verify';command.mkdir(exist_ok=True)
    (command/'main.go').write_text(verify,encoding='utf-8',newline='\n')
    (HERE/'client-pins.json').write_text(json.dumps(pins,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':'prepared_not_signed','release':RELEASE,'pins':pins}))


if __name__=='__main__':main()
