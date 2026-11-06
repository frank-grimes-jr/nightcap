"""Resolve reviewed overlap with the superseded October augment candidate only."""
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = 'f9247fba'
DEV = 'be81b04e'
NATIVE = ['server-mods/code/common/zone_hunt_policy.h', 'server-mods/code/zone/zone_hunt.cpp',
          'tools/tests/test_zone_hunt_native.py', 'tools/tests/zone_hunt_death_fixture.cpp',
          'tools/tests/zone_hunt_load_fixture.cpp']


def blob(ref, name):
    return subprocess.check_output(['git', 'show', ref + ':' + name], cwd=ROOT)


for name in NATIVE:
    # Explicit replacement: this candidate supersedes the narrower static spawn
    # policy. Its actual-body tests cover the broader contract and per-zone rates.
    (ROOT / name).write_bytes(blob(CANDIDATE, name))

for name in ('features', 'recent-changes', 'unreleased', 'zone-hunt'):
    path = 'wiki/articles/' + name + '.json'
    data = json.loads(blob(CANDIDATE, path))
    prior = json.loads(blob(DEV, path))
    if name in ('recent-changes', 'unreleased'):
        anchor = 'zoning-capacity-20261030' if name == 'recent-changes' else 'zoning-capacity'
        pattern = r'<h2 id="' + anchor + r'">.*?(?=<h2|$)'
        matches = re.findall(pattern, prior['body'], flags=re.S)
        assert len(matches) == 1
        assert 'id="' + anchor + '"' not in data['body']
        data['body'] += '\n' + matches[0]
        for source in prior['sources']:
            if 'zone-capacity' in source and source not in data['sources']:
                data['sources'].append(source)
    if name == 'recent-changes':
        data['body'] += '<h2 id="zone-augments-20261029">October 29: earlier augment candidate — superseded</h2><p>The earlier static-combat proposal is superseded by the <a href="augment-audit.html">November 6 audit candidate</a>. Neither preview is a production activation record.</p>'
    if name == 'unreleased':
        data['body'] += '<h2 id="zone-augment-preview">Zone augment eligibility — Not released</h2><p>The <a href="augment-audit.html">November 6 candidate</a> replaces the narrower October 29 static-combat proposal. It includes guards, killable merchants and scripted adds, specialty bonuses and exotic icons.</p>'
    if name == 'zone-hunt':
        data['body'] += '<h2 id="regular-combat-preview">Broader zone augments — Not released</h2><p>The earlier static-combat preview is superseded by the <a href="augment-audit.html">November 6 augment audit</a>. The newer candidate includes guards, killable merchants and scripted adds; published drop rules and catalog values remain until verified activation.</p>'
    (ROOT / path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

readme = blob(DEV, 'docs/README.md').decode('utf-8')
readme = readme.replace('# Nightcap documentation\n', '# Nightcap documentation\n\n- [November 6 augment audit: full list, icons and exact QA](audits/augments-20261106/README.md)\n', 1)
(ROOT / 'docs/README.md').write_text(readme, encoding='utf-8')

catalog = ROOT / 'wiki/catalog.py'
text = catalog.read_text(encoding='utf-8')
text = text.replace('broader augment eligibility', 'November 6 augment eligibility')
text = text.replace('is prepared for regular combat mobs, including Grind/Raid.', 'is prepared for any unowned killable NPC, including guards and scripted adds.')
text = text.replace('regular-combat eligibility update', 'November 6 augment eligibility candidate')
catalog.write_text(text, encoding='utf-8')

for path in (ROOT / 'wiki/articles').glob('*.json'):
    if path.stem not in ('zone-hateplaneb', 'item-940592', 'item-940593', 'item-940594', 'item-940595'):
        continue
    data = json.loads(path.read_text(encoding='utf-8'))
    data['body'] = '<p><strong>Historical candidate values:</strong> this earlier Hate B preview is superseded by the <a href="augment-audit.html">November 6 augment audit</a>. Neither candidate is released; use the new preview for proposed chances, specialties and icons.</p>' + data['body']
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

old = ROOT / 'docs/releases/zone-augments-20261029/README.md'
text = old.read_text(encoding='utf-8')
text = text.replace('\n\nStatus:', '\n\n**Superseded candidate:** the November 6 audit in `docs/audits/augments-20261106/` replaces this narrower proposal. This report retains historical evidence; neither proposal is a deployment receipt.\n\nStatus:', 1)
old.write_text(text, encoding='utf-8')
print('Resolved five native/test overlaps, four article overlaps and documentation; preserved zone-capacity configuration and previews.')
