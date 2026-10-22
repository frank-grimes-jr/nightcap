"""AA point cost, retired XP package and temporary boost repair. Preserve current data and hold access on uncertainty."""
import argparse
import datetime
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path, PurePosixPath

ROOT = Path('/opt/nightcap/deploy/production')
STAGE = Path('/opt/nightcap/releases/aa-pacing-million-20261021')
EVIDENCE = STAGE / 'evidence'
HELPER = Path('/opt/nightcap/releases/zone-hunt-20261009/runtime_ops.py')
BASE_ZONE = '5983172545de3fc8731e228355561527890c787140616ff95c2a602b37b1525a'
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
    assert {'bin/zone', 'rollout.py'} <= set(m['files'])
    for name, digest in m['files'].items():
        rel = PurePosixPath(name)
        assert not rel.is_absolute() and '..' not in rel.parts and '\\' not in name
        p = STAGE / name
        assert p.resolve().is_relative_to(STAGE) and not p.is_symlink() and sha(p) == digest
    assert m['base_hashes']['bin/zone'] == BASE_ZONE
    assert m['files']['bin/zone'] == m['zone_sha256']
    return m


def sql(statement):
    args = ['docker', 'compose', 'exec', '-T', 'db', 'mariadb',
            '--defaults-extra-file=/run/secrets/db_backup_config', '--batch', '--raw', '--skip-column-names', 'peq']
    result = subprocess.run(args, cwd=ROOT, input=statement, text=True, capture_output=True, timeout=180)
    if result.returncode:
        raise RuntimeError('Read-only database verification failed: ' + result.stderr[-1000:])
    return result.stdout


def checksums(names):
    assert all(re.fullmatch('[a-zA-Z_][a-zA-Z_0-9]*', name) for name in names)
    result = {name: sql('CHECKSUM TABLE `' + name + '` EXTENDED;').strip().split('\t')[-1] for name in names}
    assert all(value.isdigit() for value in result.values())
    return result


def content():
    return checksums(['items', 'spells_new', 'aa_ability', 'aa_ranks', 'aa_rank_effects', 'npc_types',
                      'spawn2', 'spawngroup', 'spawnentry', 'merchantlist', 'doors', 'zone', 'content_flags'])


def saved_state():
    names = sql("SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND "
                "(TABLE_NAME LIKE 'nightcap\\_%' OR TABLE_NAME IN ('timers','completed_tasks','instance_list',"
                "'instance_list_player','respawn_times')) ORDER BY TABLE_NAME;").splitlines()
    player = r.player_data()
    player.pop('rule_values')  # Verified against exact full before/after images separately.
    return {'player': player, 'custom': checksums([name for name in names if name not in
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


def untouched(p, mode=None):
    for service in ('db', 'web', 'tunnel'):
        assert r.compact(service) == p['services'][service], service
    verify_runtime(p, mode)
    verify_rules(p, mode)
    assert r.public() == p['public']
    assert content() == p['content']
    assert sha(ROOT / 'data/server/shared/items') == p['cache_sha256']


def build_image(m):
    # BuildKit parses a bare sha256 image ID as a registry name in FROM.
    # Resolve a release-local tag to the authenticated ID around the build.
    base = 'nightcap-game:aa-pacing-million-20261021-baseline'
    target = 'nightcap-game:aa-pacing-million-20261021'
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
    assert shutil.disk_usage(ROOT).free >= (STAGE/'bin/zone').stat().st_size + 768*1024**2, 'Reserve image layer, backup and 512MiB runtime headroom'
    services = {s: r.compact(s) for s in ('game', 'gateway', 'db', 'web', 'tunnel')}
    assert all(v['running'] and not v['oom_killed'] for v in services.values())
    assert services['game']['health'] == services['db']['health'] == 'healthy'
    assert services['game']['image_id'] == m['base_image_id']
    assert r.image_hashes(m['base_image_id']) == m['base_hashes']
    assert sha(ROOT / 'data/public/channel.json') == m['client_channel_sha256']
    r.running(m['base_image_id'], binaries(True), expected_restarts=services['game']['restarts']); health(); r.closed_ports()
    p = {'manifest_sha256': sha(STAGE / 'manifest.json'), 'old_image_id': m['base_image_id'],
         'services': services, 'runtime': r.runtime(), 'public': r.public(), 'content': content(),
         'cache_sha256': sha(ROOT / 'data/server/shared/items')}
    p.update(content_preflight(m))
    image = build_image(m)
    assert r.image_hashes(image) == {**m['base_hashes'], 'bin/zone': m['zone_sha256']}
    layers = lambda value: json.loads(r.out('docker', 'image', 'inspect', value))[0]['RootFS']['Layers']
    assert layers(image)[:-1] == layers(m['base_image_id'])
    for candidate in (image, m['base_image_id']):
        assert 'not found' not in r.out('docker', 'run', '--rm', '--network', 'none', '--entrypoint', 'ldd', candidate, '/opt/nightcap/bin/zone')
        r.call('docker', 'run', '--rm', '--network', 'none', '--entrypoint', 'python3', candidate, '-c',
               'import sys;sys.path.insert(0,"/opt/nightcap");import start;start.validate_native()')
        r.call('docker', 'run', '--rm', '--network', 'none', '--entrypoint', '/opt/nightcap/bin/loginserver', candidate, '--nightcap-crypto-self-test')
    assert shutil.disk_usage(ROOT).free >= 768*1024**2, 'Reserve stopped backup and runtime headroom'
    p['new_image_id'] = image
    untouched(p, 'before')
    assert all(r.compact(s) == v for s, v in services.items())
    EVIDENCE.mkdir(mode=0o700); save(EVIDENCE / 'preflight.json', p)
    print('Preflight passed; access unchanged.', flush=True)


def hold(folder):
    errors = []
    for args in [('stop', 'gateway'), ('stop', '-t', '90', 'game')]:
        try: r.compose(*args)
        except BaseException as error: errors.append(type(error).__name__)
    states = {}
    for service in ('gateway','game'):
        try: states[service] = r.state(service)['State']['Running']
        except BaseException: states[service] = None
    save(folder / ('held-' + str(time.time_ns()) + '.json'), {'errors': errors, 'running': states, 'database_restored': False})


def activate(recovery=False):
    manifest(); p = load(EVIDENCE / 'preflight.json')
    assert p['manifest_sha256'] == sha(STAGE / 'manifest.json')
    folder = EVIDENCE / ('recovery' if recovery else 'activation')
    assert not folder.exists(), 'Never replay an uncertain activation'
    untouched(p, None if recovery else 'before')
    if recovery:
        assert (EVIDENCE / 'activation').exists()
        assert r.state('game')['Image'] in (p['old_image_id'], p['new_image_id'])
    else:
        assert all(r.compact(s) == p['services'][s] for s in ('game', 'gateway'))
    image = p['old_image_id'] if recovery else p['new_image_id']
    assert r.image_hashes(image) == {**manifest()['base_hashes'], 'bin/zone': binaries(recovery)['zone']}
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
        assert shutil.disk_usage(ROOT).free >= 512*1024**2, 'Insufficient post-backup runtime headroom'
        assert saved_state() == data; untouched(p, None if recovery else 'before')
        apply_content(folder, p, recovery)
        assert saved_state() == data; untouched(p, 'before' if recovery else 'after')
        r.select(image); r.compose('up', '-d', '--wait', '--wait-timeout', '240', 'game')
        first = r.running(image, binaries(recovery)); health(); time.sleep(8)
        current = r.running(image, binaries(recovery)); assert current['started_at'] == first['started_at']
        rotation = verify_market(before_market, current['started_at'])
        assert saved_state() == data; untouched(p, 'before' if recovery else 'after'); health(); r.closed_ports()
        assert not r.state('gateway')['State']['Running']
        save(folder / 'verified-closed.json', {'runtime': current, 'game': r.compact('game'), 'market': rotation,
             'player_tables_preserved': len(data['player']), 'custom_tables_preserved': len(data['custom'])})
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
        assert shutil.disk_usage(ROOT).free >= 512*1024**2, 'Runtime headroom changed'
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


QUESTS = ('quests/ecommons/Magus_Goldwind.pl', 'quests/poknowledge/Magus_Goldwind.pl')

def rules():
    return sql('SELECT * FROM rule_values ORDER BY ruleset_id,rule_name;')

def verify_rules(p, mode=None):
    actual = rules()
    allowed = [p['rules_'+mode]] if mode else [p['rules_before'],p['rules_after']]
    assert actual in allowed, 'Unknown full rule-table state'

def verify_runtime(p, mode=None):
    actual = r.runtime()
    expected = dict(p['runtime'])
    for name in QUESTS:
        allowed = [p['quests_'+mode][name]] if mode else [p['quests_before'][name],p['quests_after'][name]]
        assert actual[name] in allowed, 'Unknown quest image: '+name
        expected[name] = actual[name]
    assert actual == expected, 'Unrelated runtime script drift'

def content_preflight(m):
    assert sql("SELECT ruleset_id FROM rule_sets WHERE name=COALESCE((SELECT value FROM variables WHERE varname='RuleSet'),'default');").strip() == '1'
    assert sql("SELECT ruleset_id,rule_value FROM rule_values WHERE rule_name='AA:ExpPerPoint';").strip() == '1\t40000'
    assert sql("SELECT rule_name,rule_value FROM rule_values WHERE ruleset_id=1 AND rule_name IN ('AA:PassiveExpPercent','AA:NormalizedAAEnabled','AA:ModernAAScalingEnabled') ORDER BY rule_name;").strip() == 'AA:ModernAAScalingEnabled\tfalse\nAA:NormalizedAAEnabled\tfalse\nAA:PassiveExpPercent\t10'
    assert sql("SELECT COUNT(*) FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA='peq' AND EVENT_OBJECT_TABLE='rule_values';").strip() == '0'
    assert sql("SELECT ENGINE FROM information_schema.TABLES WHERE TABLE_SCHEMA='peq' AND TABLE_NAME='rule_values';").strip() == 'InnoDB'
    assert sql("SELECT buffdurationformula,effectid1,effect_base_value1 FROM spells_new WHERE id=21030;").strip() == '3600\t337\t50'
    before = rules()
    row = sql("SELECT * FROM rule_values WHERE rule_name='AA:ExpPerPoint';")
    fields = row.split('\t'); assert fields[:3] == ['1','AA:ExpPerPoint','40000'] and before.count(row) == 1
    fields[2] = '1000000'
    after = before.replace(row,'\t'.join(fields),1); assert before != after
    # Transaction rehearsal leaves live values unchanged even if interrupted.
    result = sql("START TRANSACTION; "+rule_sql('40000','1000000')+" SELECT ROW_COUNT(); SELECT * FROM rule_values ORDER BY ruleset_id,rule_name; "+rule_sql('1000000','40000')+" SELECT ROW_COUNT(); ROLLBACK;")
    assert result == '1\n'+after+'1\n' and rules() == before
    previous = STAGE/'previous'; previous.mkdir(mode=0o700)
    quest_before = {}; quest_after = {}
    for name in QUESTS:
        live = ROOT/'data/server'/name
        assert sha(live) == m['quest_preimages'][name]
        assert sha(STAGE/name) == m['files'][name]
        # Reject scripts that would shadow the named Perl NPC file.
        assert not live.with_suffix('.lua').exists()
        dst = previous/name; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(live,dst)
        quest_before[name] = sha(live); quest_after[name] = sha(STAGE/name)
        r.call('docker','compose','exec','-T','game','perl','-c','/srv/nightcap/'+name)
    return {'rules_before':before,'rules_after':after,'quests_before':quest_before,'quests_after':quest_after}

def rule_sql(before, after):
    assert (before,after) in [('40000','1000000'),('1000000','40000')]
    return "UPDATE rule_values SET rule_value='"+after+"' WHERE ruleset_id=1 AND rule_name='AA:ExpPerPoint' AND rule_value='"+before+"';"

def apply_content(folder,p,recovery):
    verify_runtime(p); verify_rules(p)
    target = 'before' if recovery else 'after'
    values = ('1000000','40000') if recovery else ('40000','1000000')
    save(folder/'content-attempted.json', {'target':target})
    if rules() != p['rules_'+target]:
        changed = sql('START TRANSACTION; '+rule_sql(*values)+' SELECT ROW_COUNT(); COMMIT;').strip()
        assert changed == '1', 'Uncertain rule commit; hold and inspect receipts'
    verify_rules(p,target)
    for name in QUESTS:
        live = ROOT/'data/server'/name
        source = STAGE/'previous'/name if recovery else STAGE/name
        assert sha(source) == p['quests_'+target][name]
        if sha(live) != p['quests_'+target][name]:
            temp = live.with_name(live.name+'.aa-pacing-'+str(time.time_ns()))
            st = live.stat()
            with temp.open('xb') as stream:
                stream.write(source.read_bytes()); stream.flush(); os.fsync(stream.fileno())
            os.chmod(temp,st.st_mode); os.chown(temp,st.st_uid,st.st_gid); os.replace(temp,live)
    verify_runtime(p,target)
    save(folder/'content-committed.json', {'target':target,'aa_xp_per_point':values[1]})

def validate_closed_recovery(p,current):
    original = EVIDENCE/'activation'
    if (original/'opening.json').exists() or not (original/'stopped-state.json').exists(): return
    assert current == load(original/'stopped-state.json'), 'Unexplained closed-access player drift'
    started = r.state('game')['State']['StartedAt']
    baseline = load(original/'market-before.json')
    if started != p['services']['game']['started_at']:
        verify_market(baseline,started)
    else:
        assert market() == baseline, 'Unexpected market change without boot'


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
