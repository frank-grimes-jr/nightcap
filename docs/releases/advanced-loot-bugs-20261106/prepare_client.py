"""Prepare only the three client replacements; preserve other signed XML bytes."""
import argparse
import hashlib
from pathlib import Path
import re
import shutil
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
from client_advanced_loot_ui import add_advanced_loot

BASELINE_XML = '07205a47f2117e3f13f68d1f512d05cd268f0821b17ba5a71fe6e8b8d7b4f95b'


def refresh_xml(raw, expected_sha256):
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError('Baseline XML drift: recapture and review before preparing')
    root = ET.fromstring(raw)
    generated = ET.Element('XML')
    add_advanced_loot(generated)
    names = {node.get('item') for node in generated}
    existing = [node.get('item') for node in root
                if (node.get('item') or '').startswith('NCAL_') or
                node.get('item') == 'NightcapAdvancedLootWnd']
    if len(existing) != len(names) or set(existing) != names:
        raise ValueError('Baseline loot control inventory differs')
    # Match complete top-level loot controls. Leave schema, comments, pet
    # controls and every byte outside these spans untouched.
    pattern = re.compile(rb'(?m)^[\t ]*<(Button|Label|Editbox|Screen) item="'
                         rb'(NCAL_[A-Za-z0-9]+|NightcapAdvancedLootWnd)">'
                         rb'[\s\S]*?</\1>')
    blocks = list(pattern.finditer(raw))
    if len(blocks) != len(names) or {m[2].decode('ascii') for m in blocks} != names:
        raise ValueError('Unsupported XML serialization or duplicate control')
    replacements = {}
    newline = b'\r\n' if b'\r\n' in raw else b'\n'
    for node in generated:
        ET.indent(node, space='\t', level=1)
        replacements[node.get('item')] = b'\t' + ET.tostring(node, encoding='us-ascii').rstrip().replace(b'\n', newline)
    result = pattern.sub(lambda match: replacements[match[2].decode('ascii')], raw)
    if pattern.sub(b'', raw) != pattern.sub(b'', result):
        raise ValueError('Non-loot XML bytes changed')
    after = ET.fromstring(result)
    if len(after) != len(root):
        raise ValueError('XML element count changed')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline-xml', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    xml = refresh_xml(args.baseline_xml.read_bytes(), BASELINE_XML)
    args.output.mkdir(parents=True, exist_ok=False)
    for source, name in [('eq-client-dll/build/dinput8.dll', 'dinput8.dll'),
                         ('eq-client-dll/config/patch-sites.json', 'nightcap-patch-sites.json')]:
        shutil.copyfile(ROOT / source, args.output / name)
    target = args.output / 'uifiles/nightcap/equi_petinfowindow.xml'
    target.parent.mkdir(parents=True)
    target.write_bytes(xml)
    print('Prepared three replacements; all non-loot signed XML bytes preserved.')


if __name__ == '__main__':
    main()
