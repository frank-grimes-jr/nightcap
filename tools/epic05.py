"""Build the additive Epic 0.5 content package. This tool never applies SQL."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'docs/adventure-journal'


def load_catalog():
    return json.loads((DATA / 'catalog.json').read_text(encoding='utf-8'))


def era_eligible(row):
    return row['condition'] == 0 and row['min_time'] == row['max_time'] == 0 and row['chance'] > 0 and all(
        row[prefix + '_min_expansion'] in (-1, 0)
        and row[prefix + '_max_expansion'] >= -1
        and not row[prefix + '_content_flags'] and not row[prefix + '_content_flags_disabled']
        for prefix in ('spawn', 'entry'))


def validate(catalog):
    chapters = catalog['shared'] + catalog['paths']
    if len(catalog['shared']) != 3 or len(catalog['paths']) != 5:
        raise ValueError('Expected three shared chapters and five paths')
    if {c['task'] for c in chapters} != set(range(9500, 9508)):
        raise ValueError('Duplicate or unreserved task IDs')
    if {p['key'] for p in catalog['paths']} != {'guardian','striker','arcanist','warden','binder'}:
        raise ValueError('Invalid path identities')
    if {p['spell'] for p in catalog['paths']} != set(range(42801, 42806)):
        raise ValueError('Spell/native duration contract mismatch')
    if catalog['item']['id'] != 900501 or catalog['invoke_spell'] != 42800:
        raise ValueError('Item/native contract mismatch')
    if catalog['cooldown_seconds'] != 600 or catalog['era'] != 0:
        raise ValueError('Unreviewed cooldown or era')
    snapshot = json.loads((DATA / 'content-snapshot.json').read_text())
    native = {(r['id'], r['zone']): r for r in snapshot['npcs'] if era_eligible(r)}
    for chapter in chapters:
        if not 1 <= len(chapter['objectives']) <= 20 or len(chapter['title']) > 100:
            raise ValueError('Unsupported task size')
        for objective in chapter['objectives']:
            if objective['era'] != 0 or len(objective['label']) > 128:
                raise ValueError('Unreviewed objective')
            if 'npc' in objective:
                row = native.get((objective['npc'], objective['short_name']))
                if not row or (row['name'], row['level']) != (objective['name'], objective['level']):
                    raise ValueError('Objective differs from captured encounter')
                if not 20 <= objective['level'] <= 40:
                    raise ValueError('Encounter outside first campaign budget')
    for path in catalog['paths']:
        if len(path['objectives']) != 3 or path['target'] not in ('self', 'owned_pet'):
            raise ValueError('Invalid role trial')
        if not 0 <= path['duration'] <= 3 or not 1 <= len(path['effects']) <= 12:
            raise ValueError('Unbounded effect')


def task_rows(catalog):
    tasks, activities = [], []
    for chapter in catalog['shared'] + catalog['paths']:
        path = 'key' in chapter
        tasks.append(dict(id=chapter['task'], type=2, duration=0, title=chapter['title'],
                          description=chapter['description'], reward_text=(
                              chapter['key'].title() + ' attunement for your Epic 0.5' if path
                              else 'The next Adventure Journal chapter'),
                          reward_id_list='', cash_reward=0, exp_reward=0, reward_method=0,
                          min_level=chapter['level'], max_level=0, repeatable=0, enabled=1,
                          completion_emote='Your journal records the victory. Return to the Ancient Chronicler.'))
        for index, objective in enumerate(chapter['objectives']):
            activities.append(dict(taskid=chapter['task'], activityid=index, req_activity_id=-1,
                                   step=1 if path and index == 2 else 0,
                                   activitytype=2 if 'npc' in objective else 5,
                                   target_name=objective['label'], goalmethod=0, goalcount=1,
                                   description_override=objective['label'],
                                   npc_match_list=str(objective.get('npc', '')),
                                   zones=str(objective['zone']), zone_version=0, optional=0,
                                   min_x=0, max_x=0, min_y=0, max_y=0, min_z=0, max_z=0))
    return tasks, activities


def spell_rows(catalog):
    rows = []
    invoke = dict(spell=catalog['invoke_spell'], ability='Awaken the Oath', duration=0,
                  target='self', effects=[])
    for path in [invoke] + catalog['paths']:
        row = dict(id=path['spell'], name=path['ability'], player_1='BLUE_TRAIL',
                   teleport_zone='', you_cast='Your oath awakens.', other_casts="'s oath awakens.",
                   cast_on_you='Your oath answers.', cast_on_other='', spell_fades='Your oath grows quiet.',
                   range=100, aoerange=0, cast_time=0, recovery_time=0, recast_time=0,
                   buffdurationformula=1 if path['duration'] else 0,
                   buffduration=path['duration'], mana=0, goodEffect=1, Activated=0,
                   resisttype=0, targettype=5 if path['target'] == 'owned_pet' else 6,
                   skill=4, icon=1, memicon=1, new_icon=1, short_buff_box=1,
                   not_extendable=1, suspendable=0, persistdeath=0,
                   can_mgb=0, nodispell=0, no_block=0, spellgroup=path['spell'],
                   typedescnum=0, effectdescnum=0)
        for index in range(1, 17):
            row['classes' + str(index)] = 255
        for index in range(1, 13):
            effect, base, limit, maximum = (path['effects'][index - 1]
                                           if index <= len(path['effects']) else (254, 0, 0, 0))
            row.update({f'effectid{index}': effect, f'effect_base_value{index}': base,
                        f'effect_limit_value{index}': limit, f'max{index}': maximum,
                        f'formula{index}': 100})
        rows.append(row)
    return rows


def value(val):
    if isinstance(val, int):
        return str(val)
    return "CONVERT(X'" + str(val).encode('utf-8').hex() + "' USING utf8mb4)"


def insert(table, row):
    return f'INSERT INTO `{table}` (' + ','.join('`' + k + '`' for k in row) + ') VALUES (' + ','.join(map(value, row.values())) + ');'


def refuse(condition, message):
    # SIGNAL accepts a literal/local variable, not CONVERT expressions.
    literal = "'" + message.replace("'", "''") + "'"
    return f"IF {condition} THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT={literal}; END IF;"


def migration_sql(catalog):
    validate(catalog)
    tasks, activities = task_rows(catalog)
    checks = [refuse("EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name IN ('nightcap_epic05_control','nightcap_epic05_state'))", 'Epic 0.5 schema already exists; do not overwrite'),
              refuse('EXISTS (SELECT 1 FROM tasks WHERE id BETWEEN 9500 AND 9507)', 'Occupied Epic 0.5 task IDs'),
              refuse('EXISTS (SELECT 1 FROM task_activities WHERE taskid BETWEEN 9500 AND 9507)', 'Occupied Epic 0.5 activities'),
              refuse('EXISTS (SELECT 1 FROM spells_new WHERE id BETWEEN 42800 AND 42805)', 'Occupied Epic 0.5 spell IDs'),
              refuse('EXISTS (SELECT 1 FROM items WHERE id=900501)', 'Occupied Epic 0.5 item ID'),
              refuse("(SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name IN ('tasks','task_activities','spells_new','items') AND engine='InnoDB')<>4", 'Transactional content tables required')]
    unique = {o['npc']: o for c in catalog['shared'] + catalog['paths'] for o in c['objectives'] if 'npc' in o}
    gates = ' AND '.join(f"{a}.min_expansion IN (-1,0) AND {a}.max_expansion>=-1 AND COALESCE({a}.content_flags,'')='' AND COALESCE({a}.content_flags_disabled,'')=''" for a in ('s','e'))
    captured = {row['id']:row for row in json.loads((DATA/'content-snapshot.json').read_text())['npcs']}
    for npc, objective in sorted(unique.items()):
        stats = ' AND '.join('n.`'+field+'`='+value(captured[npc][field]) for field in ('hp','mindmg','maxdmg','npc_spells_id','special_abilities'))
        checks.append(refuse(f"NOT EXISTS (SELECT 1 FROM npc_types n JOIN spawnentry e ON e.npcID=n.id JOIN spawn2 s ON s.spawngroupID=e.spawngroupID WHERE n.id={npc} AND BINARY n.name=BINARY {value(objective['name'])} AND n.level={objective['level']} AND {stats} AND s.zone={value(objective['short_name'])} AND s.version=0 AND s._condition=0 AND e.min_time=0 AND e.max_time=0 AND e.chance>0 AND {gates})", 'Missing or changed encounter ' + str(npc)))
    item = dict(id=900501, Name=catalog['item']['name'], lore='*An oath earned on the roads of Norrath',
                loregroup=-1, itemclass=0, itemtype=11, slots=1, classes=65535, races=65535,
                reqlevel=35, reclevel=35, magic=1, nodrop=0, norent=255, notransfer=1,
                nopet=1, price=0, sellrate=0, weight=0, icon=973, idfile='IT63',
                ac=5, hp=35, mana=35, mr=3, fr=3, cr=3, dr=3, pr=3,
                maxcharges=-1, stacksize=1, clickeffect=42800, clicktype=4,
                clicklevel=35, clicklevel2=35, recastdelay=600, recasttype=-1,
                clickname='Awaken the Oath', proceffect=-1, worneffect=-1, focuseffect=-1,
                scrolleffect=-1, bardeffect=-1, epicitem=1,
                comment='Nightcap Epic 0.5 v1; fixed tier; attunement and cooldown are server-owned')
    schema = '''CREATE TABLE nightcap_epic05_control (
 id TINYINT UNSIGNED PRIMARY KEY, enabled TINYINT UNSIGNED NOT NULL DEFAULT 0,
 native_contract INT UNSIGNED NOT NULL, catalog_version INT UNSIGNED NOT NULL
) ENGINE=InnoDB;
CREATE TABLE nightcap_epic05_state (
 character_id INT UNSIGNED PRIMARY KEY, active_path VARCHAR(16) NOT NULL,
 ready_at BIGINT UNSIGNED NOT NULL DEFAULT 0, uses BIGINT UNSIGNED NOT NULL DEFAULT 0
) ENGINE=InnoDB;'''
    rows = [insert('nightcap_epic05_control', dict(id=1, enabled=0, native_contract=1, catalog_version=1))]
    rows += [insert('tasks', row) for row in tasks]
    rows += [insert('task_activities', row) for row in activities]
    rows += [insert('spells_new', row) for row in spell_rows(catalog)]
    rows += [insert('items', item)]
    return ('-- Additive candidate. DDL may remain empty after a later failure; never overwrite it.\n'
            'DELIMITER //\nBEGIN NOT ATOMIC\nDECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;\n'
            + '\n'.join(checks) + '\n' + schema + '\nSTART TRANSACTION;\n'
            + '\n'.join(rows) + '\nCOMMIT;\nEND //\nDELIMITER ;\n')


def spell_fields(catalog):
    schema = json.loads((DATA / 'content-snapshot.json').read_text())['schemas']['spells_new']
    if len(schema) != 237 or [r['name'] for r in schema[:2]] != ['id', 'name']:
        raise ValueError('Expected the reviewed 237-column RoF2 spell schema')
    result = {}
    for row in spell_rows(catalog):
        fields = []
        for field in schema:
            default = field['default']
            if default is None:
                default = '' if 'char' in field['type'] else '0'
            fields.append(str(row.get(field['name'], default)))
        result[row['id']] = '^'.join(fields).encode('latin1')
    return result


def client_spells(raw, catalog):
    validate(catalog)
    if not raw or (not raw.endswith(b'\n')):
        raise ValueError('Expected a nonempty newline-terminated spell file')
    expected = spell_fields(catalog)
    seen = set()
    for line in raw.splitlines():
        fields = line.split(b'^')
        if len(fields) != 237:
            raise ValueError('Malformed source spell row')
        spell_id = int(fields[0])
        if spell_id in seen:
            raise ValueError('Duplicate source spell')
        seen.add(spell_id)
        if spell_id in expected and line != expected[spell_id]:
            raise ValueError('Custom spell ID already belongs to different content')
    ending = b'\r\n' if b'\r\n' in raw else b'\n'
    return raw + b''.join(row + ending for spell_id, row in expected.items() if spell_id not in seen)


def perl_data(catalog):
    # JSON is parsed once when the plugin loads, avoiding a second hand-maintained catalog.
    return ('# Generated by tools/epic05.py; edit docs/adventure-journal/catalog.json.\n'
            'use JSON::PP ();\nmy $epic05_catalog = JSON::PP::decode_json(q~'
            + json.dumps(catalog, separators=(',', ':'), ensure_ascii=True)
            + '~);\nsub epic05_catalog { return $epic05_catalog; }\n1;\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client-source', type=Path)
    parser.add_argument('--client-output', type=Path)
    args = parser.parse_args()
    catalog = load_catalog()
    validate(catalog)
    if args.client_source or args.client_output:
        if not args.client_source or not args.client_output or args.client_source.resolve() == args.client_output.resolve():
            parser.error('Provide distinct source and staging output paths')
        if 'client_rof2_dev' in str(args.client_output.resolve()).lower():
            parser.error('The original client is read-only')
        args.client_output.parent.mkdir(parents=True, exist_ok=True)
        args.client_output.write_bytes(client_spells(args.client_source.read_bytes(), catalog))
        print('Staged six Epic 0.5 spells; source file unchanged.')
        return
    (DATA / 'setup.sql').write_text(migration_sql(catalog), encoding='utf-8')
    (DATA / 'disable.sql').write_text(
        '-- Retain all history, owned items and spell definitions. Reload tasks after applying.\n'
        'START TRANSACTION;\nUPDATE nightcap_epic05_control SET enabled=0 WHERE id=1;\n'
        'UPDATE tasks SET enabled=0 WHERE id BETWEEN 9500 AND 9507;\nCOMMIT;\n', encoding='utf-8')
    (ROOT / 'server-mods/plugins/epic05_data.pl').write_text(perl_data(catalog), encoding='utf-8')
    print('Generated eight tasks, 22 objectives, six spells, one charm and disabled release gate.')


if __name__ == '__main__':
    main()
