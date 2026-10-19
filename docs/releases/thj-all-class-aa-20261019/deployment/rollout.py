"""All-class AA policy and guarded Healing Boon access. Hold on uncertainty."""
import argparse
import datetime
import hashlib
import gzip
import importlib.util
import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path, PurePosixPath

ROOT = Path('/opt/nightcap/deploy/production')
STAGE = Path('/opt/nightcap/releases/all-class-aa-20261019')
EVIDENCE = STAGE / 'evidence'
HELPER = Path('/opt/nightcap/releases/zone-hunt-20261009/runtime_ops.py')
BASE_ZONE = '9d3c8d81f76597a9ca856c1052ab8426c6a6136837cfe2f7ced79e3755ede1b0'
CLONE = 'nightcap_allclass_aa_20261019'
r = None


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def load(path):
    return json.loads(path.read_text())


def manifest():
    m = load(STAGE / 'manifest.json')
    assert sha(HELPER) == m['runtime_helper_sha256']
    assert {'bin/zone', 'rollout.py', 'healing-boon-forward.sql', 'healing-boon-rollback.sql', 'aa-catalog.json.gz'} <= set(m['files'])
    for name, digest in m['files'].items():
        rel = PurePosixPath(name)
        assert not rel.is_absolute() and '..' not in rel.parts and '\\' not in name
        p = STAGE / name
        assert p.resolve().is_relative_to(STAGE) and not p.is_symlink() and sha(p) == digest
    assert m['base_hashes']['bin/zone'] == BASE_ZONE
    assert m['files']['bin/zone'] == m['zone_sha256']
    return m


def sql(statement, database='peq'):
    assert database in ('peq', CLONE)
    args = ['docker', 'compose', 'exec', '-T', 'db', 'mariadb',
            '--defaults-extra-file=/run/secrets/db_backup_config', '--batch', '--raw', '--skip-column-names', '--default-character-set=utf8mb4', database]
    result = subprocess.run(args, cwd=ROOT, input=statement, text=True, capture_output=True, timeout=180)
    if result.returncode:
        raise RuntimeError('Database operation failed: ' + result.stderr[-1000:])
    return result.stdout


def checksums(names):
    assert all(re.fullmatch('[a-zA-Z_][a-zA-Z_0-9]*', name) for name in names)
    result = {name: sql('CHECKSUM TABLE `' + name + '` EXTENDED;').strip().split('\t')[-1] for name in names}
    assert all(value.isdigit() for value in result.values())
    return result


def content():
    return checksums(['items', 'spells_new', 'aa_rank_prereqs', 'aa_ranks', 'aa_rank_effects', 'lootdrop', 'lootdrop_entries', 'loottable_entries', 'npc_types',
                      'spawn2', 'spawngroup', 'spawnentry', 'merchantlist', 'doors', 'zone', 'content_flags', 'rule_values'])


def saved_state():
    names = sql("SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND "
                "(TABLE_NAME LIKE 'nightcap\\_%' OR TABLE_NAME IN ('timers','completed_tasks','instance_list',"
                "'instance_list_player','respawn_times')) ORDER BY TABLE_NAME;").splitlines()
    return {'player': r.player_data(), 'custom': checksums([name for name in names if name not in
            {'nightcap_market_state', 'nightcap_market_offers'}])}


def market():
    return sql('SELECT id,enabled,epoch,expansion,loot_multiplier,buy_cost_mod,rotated_at FROM nightcap_market_state;').strip().split('\t')


def verify_market(before, started):
    after = market()
    assert len(before) == len(after) == 7 and before[:2] == after[:2] == ['1', '1']
    assert int(after[2]) == int(before[2]) + 1 and before[3:6] == after[3:6]
    stamp = datetime.datetime.fromisoformat(after[6]).replace(tzinfo=datetime.timezone.utc)
    start = datetime.datetime.fromisoformat(started.replace('Z', '+00:00'))
    assert 0 <= (stamp - start).total_seconds() <= 60
    epoch = int(after[2])
    capacity = int(sql("SELECT COALESCE(SUM(IF(kind='find',1,2)),0) FROM nightcap_market_actors;"))
    count = int(sql('SELECT COUNT(*) FROM nightcap_market_offers;'))
    assert 0 <= count <= capacity
    assert sql('SELECT epoch,COUNT(*) FROM nightcap_market_offers GROUP BY epoch;').strip() == (f'{epoch}\t{count}' if count else '')
    invalid = sql(f"""SELECT COUNT(*) FROM nightcap_market_offers o
LEFT JOIN nightcap_market_actors a ON a.npc_id=o.npc_id LEFT JOIN nightcap_market_catalog c ON c.item_id=o.item_id LEFT JOIN items i ON i.id=o.item_id
WHERE a.npc_id IS NULL OR c.item_id IS NULL OR i.id IS NULL OR o.epoch<>{epoch} OR o.remaining<>1
OR o.zone_id<>a.zone_id OR o.kind<>a.kind OR o.price_cp<=0
OR o.price_cp<>CASE o.kind WHEN 'find' THEN c.find_cp WHEN 'sell' THEN c.sell_cp ELSE c.buy_cp END
OR c.pool<>IF(o.kind='find','find','tunnel') OR c.min_expansion>{int(after[3])} OR (c.max_expansion>=0 AND c.max_expansion<{int(after[3])})
OR i.nodrop=0 OR i.norent=0 OR i.stackable<>0 OR i.maxcharges<>0 OR i.itemclass<>0 OR i.questitemflag<>0 OR i.attuneable<>0
OR c.buy_cp>=c.sell_cp OR c.buy_cp>=c.find_cp
OR EXISTS(SELECT 1 FROM merchantlist m JOIN npc_types n ON n.merchant_id=m.merchantid WHERE m.item=o.item_id AND n.id=o.npc_id);
SELECT COUNT(*) FROM (SELECT npc_id,kind,COUNT(*) n FROM nightcap_market_offers GROUP BY npc_id,kind HAVING n>IF(kind='find',1,2)) x;
SELECT COUNT(*) FROM (SELECT item_id,kind,COUNT(*) n FROM nightcap_market_offers GROUP BY item_id,kind HAVING n>IF(kind='sell',3,2)) x;""").splitlines()
    assert invalid == ['0', '0', '0']
    # The retained procedure skips a slot when its eligible pool is exhausted.
    # Authenticate every present offer and enforce capacities, not mandatory fill.
    return {'before': before, 'after': after, 'offers': count, 'capacity': capacity}


def health():
    r.call('docker', 'exec', r.state('game')['Id'], 'python3', '/opt/nightcap/start.py', '--health')


def binaries(recovery=False):
    m = manifest()
    return {name: (m['zone_sha256'] if name == 'zone' and not recovery else m['base_hashes']['bin/' + name])
            for name in ('world', 'zone', 'shared_memory', 'ucs', 'loginserver')}


def untouched(p, aa_mode='before'):
    for service in ('db', 'web', 'tunnel'):
        assert r.compact(service) == p['services'][service], service
    assert r.runtime() == p['runtime'] and r.public() == p['public']
    assert content() == p['content']
    assert caches() == p['caches']
    assert routing() == p['routing']
    assert aa_state() == p['aa_' + aa_mode], 'AA content mismatch'



def caches():
    return {p.name: sha(p) for p in (ROOT/'data/server/shared').iterdir() if p.is_file()}


def routing():
    selected = sql("SELECT ruleset_id FROM rule_sets WHERE name=COALESCE((SELECT value FROM variables WHERE varname='RuleSet'),'default');").strip()
    assert selected == '1', 'Effective ruleset changed'
    values = dict(line.split('\t') for line in sql("SELECT rule_name,rule_value FROM rule_values WHERE ruleset_id=1 AND rule_name IN ('Character:MaxLevel','World:ExpansionSettings','Expansion:CurrentExpansion','Character:AAExpMinLevel');").splitlines())
    assert values == {'Character:MaxLevel':'50','World:ExpansionSettings':'2097151','Expansion:CurrentExpansion':'0','Character:AAExpMinLevel':'1'}, values
    return {'values': values, 'sets': sql('SELECT * FROM rule_sets ORDER BY ruleset_id;'),
            'selection': sql("SELECT * FROM variables WHERE varname='RuleSet';")}


def guard_routines(database='peq'):
    assert sql("SELECT COUNT(*) FROM information_schema.ROUTINES WHERE ROUTINE_SCHEMA=DATABASE() AND ROUTINE_NAME LIKE 'nightcap_allclass_aa%20261019%';", database).strip() == '0', 'Uncertain previous SQL attempt; inspect before recovery'


def aa_state(database='peq'):
    rows = sql('SELECT * FROM aa_ability ORDER BY id;', database)
    return {'rows':len(rows.splitlines()), 'sha256':hashlib.sha256(rows.encode()).hexdigest()}


def verify_catalog():
    expected = json.loads(gzip.decompress((STAGE/'aa-catalog.json.gz').read_bytes()))
    boon = [row for row in expected['aa_ability'] if row['id'] == 389]
    assert len(boon) == 1 and boon[0]['classes'] == 550
    boon[0]['classes'] = 518  # Candidate fixture includes this deployment's sole SQL delta.
    for table, rows in expected.items():
        assert table in ('aa_ability','aa_ranks','aa_rank_effects','aa_rank_prereqs')
        fields = sorted(rows[0])
        assert all(re.fullmatch('[a-zA-Z_][a-zA-Z_0-9]*', f) for f in fields)
        query = 'SELECT JSON_OBJECT('+','.join("'"+f+"',`"+f+'`' for f in fields)+') FROM `'+table+'`;'
        actual = [json.loads(line) for line in sql(query).splitlines()]
        canonical = lambda values: sorted(json.dumps(v,sort_keys=True) for v in values)
        assert canonical(actual) == canonical(rows), table+' differs from tested AA fixture'


def rehearse(before):
    assert sql("SELECT COUNT(*) FROM information_schema.SCHEMATA WHERE SCHEMA_NAME='"+CLONE+"';").strip() == '0'
    sql('CREATE DATABASE `'+CLONE+'`;')
    sql('CREATE TABLE `'+CLONE+'`.aa_ability LIKE peq.aa_ability; INSERT INTO `'+CLONE+'`.aa_ability SELECT * FROM peq.aa_ability;')
    assert aa_state(CLONE) == before
    # Independently derive the exact expected afterimage before executing the migration.
    sql('UPDATE aa_ability SET classes=550 WHERE id=389 AND classes=518;', CLONE)
    after = aa_state(CLONE); assert after != before
    sql('UPDATE aa_ability SET classes=518 WHERE id=389 AND classes=550;', CLONE)
    assert aa_state(CLONE) == before
    for direction, expected in [('forward',after),('forward',after),('rollback',before),('rollback',before),('forward',after)]:
        guard_routines(CLONE)
        sql((STAGE/('healing-boon-'+direction+'.sql')).read_text(), CLONE)
        assert aa_state(CLONE) == expected
    guard_routines(CLONE)
    assert aa_state() == before
    return after


def content_mode(p):
    current = aa_state()
    if current == p['aa_before']: return 'before'
    assert current == p['aa_after'], 'Unknown AA image; hold for diagnosis'
    return 'after'


def validate_closed_recovery(p, current):
    original = EVIDENCE/'activation'
    # Before any possible player access, a hold may not redefine unexplained drift.
    if (original/'opening.json').exists() or not (original/'stopped-state.json').exists():
        return
    assert current == load(original/'stopped-state.json'), 'Unexplained closed-access player/timer drift'
    first_market = load(original/'market-before.json')
    started = r.state('game')['State']['StartedAt']
    if started != p['services']['game']['started_at']:
        verify_market(first_market, started)
    else:
        assert market() == first_market, 'Market changed without candidate startup'


def apply_content(folder, p, recovery):
    direction = 'rollback' if recovery else 'forward'
    expected = p['aa_before' if recovery else 'aa_after']
    guard_routines()
    # A prior uncertain acknowledgment must be diagnosed, not implicitly retried.
    if recovery:
        attempted = EVIDENCE/'activation/sql-attempted.json'
        committed = EVIDENCE/'activation/sql-committed.json'
        assert not attempted.exists() or committed.exists(), 'Uncertain SQL requires explicit diagnosis'
    save(folder/'sql-attempted.json', {'direction':direction, 'before':aa_state()})
    sql((STAGE/('healing-boon-'+direction+'.sql')).read_text())
    assert aa_state() == expected
    guard_routines()
    save(folder/'sql-committed.json', {'direction':direction, 'after':expected})


def build_image(m):
    # BuildKit parses a bare sha256 image ID as a registry name in FROM.
    # Resolve a release-local tag to the authenticated ID around the build.
    base = 'nightcap-game:all-class-aa-20261019-baseline'
    target = 'nightcap-game:all-class-aa-20261019'
    inspect = lambda name: r.out('docker', 'image', 'inspect', '--format', '{{.Id}}', name).strip()
    r.call('docker', 'tag', m['base_image_id'], base)
    assert inspect(base) == m['base_image_id']
    (STAGE / 'Dockerfile').write_text('FROM ' + base + '\nCOPY bin/zone /opt/nightcap/bin/zone\n')
    (STAGE / '.dockerignore').write_text('*\n!Dockerfile\n!.dockerignore\n!bin\n!bin/zone\n')
    r.call('docker', 'build', '--pull=false', '--network', 'none', '-t', target, str(STAGE))
    assert inspect(base) == m['base_image_id']
    return inspect(target)


def preflight():
    m = manifest()
    assert not EVIDENCE.exists(), 'Existing attempt; inspect receipts'
    # Two zone copies for layer/build storage, 512 MiB backup budget, 1 GiB reserve.
    assert shutil.disk_usage(ROOT).free >= 2 * (STAGE/'bin/zone').stat().st_size + 1536 * 1024**2
    services = {s: r.compact(s) for s in ('game', 'gateway', 'db', 'web', 'tunnel')}
    assert all(v['running'] and not v['oom_killed'] for v in services.values())
    assert services['game']['health'] == services['db']['health'] == 'healthy'
    assert services['game']['image_id'] == m['base_image_id']
    assert r.image_hashes(m['base_image_id']) == m['base_hashes']
    assert sha(ROOT / 'data/public/channel.json') == m['client_channel_sha256']
    guard_routines(); verify_catalog()
    r.running(m['base_image_id'], binaries(True), expected_restarts=services['game']['restarts']); health(); r.closed_ports()
    p = {'manifest_sha256': sha(STAGE / 'manifest.json'), 'old_image_id': m['base_image_id'],
         'services': services, 'runtime': r.runtime(), 'public': r.public(), 'content': content(),
         'caches': caches(), 'routing': routing(), 'aa_before': aa_state()}
    p['aa_after'] = rehearse(p['aa_before'])
    image = build_image(m)
    assert r.image_hashes(image) == {**m['base_hashes'], 'bin/zone': m['zone_sha256']}
    layers = lambda value: json.loads(r.out('docker', 'image', 'inspect', value))[0]['RootFS']['Layers']
    assert layers(image)[:-1] == layers(m['base_image_id'])
    for candidate in (image, m['base_image_id']):
        assert 'not found' not in r.out('docker', 'run', '--rm', '--network', 'none', '--entrypoint', 'ldd', candidate, '/opt/nightcap/bin/zone')
        r.call('docker', 'run', '--rm', '--network', 'none', '--entrypoint', 'python3', candidate, '-c',
               'import sys;sys.path.insert(0,"/opt/nightcap");import start;start.validate_native()')
        r.call('docker', 'run', '--rm', '--network', 'none', '--entrypoint', '/opt/nightcap/bin/loginserver', candidate, '--nightcap-crypto-self-test')
    assert shutil.disk_usage(ROOT).free >= 1536 * 1024**2
    p['new_image_id'] = image
    untouched(p)
    assert all(r.compact(s) == v for s, v in services.items())
    EVIDENCE.mkdir(mode=0o700); save(EVIDENCE / 'preflight.json', p)
    print('Preflight passed; access unchanged.', flush=True)


def hold(folder):
    errors = []
    for args in [('stop', 'gateway'), ('stop', '-t', '90', 'game')]:
        try: r.compose(*args)
        except BaseException as error: errors.append(type(error).__name__)
    save(folder / ('held-' + str(time.time_ns()) + '.json'), {'errors': errors, 'database_restored': False})


def activate(recovery=False):
    manifest(); p = load(EVIDENCE / 'preflight.json')
    assert p['manifest_sha256'] == sha(STAGE / 'manifest.json')
    folder = EVIDENCE / ('recovery' if recovery else 'activation')
    assert not folder.exists(), 'Never replay an uncertain activation'
    untouched(p, content_mode(p) if recovery else 'before')
    guard_routines()
    if recovery:
        assert (EVIDENCE / 'activation').exists()
        assert r.state('game')['Image'] in (p['old_image_id'], p['new_image_id'])
    else:
        assert all(r.compact(s) == p['services'][s] for s in ('game', 'gateway'))
    image = p['old_image_id'] if recovery else p['new_image_id']
    assert r.image_hashes(image) == {**manifest()['base_hashes'], 'bin/zone': binaries(recovery)['zone']}
    assert shutil.disk_usage(ROOT).free >= 1536 * 1024**2
    folder.mkdir(mode=0o700)
    try:
        r.compose('stop', 'gateway'); r.compose('stop', '-t', '90', 'game')
        assert not r.state('gateway')['State']['Running'] and not r.state('game')['State']['Running']
        old = r.state('game')['State']
        assert old['ExitCode'] == 0 and not old.get('OOMKilled')
        data = saved_state(); before_market = market()
        if recovery: validate_closed_recovery(p, data)
        save(folder / 'stopped-state.json', data); save(folder / 'market-before.json', before_market)
        r.STAGE = folder
        save(folder / 'backup.json', r.database_backup())
        assert saved_state() == data; untouched(p, content_mode(p) if recovery else 'before')
        apply_content(folder, p, recovery)
        assert saved_state() == data; untouched(p, 'before' if recovery else 'after')
        r.select(image); r.compose('up', '-d', '--wait', '--wait-timeout', '240', 'game')
        first = r.running(image, binaries(recovery)); health(); time.sleep(8)
        current = r.running(image, binaries(recovery)); assert current['started_at'] == first['started_at']
        rotation = verify_market(before_market, current['started_at'])
        assert saved_state() == data; untouched(p, 'before' if recovery else 'after'); health(); r.closed_ports()
        assert not r.state('gateway')['State']['Running']
        save(folder / 'verified-closed.json', {'runtime': current, 'game': r.compact('game'), 'market': rotation,
             'player_tables_preserved': len(data['player']), 'custom_tables_preserved': len(data['custom']), 'aa': aa_state(), 'classic': routing(), 'caches': caches()})
        print('Verified with access closed.', flush=True)
    except BaseException:
        hold(folder); raise


def open_access(recovery=False):
    manifest(); p = load(EVIDENCE / 'preflight.json')
    assert p['manifest_sha256'] == sha(STAGE / 'manifest.json')
    folder = EVIDENCE / ('recovery' if recovery else 'activation')
    closed = load(folder / 'verified-closed.json')
    assert not list(folder.glob('held-*.json')) and not (folder / 'opening.json').exists()
    try:
        assert not r.state('gateway')['State']['Running'] and r.compact('game') == closed['game']
        assert saved_state() == load(folder / 'stopped-state.json')
        assert verify_market(load(folder / 'market-before.json'), closed['runtime']['started_at']) == closed['market']
        untouched(p, 'before' if recovery else 'after'); health(); r.closed_ports()
        save(folder / 'opening.json', {'client_channel_sha256': manifest()['client_channel_sha256']})
        r.compose('up', '-d', '--wait', '--wait-timeout', '60', 'gateway')
        assert r.state('gateway')['State']['Running']
        current = r.running(closed['runtime']['image_id'], binaries(recovery))
        assert current['started_at'] == closed['runtime']['started_at']
        untouched(p, 'before' if recovery else 'after'); health(); r.closed_ports()
        save(folder / 'deployed.json', {**closed, 'runtime': current, 'gateway_open': True,
             'database_restored': False, 'owner_gameplay_accepted': False, 'recovery': recovery})
        print('Access open.', flush=True)
    except BaseException:
        hold(folder); raise


def initialize():
    global r
    manifest()
    spec = importlib.util.spec_from_file_location('retained_runtime', HELPER)
    r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
    r.STAGE = STAGE; r.EVIDENCE = EVIDENCE; r.sql = sql


if __name__ == '__main__':
    import fcntl
    assert __debug__; os.umask(0o077); initialize()
    parser = argparse.ArgumentParser(); parser.add_argument('action', choices=['preflight','activate','open','rollback','open-rollback'])
    action = parser.parse_args().action
    with (ROOT / '.deployment.lock').open('a') as lock, open('/var/lock/nightcap-gm.lock', 'a') as gm:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB); fcntl.flock(gm, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert not (ROOT / 'private/gm-maintenance.json').exists() and sql("SELECT IS_FREE_LOCK('nightcap_gm_writes');").strip() == '1'
        {'preflight': preflight, 'activate': activate, 'open': open_access,
         'rollback': lambda: activate(True), 'open-rollback': lambda: open_access(True)}[action]()
