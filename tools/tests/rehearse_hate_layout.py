"""Exercise Hate content SQL in a new local-only database, retaining evidence.

Schema clones contain no copied player data. All character/run/earned rows below
are synthetic. Never writes PEQ or connects to production.
"""
import hashlib
import json
from pathlib import Path
import re
import sys
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from rehearse_dungeons import query
import hate_layout_migration as layout
from pok_hub_migration import insert


def main():
    population_sha256 = hashlib.sha256((layout.HERE / 'population.json').read_bytes()).hexdigest()
    name = 'nightcap_dungeon_rehearsal_' + uuid.uuid4().hex[:12]
    print('Isolated Hate layout rehearsal: ' + name, flush=True)
    def run(sql, check=True):
        return query(sql, name, check)
    query(f'CREATE DATABASE `{name}` CHARACTER SET utf8mb4;', 'information_schema')
    preserved = ['inventory', 'nightcap_dungeon_runs', 'nightcap_dungeon_members',
                 'nightcap_dungeon_corpses', 'nightcap_dungeon_respawns',
                 'spawn2', 'npc_types', 'ground_spawns', 'spawngroup', 'spawnentry']
    schema = (ROOT / 'server-mods/sql/20261016_dungeons.sql').read_text()
    for table in list(layout.KEYS) + preserved:
        if table.startswith('nightcap_dungeon_'):
            # The local PEQ baseline predates dungeons. Use the reviewed native
            # schema, including its actual foreign keys, in this empty database.
            ddl = re.search(r'CREATE TABLE ' + table + r' \(.*?ENGINE=InnoDB.*?;', schema, re.S)
            assert ddl, table
            run(ddl.group())
        else:
            run(f'CREATE TABLE `{table}` LIKE peq.`{table}`;')
    aux = json.loads((layout.HERE / 'public-aux.json').read_text())
    for row in aux['ground_spawns']:
        run(insert('ground_spawns', row))
    source = json.loads((layout.HERE / 'public-source.json').read_text())['spawn'][0]
    run(insert('npc_types', dict(id=source['npc_id'], name=source['name'],
        level=source['level'], **{'class': source['class']}, race=source['race'],
        bodytype=source['bodytype'], hp=source['hp'], mindmg=source['min_dmg'],
        maxdmg=source['max_dmg'], loottable_id=source['loot_id'])))
    run(insert('spawngroup', dict(id=source['group_id'], name='Hate rehearsal public group')))
    run(insert('spawnentry', dict(spawngroupID=source['group_id'], npcID=source['npc_id'], chance=source['chance'])))
    source_by_id = {r['id']: r for r in json.loads((layout.HERE / 'public-source.json').read_text())['spawn']
                    if r['zone'] == 'hateplane'}
    spawn_fixtures = []
    for policy in layout.source_policy():
        pose = source_by_id[policy['id']]
        spawn_fixtures.append(insert('spawn2', dict(policy, x=pose['x'], y=pose['y'], z=pose['z'],
                                                   heading=pose['heading'], pathgrid=pose['grid_id'])))
    run('\n'.join(spawn_fixtures))
    # Retain public grids and an unrelated private service across every case.
    run(insert('grid', dict(id=1, zoneid=186, type=0, type2=0)))
    run(insert('grid_entries', dict(gridid=1, zoneid=186, number=1,
                                   x=1, y=2, z=3, heading=0, pause=0)))
    run(insert('nightcap_dungeon_spawns', dict(zone_id=76, spawn_id=9100012,
            npc_id=998812, group_id=998812, boss_id=0, is_final=0,
            x=-337.08, y=-374.8, z=2, heading=0, respawn=86400, grid_id=0)))
    for zone, character in [(76, 4242), (186, 4243)]:
        identity = str(uuid.uuid4())
        run(insert('nightcap_dungeon_runs', dict(run_id=identity, instance_id=character,
            instance_start=1, zone_id=zone, owner_id=character, mode=1, seed=42,
            revision=2026101601, expires_at=9999999999)))
        run(insert('nightcap_dungeon_members', dict(run_id=identity, character_id=character,
            reward_item=960114, reward_drop_id=str(uuid.uuid4()), completed_at=123)))
        run(insert('nightcap_dungeon_corpses', dict(run_id=identity, spawn_id=1996,
            corpse_id=str(uuid.uuid4()), payload='{}', expires_at=9999999999)))
        run(insert('nightcap_dungeon_respawns', dict(run_id=identity, spawn_id=1996,
            respawn_at=9999999999, died_at=123)))
        run(insert('inventory', dict(character_id=character, slot_id=23,
                                      item_id=960114, charges=1)))
    def checksums():
        return {t: run(f'CHECKSUM TABLE `{t}` EXTENDED;').stdout.strip() for t in preserved}
    baseline = checksums()
    before = layout.capture(lambda sql: run(sql).stdout)
    after = layout.desired(before)
    sql = layout.patch_sql(before, after)
    run('ALTER TABLE grid ENGINE=MyISAM;')
    engine = run(sql, False)
    assert engine.returncode and 'Hate layout engine drift: grid' in engine.stderr
    run('ALTER TABLE grid ENGINE=InnoDB;')
    run('CREATE TRIGGER rehearsal_guard BEFORE INSERT ON grid FOR EACH ROW SET NEW.type=NEW.type;')
    trigger = run(sql, False)
    assert trigger.returncode and 'Hate layout trigger drift: grid' in trigger.stderr
    run('DROP TRIGGER rehearsal_guard;')
    # Fail after the private population was inserted, proving all preceding
    # writes roll back on a later statement error.
    marker = 'INSERT INTO `grid`'
    assert marker in sql
    fault = sql.replace(marker, "SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='injected Hate fault';\n" + marker, 1)
    failed = run(fault, False)
    assert failed.returncode and 'injected Hate fault' in failed.stderr
    assert layout.capture(lambda q: run(q).stdout)['rows'] == before['rows']
    assert checksums() == baseline
    # An occupied reserved row must reject without losing that row.
    run(insert('grid', dict(id=9001, zoneid=186, type=0, type2=0)))
    occupied = run(sql, False)
    assert occupied.returncode and 'Hate layout count drift: grid' in occupied.stderr
    assert run('SELECT type FROM grid WHERE zoneid=186 AND id=9001;').stdout.strip() == '0'
    run('DELETE FROM grid WHERE zoneid=186 AND id=9001;')
    run(sql)
    for check in layout.runtime_checks():
        actual = run(check['sql'] + ';').stdout.strip()
        assert actual == check['expected'], (check['label'], actual, check['expected'])
    # A source respawn variance change is rejected by the paired runtime
    # contract even though this migration never mutates the public spawn.
    policy_check = next(c for c in layout.runtime_checks() if c['label'] == 'hate-layout/original-spawn-policy/0')
    run('UPDATE spawn2 SET variance=variance+1 WHERE id=1836;')
    assert run(policy_check['sql'] + ';').stdout.strip() != policy_check['expected']
    run('UPDATE spawn2 SET variance=variance-1 WHERE id=1836;')
    installed = layout.capture(lambda q: run(q).stdout)
    repeat = run(sql, False)
    assert repeat.returncode and 'Hate layout count drift: nightcap_dungeon_spawns' in repeat.stderr
    assert layout.capture(lambda q: run(q).stdout)['rows'] == installed['rows']
    inverse = layout.patch_sql(installed, before)
    run('UPDATE nightcap_dungeon_spawns SET x=x+1 WHERE zone_id=186 AND spawn_id=1836;')
    drift = run(inverse, False)
    assert drift.returncode and 'Hate layout row drift: nightcap_dungeon_spawns' in drift.stderr
    run('UPDATE nightcap_dungeon_spawns SET x=x-1 WHERE zone_id=186 AND spawn_id=1836;')
    run(inverse)
    assert layout.capture(lambda q: run(q).stdout)['rows'] == before['rows']
    assert checksums() == baseline
    assert run('SELECT COUNT(*) FROM grid WHERE zoneid=186 AND id=1;').stdout.strip() == '1'
    assert run('SELECT COUNT(*) FROM grid_entries WHERE zoneid=186 AND gridid=1;').stdout.strip() == '1'
    assert run('SELECT COUNT(*) FROM nightcap_dungeon_spawns WHERE zone_id=76;').stdout.strip() == '1'
    # Reinstall after an exact isolated inverse is safe and verifies that no
    # transaction or row lock was left behind by rejected SQL.
    run(sql)
    assert checksums() == baseline
    for filename, data in [('rehearsal-before.json', before), ('rehearsal-installed.json', installed)]:
        (layout.HERE / filename).write_text(json.dumps(data, indent=2) + '\n')
    (layout.HERE / 'inverse-rehearsal.sql').write_text(
        '-- ISOLATED REHEARSAL ONLY: retain successor content after real runs exist.\n' + inverse,
        encoding='utf-8', newline='\n')
    assert population_sha256 == hashlib.sha256((layout.HERE / 'population.json').read_bytes()).hexdigest(), 'Population changed during rehearsal'
    assert sql == (layout.HERE / 'forward.sql').read_text(), 'Forward artifact differs from rehearsed SQL'
    report = dict(database=name, scope='isolated local MariaDB; synthetic players only; no production writes',
        population_sha256=population_sha256,
        counts={t: len(v) for t, v in after['rows'].items()},
        forward_sha256=hashlib.sha256(sql.encode()).hexdigest(),
        inverse_sha256=hashlib.sha256(inverse.encode()).hexdigest(),
        runtime_checks=len(layout.runtime_checks()), forward_passed=True,
        repeat_rejected=True, occupied_range_rejected=True, inverse_drift_rejected=True,
        nontransactional_engine_rejected=True, unexpected_trigger_rejected=True,
        original_spawn_variance_drift_detected=True,
        injected_mid_transaction_failure_rolled_back=True,
        isolated_inverse_passed=True, reinstall_passed=True,
        earned_run_corpse_respawn_inventory_and_public_content_preserved=checksums() == baseline,
        checksums=baseline, gameplay_acceptance=False)
    (layout.HERE / 'rehearsal.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
