"""Approved configuration-only rollout; never restore player data or auto-enable LORE."""
import fcntl
import hashlib
import json
import mmap
import os
from pathlib import Path
import struct
import sys

sys.path.insert(0, '/opt/nightcap/releases/zone-hunt-20261009')
import runtime_ops as r

STAGE = Path('/opt/nightcap/releases/remove-item-lore-20261012')
r.STAGE = STAGE
r.EVIDENCE = STAGE / 'evidence'
EXPECTED_IMAGE = 'sha256:5e8a26cf1275758dc78ae4327f520389c98e01dcba3ffaed42e8f84ce7502022'
LOADER = '91664a87eac78306e8a76ab4cb923ba1f03c2d0da180278db6b6cf9b6607c0ef'


def save(name, data):
    with (r.EVIDENCE / name).open('x') as output:
        json.dump(data, output, indent=2)
        output.write('\n')


def load(name):
    return json.loads((r.EVIDENCE / name).read_text())


def policy(enabled):
    expected = 'true' if enabled else 'false'
    assert r.sql("SELECT ruleset_id,rule_value FROM rule_values WHERE rule_name='Items:DisableLore';").strip() == '1\t' + expected
    assert r.sql("SELECT COUNT(*) FROM variables WHERE varname IN ('RuleSet','disablelore');").strip() == '0'
    assert r.sql("SELECT name FROM rule_sets WHERE ruleset_id=1;").strip() == 'default'


def cache(enabled):
    rows = [tuple(map(int, row.split('\t'))) for row in r.sql('SELECT id,loregroup FROM items ORDER BY id;').splitlines()]
    digest = hashlib.sha256()
    path = r.ROOT / 'data/server/shared/items'
    with path.open('rb') as source, mmap.mmap(source.fileno(), 0, access=mmap.ACCESS_READ) as mem:
        payload, count, maximum, current = struct.unpack_from('<IIII', mem)
        assert payload + 8 == len(mem) and maximum == current == len(rows)
        assert len(mem) == 20 + 4 * count + 1332 * current
        start = 16 + 4 * count
        indices = set()
        for item_id, lore in rows:
            assert 0 <= item_id < count
            index = struct.unpack_from('<I', mem, 16 + item_id * 4)[0]
            assert index < current and index not in indices
            indices.add(index)
            data = mem[start + index * 1332:start + (index + 1) * 1332]
            assert struct.unpack_from('<I', data, 440)[0] == item_id
            assert struct.unpack_from('<i', data, 464)[0] == (0 if enabled else lore), item_id
            assert data[468] == (0 if enabled else int(lore != 0)), item_id
            digest.update(data[:464])
            digest.update(data[469:])
        full = hashlib.sha256(mem).hexdigest()
    return {'items_checked': len(rows), 'raw_lore_items': sum(lore != 0 for _, lore in rows),
            'effective_lore_items': 0 if enabled else sum(lore != 0 for _, lore in rows),
            'non_lore_fields_sha256': digest.hexdigest(), 'cache_sha256': full}


def player_data():
    # Rules are checked separately, preserving every column except the one value.
    data = r.player_data()
    del data['rule_values']
    return data


def custom_data():
    tables = r.sql("SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA='peq' AND TABLE_NAME LIKE 'nightcap\\_%' AND TABLE_NAME NOT IN ('nightcap_market_offers','nightcap_market_state') ORDER BY TABLE_NAME;").splitlines()
    assert all(name.replace('_', '').isalnum() for name in tables)
    data = {name: r.sql('CHECKSUM TABLE `' + name + '` EXTENDED;').strip().split('\t')[-1] for name in tables}
    assert all(value.isdigit() for value in data.values())
    return data


def rules():
    return r.sql("SELECT ruleset_id,rule_name,IF(rule_name='Items:DisableLore','<owned>',rule_value),notes FROM rule_values ORDER BY ruleset_id,rule_name;")


def preflight():
    assert not r.EVIDENCE.exists()
    policy(False)
    game = r.compact('game')
    assert game['image_id'] == EXPECTED_IMAGE and game['running'] and game['health'] == 'healthy'
    hashes = r.image_hashes(EXPECTED_IMAGE)
    assert hashes['bin/shared_memory'] == LOADER
    binaries = {name: hashes['bin/' + name] for name in ('world', 'zone', 'ucs', 'loginserver', 'shared_memory')}
    r.running(EXPECTED_IMAGE, binaries, expected_restarts=game['restarts'])
    start = r.out('docker', 'exec', game['id'], 'cat', '/opt/nightcap/start.py')
    assert "subprocess.run([str(BIN/'shared_memory')], check=True)" in start
    r.closed_ports()
    assert r.compact('gateway')['running']
    before = cache(False)
    r.EVIDENCE.mkdir(mode=0o700)
    backup = r.database_backup()
    save('preflight.json', {'image': EXPECTED_IMAGE, 'binaries': binaries,
        'services': {s: r.compact(s) for s in ('game', 'gateway', 'db', 'web', 'tunnel')},
        'runtime': r.runtime(), 'public': r.public(), 'content': r.content_data(),
        'rules': rules(), 'cache': before, 'backup': backup,
        'activate_sha256': r.sha(STAGE / 'activate.sql')})
    print(json.dumps({'status': 'preflight_passed', 'backup': backup, 'cache': before}), flush=True)


def activate():
    p = load('preflight.json')
    assert r.sha(STAGE / 'activate.sql') == p['activate_sha256']
    policy(False)
    assert all(r.compact(s) == p['services'][s] for s in ('game', 'gateway'))
    r.untouched(p)
    assert rules() == p['rules'] and r.content_data() == p['content']
    opened = False
    try:
        r.compose('stop', 'gateway')
        r.compose('stop', '-t', '90', 'game')
        state = r.state('game')['State']
        assert not r.state('gateway')['State']['Running'] and not state['Running'] and state['ExitCode'] == 0 and not state.get('OOMKilled')
        before = {'player': player_data(), 'custom': custom_data(), 'cache': cache(False)}
        save('stopped-data.json', before)
        r.sql((STAGE / 'activate.sql').read_text())
        policy(True)
        r.compose('up', '-d', '--no-deps', '--wait', '--wait-timeout', '240', 'game')
        # Existing container restart count is preserved by Compose start.
        running = r.running(p['image'], p['binaries'], expected_restarts=p['services']['game']['restarts'])
        after = cache(True)
        assert after['items_checked'] == before['cache']['items_checked']
        assert after['non_lore_fields_sha256'] == before['cache']['non_lore_fields_sha256']
        assert player_data() == before['player'], 'Player-state drift; keep access closed'
        assert custom_data() == before['custom'], 'Custom-state drift; keep access closed'
        assert rules() == p['rules'] and r.content_data() == p['content']
        policy(True)
        r.untouched(p)
        r.closed_ports()
        verified = {'runtime': running, 'cache': after, 'player_tables_preserved': len(before['player']),
                    'custom_tables_preserved': len(before['custom']), 'backup': p['backup']}
        save('verified-closed.json', verified)
        opened = True  # Treat any lost acknowledgment as possible player activity.
        r.compose('up', '-d', '--no-deps', '--wait', '--wait-timeout', '60', 'gateway')
        assert r.compact('gateway')['running']
        save('activated.json', {**verified, 'gateway_open': True, 'database_restored': False})
        print(json.dumps({'status': 'activated', 'gateway_open': True, 'cache': after}), flush=True)
    except BaseException:
        r.compose('stop', 'gateway')
        save('held-closed.json', {'gateway_open': False, 'opening_attempted': opened,
                                'automatic_lore_rollback': False, 'database_restored': False})
        raise


def report():
    p = load('preflight.json')
    a = load('activated.json')
    policy(True)
    running = r.running(p['image'], p['binaries'], expected_restarts=p['services']['game']['restarts'])
    assert running['started_at'] == a['runtime']['started_at']
    current = cache(True)
    assert current == a['cache']
    assert rules() == p['rules'] and r.content_data() == p['content']
    r.untouched(p)
    r.closed_ports()
    assert r.compact('gateway')['running']
    result = {'status': 'healthy', 'runtime': running, 'cache': current, 'gateway_open': True}
    save('followup.json', result)
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    os.umask(0o077)
    assert r.sha(Path(r.__file__)) == 'a3242bee3e8d4a7e60ea81bbd6fd34587201b712247665f3c03673733b95a811'
    action = sys.argv[1]
    assert action in ('preflight', 'activate', 'report')
    with (r.ROOT / '.deployment.lock').open('a') as lock, open('/var/lock/nightcap-gm.lock', 'a') as gm_lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        fcntl.flock(gm_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert not (r.ROOT / 'private/gm-maintenance.json').exists()
        assert r.sql("SELECT IS_FREE_LOCK('nightcap_gm_writes');").strip() == '1'
        globals()[action]()
