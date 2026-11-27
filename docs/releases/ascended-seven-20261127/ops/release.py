"""Activate the tested zone and one persisted tier rule while both game versions are stopped."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import time

import common as ops

STAGE = ops.STAGE
RELEASE = 'ascended-seven-20261127'
TAG = ('nightcap-local' if ops.LOCAL else 'nightcap-game') + ':' + RELEASE
TIERS = ('Zone:LootTierEpicChance', 'Zone:LootTierLegendaryChance', 'Zone:LootTierRareChance')
FILTER = 'rule_name IN (' + ','.join("'" + name + "'" for name in TIERS) + ')'
SELECT = 'SELECT ruleset_id,rule_name,rule_value FROM rule_values WHERE ' + FILTER + ' ORDER BY rule_name,ruleset_id;'


def rows(value):
    return [f'1\t{name}\t{n}' for name, n in zip(TIERS, (500, value, 2000))]


def update(table, old, new):
    assert table in ('rule_values', 'test_tiers') and {old, new} == {100, 700}
    return (f"UPDATE {table} SET rule_value='{new}' WHERE ruleset_id=1 "
            f"AND rule_name='{TIERS[1]}' AND BINARY rule_value='{old}';")


def transaction(table, old, new):
    siblings = (f"(rule_name='{TIERS[0]}' AND BINARY rule_value='500') OR "
                f"(rule_name='{TIERS[1]}' AND BINARY rule_value='{new}') OR "
                f"(rule_name='{TIERS[2]}' AND BINARY rule_value='2000')")
    return ('DELIMITER //\nBEGIN NOT ATOMIC\n'
              'DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;\n'
              'START TRANSACTION;\n' + update(table, old, new) +
              f"\nIF ROW_COUNT() <> 1 OR (SELECT COUNT(*) FROM {table} WHERE " + FILTER + ") <> 3 "
              f"OR (SELECT COUNT(*) FROM {table} WHERE ruleset_id=1 AND (" + siblings + ")) <> 3 "
              "THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Unexpected tier state'; END IF;\n"
              'COMMIT;\nEND//\nDELIMITER ;\n')


def sql_switch(old, new):
    assert ops.db(SELECT).splitlines() == rows(old)
    ops.db(transaction('rule_values', old, new))
    assert ops.db(SELECT).splitlines() == rows(new)


def rehearse():
    assert ops.db("SELECT ruleset_id FROM rule_sets WHERE name='default'") == '1'
    assert ops.db("SELECT ENGINE FROM information_schema.TABLES WHERE TABLE_SCHEMA='peq' AND TABLE_NAME='rule_values'") == 'InnoDB'
    script = 'CREATE TEMPORARY TABLE test_tiers LIKE rule_values;\n'
    script += 'INSERT INTO test_tiers SELECT * FROM rule_values WHERE ' + FILTER + ';\n'
    sample = SELECT.replace('rule_values', 'test_tiers') + '\n'
    for old, new in ((100, 700), (700, 100)):
        script += transaction('test_tiers', old, new) + sample
    # An unexpected Epic rate makes the same transaction unwind its Ascended write.
    script += f"UPDATE test_tiers SET rule_value='501' WHERE rule_name='{TIERS[0]}';\nSET @caught=0;\n"
    nested = transaction('test_tiers', 100, 700).removeprefix('DELIMITER //\n').removesuffix('END//\nDELIMITER ;\n')
    script += ("DELIMITER //\nBEGIN NOT ATOMIC\nDECLARE CONTINUE HANDLER FOR SQLSTATE '45000' SET @caught=1;\n"
               + nested + "END;\nEND//\nDELIMITER ;\nSELECT @caught;\n" + sample)
    assert ops.db(script).splitlines() == [*rows(700), *rows(100), '1', rows(100)[0].replace('500','501'), *rows(100)[1:]]


def read(name):
    return json.loads((STAGE / name).read_bytes())


def manifest():
    data = read('manifest.json')
    assert re.fullmatch('[0-9a-f]{40}', data['source'])
    assert set(data['operator']) == {'release.py', 'common.py', 'world_count.py', 'probe.py'}
    for name, pin in data['operator'].items():
        assert ops.digest(STAGE / name) == pin
    assert ops.digest(STAGE / 'zone') == data['zone'] != data['binaries']['zone']
    return data


def check(m, candidate):
    expected_image = read('prepared.json')['image'] if candidate else m['base_image']
    game = ops.state(ops.SERVICE)
    assert game['Image'] == expected_image and game['State']['Health']['Status'] == 'healthy'
    assert not game['State']['OOMKilled'] and game['RestartCount'] == 0
    snapshot = json.loads(ops.compose('exec', '-T', ops.SERVICE, 'python3', '-', data=(STAGE/'probe.py').read_bytes()))
    snapshot['quests'] = {name: hashlib.sha256(base64.b64decode(value)).hexdigest() for name, value in snapshot['quests'].items()}
    expected = dict(m['binaries'], zone=m['zone']) if candidate else m['binaries']
    assert snapshot['binaries'] == expected and snapshot['cache'] == m['cache'] and snapshot['quests'] == m['quests']
    actual = ops.db(SELECT).splitlines()
    assert actual == rows(700 if candidate else 100)
    return dict(image=expected_image, source=m['source'], players=ops.world('GetPlayerCount'), rules=actual, **snapshot)


def prepare(m):
    check(m, False)
    rehearse()
    volume = STAGE if ops.LOCAL else Path('/mnt/archive')
    size = int(ops.db("SELECT SUM(data_length) FROM information_schema.tables WHERE table_schema='peq'"))
    assert shutil.disk_usage(volume).free > size + 512*1024**2
    image = m['base_image']
    assert ops.run('docker', 'image', 'inspect', '--format', '{{.Id}}', m['base_tag']).decode().strip() == image
    base = TAG + '-base-' + image[7:19]
    ops.run('docker', 'tag', image, base)
    context = STAGE / 'image'
    context.mkdir(exist_ok=True)
    (context/'Dockerfile').write_text(f'FROM {base}\nCOPY --chmod=0755 zone /opt/nightcap/bin/zone\n')
    if not (context/'zone').exists():
        shutil.copyfile(STAGE/'zone', context/'zone')
    assert ops.digest(context/'zone') == m['zone']
    ops.run('docker', 'build', '--network', 'none', '--pull=false', '-t', TAG, context)
    candidate = ops.run('docker', 'image', 'inspect', '--format', '{{.Id}}', TAG).decode().strip()
    assert ops.run('docker', 'run', '--rm', '--network', 'none', '--entrypoint', 'sha256sum', candidate,
                   '/opt/nightcap/bin/zone').split()[0].decode() == m['zone']
    assert b'not found' not in ops.run('docker', 'run', '--rm', '--network', 'none', '--entrypoint', 'ldd', candidate, '/opt/nightcap/bin/zone')
    receipt = dict(manifest=ops.digest(STAGE/'manifest.json'), image=candidate, forward_inverse_stale_rehearsed=True)
    if (STAGE/'prepared.json').exists():
        assert read('prepared.json') == receipt
    else:
        ops.evidence('prepared.json', receipt)


def activate(m, forward):
    prepared = read('prepared.json')
    assert prepared['manifest'] == ops.digest(STAGE/'manifest.json')
    assert ops.run('docker', 'image', 'inspect', '--format', '{{.Id}}', TAG).decode().strip() == prepared['image']
    selector = TAG if ops.LOCAL else prepared['image']
    old, new = (m['base_tag'], selector) if forward else (selector, m['base_tag'])
    old_rate, new_rate = (100, 700) if forward else (700, 100)
    assert check(m, not forward)['players'] == 0, 'Game occupied'
    assert ops.db("SELECT IS_FREE_LOCK('nightcap_gm_writes')") == '1'
    assert ops.LOCAL or not (ops.ROOT/'private/gm-maintenance.json').exists()
    assert not ops.world('IsLocked') and (ops.LOCAL or ops.state('gateway')['State']['Running'])
    phase = 'activation' if forward else 'rollback'
    ops.evidence(phase+'-started.json', dict(source=m['source']))
    stopped = switched = opening = False
    try:
        if ops.LOCAL:
            assert ops.world('Lock')['status'] == 'complete' and ops.world('IsLocked')
        else:
            ops.compose('stop', 'gateway')
            assert not ops.state('gateway')['State']['Running']
            time.sleep(125)
        assert ops.world('GetPlayerCount') == 0
        ops.stop_game()
        stopped = True
        ops.evidence(phase+'-backup.json', ops.backup())
        sql_switch(old_rate, new_rate)
        ops.atomic_pointer(old, new)
        switched = True
        ops.start_game()
        result = check(m, forward)
        assert result['players'] == 0
        ops.evidence(phase+'-verified.json', result)
        opening = True
        ops.reopen()
        assert not ops.world('IsLocked')
        ops.evidence(phase+'-complete.json', dict(result, admission_open=True))
    except BaseException:
        if opening:
            raise
        if stopped:
            if ops.state(ops.SERVICE)['State']['Running']:
                assert ops.world('GetPlayerCount') == 0
                ops.stop_game()
            if switched:
                ops.atomic_pointer(new, old)
            current = ops.db(SELECT).splitlines()
            if current == rows(new_rate):
                sql_switch(new_rate, old_rate)
            else:
                assert current == rows(old_rate), 'Unexpected state during recovery; holding closed'
        ops.start_game()
        check(m, not forward)
        ops.reopen()
        raise


if __name__ == '__main__':
    if not __debug__:
        raise RuntimeError('Integrity checks disabled')
    os.umask(0o077)
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('prepare', 'activate', 'rollback', 'verify'))
    action = parser.parse_args().action
    with ops.locks():
        data = manifest()
        if action == 'prepare':
            prepare(data)
        elif action == 'verify':
            print(json.dumps(check(data, True)))
        else:
            activate(data, action == 'activate')
