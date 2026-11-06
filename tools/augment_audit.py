"""Audit captured production content and generate a guarded candidate, never apply it."""
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/audits/augments-20261106'
# Visually reviewed stock gems/orbs/crystals from RoF2 dragitem13.dds.
# Same icon for all qualities of a family; none is wearable equipment.
# A_DragItem is VERTICAL: IDs advance down columns, not across rows.
# IconCache subtracts 500 (eqgame RVA2655da/265af8); SetCurCell RVA47a860.
ICONS = list(range(944, 968))  # dragitem13: columns 2..5, all six rows.
LABELS = {'avoidance': 'Avoidance', 'shield_block': 'Shield block (strongest Hunt only)',
          'spell_damage': 'Spell Damage', 'healing': 'Healing Amount',
          'spell_haste': 'Spell haste focus', 'mana_preservation': 'Mana preservation focus',
          'faerune': 'Faerune', 'dodge': 'Improved Dodge I', 'shielding': 'Shielding',
          'accuracy': 'Accuracy', 'spell_shielding': 'Spell shielding'}


def specialties():
    groups = json.loads((ROOT / 'config/augment-specialties.json').read_text())
    result = {}
    for specialty, zones in groups.items():
        if specialty not in LABELS:
            raise ValueError('Unknown specialty: ' + specialty)
        for zone in zones:
            if zone in result:
                raise ValueError('Duplicate zone: ' + zone)
            result[zone] = specialty
    return result


def changes(specialty, tier, icon):
    delta = {'icon': str(icon)}
    if specialty == 'shield_block' and tier:
        delta['lore'] = f'Hunt shield block +{2 if tier == 3 else 1}%; strongest Hunt augment only.'
    elif specialty in ('avoidance', 'accuracy', 'shielding', 'spell_shielding'):
        field = {'spell_shielding': 'spellshield'}.get(specialty, specialty)
        values = {'avoidance': [1, 2, 3, 4], 'accuracy': [2, 3, 4, 5],
                  'shielding': [0, 0, 1, 1], 'spell_shielding': [0, 1, 1, 2]}
        delta[field] = str(values[specialty][tier])
    elif specialty in ('spell_damage', 'healing'):
        delta['spelldmg' if specialty == 'spell_damage' else 'healamt'] = str([1, 2, 4, 8][tier])
    elif specialty in ('spell_haste', 'mana_preservation') and tier:
        delta.update(focuseffect=str((2341 if specialty == 'spell_haste' else 2344) if tier == 3
                                    else (4303 if specialty == 'spell_haste' else 4306)),
                     focustype='6', focuslevel='1', focuslevel2='1')
    elif specialty == 'dodge' and tier >= 2:
        delta.update(worneffect='3889', worntype='2', wornlevel='1', wornlevel2='1')
    elif specialty == 'faerune' and tier == 3:
        delta.update(worneffect='3660', worntype='2', wornlevel='1', wornlevel2='1')
    return delta


def literal(value):
    return 'NULL' if value == 'NULL' else "X'" + str(value).encode().hex() + "'"


def guarded_sql(rows, reverse=False, zones=(), effects=()):
    label = 'rollback' if reverse else 'forward'
    name = 'nightcap_augments_20261106_' + label
    sql = ['-- Candidate only. Stop writers, take a fresh backup, validate exact schema/content first.',
           '-- Keep player inventories and all earned-item/forge/death receipts.',
           'DELIMITER //', f'CREATE PROCEDURE {name}()', 'BEGIN',
           ' DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;',
           ' START TRANSACTION;',
           " IF (SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME IN ('items','nightcap_zone_hunt_zones') AND ENGINE='InnoDB')<>2 OR EXISTS (SELECT 1 FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=DATABASE() AND EVENT_OBJECT_TABLE IN ('items','nightcap_zone_hunt_zones')) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Unreviewed content storage'; END IF;",
           " IF NOT EXISTS (SELECT 1 FROM nightcap_zone_hunt_state WHERE id=1 AND revision=2026100901 AND enabled=1) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Hunt state drift'; END IF;"]
    if not reverse:
        sql += [" IF NOT EXISTS (SELECT 1 FROM rule_values WHERE ruleset_id=1 AND rule_name='Spells:AdditiveBonusWornType' AND rule_value='0') THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Unreviewed worn stacking rule'; END IF;"]
        used = {r['after'][k] for r in rows for k in ('focuseffect', 'worneffect')} - {'-1', '0'}
        for effect in effects:
            if effect['id'] in used:
                predicate = 'id=' + str(int(effect['id'])) + ' AND ' + ' AND '.join(f'BINARY `{k}` <=> {literal(v)}' for k, v in effect.items())
                sql += [f" IF NOT EXISTS (SELECT 1 FROM spells_new WHERE {predicate}) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Spell effect drift'; END IF;"]
    for entry in rows:
        before, after = (entry['after'], entry['before']) if reverse else (entry['before'], entry['after'])
        fields = [k for k in before if before[k] != after[k]]
        if not fields:
            continue
        # Full captured row, including all unknown columns, must still match.
        where = 'id=' + str(int(before['id'])) + ' AND ' + ' AND '.join(f'BINARY `{k}` <=> {literal(v)}' for k, v in before.items())
        sql += [' UPDATE items SET ' + ','.join(f'`{k}`={literal(after[k])}' for k in fields)
                + ',`updated`=`updated` WHERE ' + where + ';',
                " IF ROW_COUNT()<>1 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Augment preimage drift'; END IF;"]
    for zone in zones:
        if zone['short_name'] not in ('hateplaneb', 'cazicthule'):
            continue
        expected = {k: v for k, v in zone.items() if k not in ('short_name', 'long_name')}
        expected['enabled'] = '1' if reverse else '0'
        predicate = 'zone_id=' + str(int(expected['zone_id'])) + ' AND ' + ' AND '.join(f'BINARY `{k}` <=> {literal(v)}' for k, v in expected.items())
        sql += [f" UPDATE nightcap_zone_hunt_zones SET enabled={0 if reverse else 1} WHERE {predicate};",
                " IF ROW_COUNT()<>1 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Zone enable preimage drift'; END IF;"]
    sql += [' COMMIT;', 'END//', 'DELIMITER ;', f'CALL {name}();', f'DROP PROCEDURE {name};']
    return '\n'.join(sql) + '\n'


def plan(data):
    special = specialties()
    items = {int(i['id']): i for i in data['items']}
    families = []
    for z in data['zones']:
        families.append(dict(zone=z['short_name'], zone_id=int(z['zone_id']), name=z['long_name'],
                             base=int(z['augment_base']), enabled=z['enabled'] == '1',
                             rate=int(z['augment_chance'])))
    families += [dict(zone='chapterhouse', zone_id=760, name='Chapterhouse of the Fallen', base=961000, enabled=True, rate=50),
                 dict(zone='kael', zone_id=113, name='Kael: The Ashen Compact', base=961020, enabled=True, rate=50)]
    if set(special) != {f['zone'] for f in families}:
        raise ValueError('Specialty coverage differs from installed augment families')
    rows = []
    for index, family in enumerate(families):
        family['specialty'] = special[family['zone']]
        family['icon'] = ICONS[index % len(ICONS)]
        family['item'] = items[family['base'] + 3]['Name']
        family['candidate_enabled'] = family['enabled'] or family['zone'] in ('cazicthule', 'hateplaneb')
        for tier in range(4):
            before = items[family['base'] + tier]
            delta = changes(family['specialty'], tier, family['icon'])
            # Preserve every existing primary-stat budget, raw damage and healing floor.
            for field in ('spelldmg', 'healamt'):
                if field in delta:
                    delta[field] = str(max(int(before[field]), int(delta[field])))
            rows.append(dict(zone=family['zone'], tier=tier, before=before, after=before | delta))
    return families, rows


def generate():
    capture = OUT / 'production.json'
    data = json.loads(capture.read_text())
    families, rows = plan(data)
    sources = {(s['zone_id'], s['spawn_id'], s['npc_id']) for s in data['sources']}
    coverage = []
    for f in families:
        spawns = [s for s in data['spawns'] if int(s['zone_id']) == f['zone_id']]
        guards = [s for s in spawns if 'guard' in s['name'].lower()]
        coverage.append(dict(zone=f['zone'], spawn_npc_pairs=len(spawns), guard_pairs=len(guards),
            old_allowlist_pairs=sum((s['zone_id'], s['spawn_id'], s['npc_id']) in sources for s in spawns),
            old_guard_pairs=sum((s['zone_id'], s['spawn_id'], s['npc_id']) in sources for s in guards)))
    summary = dict(captured_utc=data['captured_utc'], environment=data['environment'],
        capture_sha256=hashlib.sha256(capture.read_bytes()).hexdigest(),
        status='candidate; no production writes or public publication',
        families=families, coverage=coverage, old_icons=dict(Counter(r['before']['icon'] for r in rows)),
        specialties=dict(Counter(f['specialty'] for f in families)), rules=data['rules'])
    for filename, content in [('summary.json', summary), ('item-preimages.json', rows), ('effect-preimages.json', data['effects'])]:
        (OUT / filename).write_text(json.dumps(content, indent=2) + '\n')
    (OUT / 'zone-preimages.json').write_text(json.dumps(data['zones'], indent=2) + '\n')
    (OUT / 'forward.sql').write_text(guarded_sql(rows, zones=data['zones'], effects=data['effects']))
    (OUT / 'rollback.sql').write_text(guarded_sql(rows, reverse=True, zones=data['zones']))
    report = ['# Ascension augments — November 6 audit', '',
        'Ascension is the in-game top quality (called Ascended in the request).',
        'Production source captured ' + data['captured_utc'] + '. Candidate specialties/icons below are not deployed.', '',
        '| ID | Augment | Zone | Current drops | Candidate specialty | Icon |',
        '|---:|---|---|---|---|---:|']
    for f in sorted(families, key=lambda f: (not f['enabled'], f['name'])):
        rate = (f"{f['rate']/100:g}%" if f['enabled'] else 'Disabled')
        if f['zone'] in ('chapterhouse', 'kael'):
            rate += ' · managed expedition only'
        if f['zone'] == 'hateplane':
            rate += ' · currently inherited by managed Hate B'
        report.append(f"| {f['base']+3} | {f['item']} | {f['name']} ({f['zone']}) | {rate} | {LABELS[f['specialty']]} | {f['icon']} |")
    (OUT / 'AUGMENTS.md').write_text('\n'.join(report) + '\n', encoding='utf-8')
    print(json.dumps({'families': len(families), 'definitions': len(rows), 'specialties': summary['specialties']}))


if __name__ == '__main__':
    generate()
