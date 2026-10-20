"""Paired THJ release. One-shot components, stopped backup and closed-access checks."""
import argparse
import base64
import fcntl
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

ROOT = Path('/opt/nightcap/deploy/production')
STAGE = Path('/opt/nightcap/releases/thj-behaviors-live-20261019')
EVIDENCE = STAGE / 'evidence'
CLONE = 'nightcap_thj_behaviors_live_20261019'
TABLES = ('items', 'spells_new', 'aa_ability', 'aa_ranks', 'aa_rank_effects',
          'aa_rank_prereqs', 'rule_values')
CONTROL = ('npc_types', 'spawn2', 'spawngroup', 'spawnentry', 'merchantlist', 'doors', 'zone', 'content_flags', 'lootdrop', 'lootdrop_entries', 'loottable_entries', 'character_pet_armor')
r = None
b = None


def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def save(path, value):
    with path.open('x') as f:
        json.dump(value, f, indent=2)
        f.write('\n'); f.flush(); os.fsync(f.fileno())


def load(path):
    return json.loads(path.read_text())


def manifest():
    m = load(STAGE / 'manifest.json')
    assert sha(Path('/opt/nightcap/releases/zone-hunt-20261009/runtime_ops.py')) == m['runtime_helper_sha256']
    for name, digest in m['files'].items():
        path = STAGE / name
        assert path.resolve().is_relative_to(STAGE) and not path.is_symlink() and sha(path) == digest, name
    assert len(m['components']) == 3 and m['components'] == sorted(m['components'])
    return m


def sql(statement, database='peq'):
    assert database in ('peq', CLONE)
    args = ['docker','compose','exec','-T','db','mariadb',
            '--defaults-extra-file=/run/secrets/db_backup_config','--batch','--raw','--quick',
            '--skip-column-names','--default-character-set=utf8mb4', database]
    result = subprocess.run(args, cwd=ROOT, input='SET SESSION max_session_mem_used=134217728;\n'+statement,
                            text=True, capture_output=True, timeout=1800)
    if result.returncode:
        raise RuntimeError('Database operation failed: '+result.stderr[-2200:])
    return result.stdout


def checksums(tables, database='peq'):
    assert all(re.fullmatch('[a-z_][a-z_0-9]*', n) for n in tables)
    result = {n: sql('CHECKSUM TABLE `'+n+'` EXTENDED;', database).strip().split('\t')[-1] for n in tables}
    assert all(v.isdigit() for v in result.values())
    return result


def schema(database='peq'):
    return sql('SHOW CREATE TABLE character_pet_armor;', database)


def expected_schema(before):
    old = 'CONSTRAINT `pet_armor_slot` CHECK (`slot_id` in (2,17,7,9,12,18,19,20))'
    new = 'CONSTRAINT `pet_armor_slot` CHECK (`slot_id` between 0 and 21)'
    assert before.count(old) == 1
    return before.replace(old, new)


def guards():
    names = TABLES
    quoted = ','.join("'"+n+"'" for n in names)
    rows = sql('SELECT TABLE_NAME,ENGINE FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME IN ('+quoted+');')
    assert dict(x.split('\t') for x in rows.splitlines()) == {n:'InnoDB' for n in names}
    assert sql('SELECT COUNT(*) FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=DATABASE() AND EVENT_OBJECT_TABLE IN ('+quoted+');').strip() == '0'
    assert sql("SELECT COUNT(*) FROM information_schema.ROUTINES WHERE ROUTINE_SCHEMA=DATABASE() AND ROUTINE_NAME LIKE 'nightcap_thj%';").strip() == '0'



def routing():
    selected = sql("SELECT ruleset_id FROM rule_sets WHERE name=COALESCE((SELECT value FROM variables WHERE varname='RuleSet'),'default');").strip()
    assert selected == '1', 'Effective ruleset changed'
    values = dict(line.split('\t') for line in sql("SELECT rule_name,rule_value FROM rule_values WHERE ruleset_id=1 AND rule_name IN ('Character:MaxLevel','World:ExpansionSettings','Expansion:CurrentExpansion');").splitlines())
    assert values == {'Character:MaxLevel':'50','World:ExpansionSettings':'2097151','Expansion:CurrentExpansion':'0'}, values
    return {'sets':sql('SELECT * FROM rule_sets ORDER BY ruleset_id;'),
            'selection':sql("SELECT * FROM variables WHERE varname='RuleSet';")}


def published_client():
    receipt = load(STAGE/'client/published.json')
    assert receipt['release'] == 2026101902 and receipt['verified_files'] == 138
    entries = load(STAGE/'client/publication-files.json')
    assert receipt['channel_sha256'] == manifest()['files']['client/channel.json'] == entries['channel.json']['sha256']
    assert len(entries) == 139
    for name,record in entries.items():
        path = ROOT/'data/public'/name
        assert path.resolve().is_relative_to(ROOT/'data/public') and not path.is_symlink()
        assert path.stat().st_size == record['size'] and sha(path) == record['sha256'], name
    hosted = load(STAGE/'client/hosted-verification.json')
    assert hosted['release'] == 2026101902 and hosted['hosted'] is True and hosted['managed_files'] == 138
    assert hosted['channel_sha256'] == receipt['channel_sha256']
    assert hosted['signature'] == 'valid against shipped production key'
    assert hosted['verified_bytes'] == sum(v['size'] for n,v in entries.items() if n != 'channel.json')


def saved_state():
    players = r.player_data(); players.pop('rule_values')
    names = sql("SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND "
                "(TABLE_NAME LIKE 'nightcap\\_%' OR TABLE_NAME IN ('timers','completed_tasks','instance_list',"
                "'instance_list_player','respawn_times')) ORDER BY TABLE_NAME;").splitlines()
    return {'player': players, 'custom': checksums([n for n in names if n not in
            {'nightcap_market_state','nightcap_market_offers'}])}


def binaries():
    m = manifest()
    return {n: m['files'].get('bin/'+n, m['base_hashes']['bin/'+n]) for n in
            ('world','zone','shared_memory','ucs','loginserver')}


def health():
    r.call('docker','exec',r.state('game')['Id'],'python3','/opt/nightcap/start.py','--health')


def untouched(p, installed=False, published=False):
    for service in ('db','web','tunnel'):
        assert r.compact(service) == p['services'][service], service
    assert r.runtime() == p['runtime'], 'Quest/plugin drift'
    assert routing() == p['routing'], 'Ruleset selection drift'
    public = dict(p['public'])
    if published:
        public['channel.json'] = manifest()['files']['client/channel.json']
    assert r.public() == public, 'Public root drift'
    assert checksums(CONTROL) == p['control'], 'Unrelated content drift'
    assert checksums(TABLES) == p['after' if installed else 'before'], 'Content mismatch'



def build_image(m):
    base = 'nightcap-game:thj-behaviors-live-20261019-base'
    target = 'nightcap-game:thj-behaviors-live-20261019'
    inspect = lambda n: r.out('docker','image','inspect','--format','{{.Id}}',n).strip()
    r.call('docker','tag',m['base_image_id'],base)
    assert inspect(base) == m['base_image_id']
    (STAGE/'Dockerfile').write_text('FROM '+base+'\nCOPY bin/ /opt/nightcap/bin/\n')
    (STAGE/'.dockerignore').write_text('*\n!Dockerfile\n!.dockerignore\n!bin\n!bin/*\n')
    assert {p.name for p in (STAGE/'bin').iterdir()} == {'world','zone','shared_memory'}
    r.call('docker','build','--pull=false','--network','none','-t',target,str(STAGE))
    assert inspect(base) == m['base_image_id']
    image = inspect(target)
    assert r.image_hashes(image) == {**m['base_hashes'], **{'bin/'+n:h for n,h in binaries().items()}}
    layers = lambda value: json.loads(r.out('docker','image','inspect',value))[0]['RootFS']['Layers']
    assert layers(image)[:-1] == layers(m['base_image_id'])
    for n in ('world','zone','shared_memory'):
        assert 'not found' not in r.out('docker','run','--rm','--network','none','--entrypoint','ldd',image,'/opt/nightcap/bin/'+n)
    r.call('docker','run','--rm','--network','none','--entrypoint','python3',image,'-c',
           'import sys;sys.path.insert(0,"/opt/nightcap");import start;start.validate_native()')
    r.call('docker','run','--rm','--network','none','--entrypoint','/opt/nightcap/bin/loginserver',image,'--nightcap-crypto-self-test')
    return image


def preflight():
    m = manifest(); assert not EVIDENCE.exists(), 'Inspect previous attempt; never replay'
    assert shutil.disk_usage(ROOT).free >= 3*1024**3
    services = {s:r.compact(s) for s in ('game','gateway','db','web','tunnel')}
    assert all(v['running'] and not v['oom_killed'] for v in services.values())
    assert services['game']['health'] == services['db']['health'] == 'healthy'
    assert services['game']['image_id'] == m['base_image_id']
    assert r.image_hashes(m['base_image_id']) == m['base_hashes']
    assert sha(ROOT/'data/public/channel.json') == m['previous_channel_sha256']
    r.running(m['base_image_id'],{n:m['base_hashes']['bin/'+n] for n in binaries()},expected_restarts=services['game']['restarts'])
    health(); r.closed_ports(); guards()
    p = {'manifest_sha256':sha(STAGE/'manifest.json'), 'services':services,
         'runtime':r.runtime(),'public':r.public(),'before':checksums(TABLES),
         'control':checksums(CONTROL),'routing':routing()}
    assert sql("SELECT COUNT(*) FROM information_schema.SCHEMATA WHERE SCHEMA_NAME='"+CLONE+"';").strip() == '0'
    sql('CREATE DATABASE `'+CLONE+'`;')
    for table in TABLES:
        sql('CREATE TABLE `'+CLONE+'`.`'+table+'` LIKE peq.`'+table+'`;')
        sql('INSERT INTO `'+CLONE+'`.`'+table+'` SELECT * FROM peq.`'+table+'`;')
    assert checksums(TABLES, CLONE) == p['before']

    for component in m['components']:
        sql((STAGE/component).read_text(), CLONE)
    p['after'] = checksums(TABLES, CLONE)

    p['rules_after'] = sql('SELECT ruleset_id,rule_name,rule_value FROM rule_values ORDER BY ruleset_id,rule_name;',CLONE)
    sql('DROP DATABASE `'+CLONE+'`;')
    p['new_image_id'] = build_image(m)
    untouched(p); assert all(r.compact(s) == v for s,v in services.items())
    health(); r.closed_ports()
    EVIDENCE.mkdir(mode=0o700); save(EVIDENCE/'preflight.json',p)
    print('Preflight passed: fresh content clone forward, paired binaries and unchanged live services.',flush=True)


def hold():
    errors = []
    for args in [('stop','gateway'),('stop','-t','90','game')]:
        try:
            r.compose(*args)
        except BaseException as error:
            errors.append(type(error).__name__)
    save(EVIDENCE/('held-'+str(time.time_ns())+'.json'),{'errors':errors,'database_restored':False})


def activate():
    m = manifest(); p = load(EVIDENCE/'preflight.json')
    assert sha(STAGE/'manifest.json') == p['manifest_sha256']
    assert not (EVIDENCE/'activation-started.json').exists()
    untouched(p); guards()
    assert all(r.compact(s) == v for s,v in p['services'].items())
    assert shutil.disk_usage(ROOT).free >= 1024**3 + 512*1024**2 + sum((ROOT/'data/server/shared'/n).stat().st_size for n in ('items','spells'))
    save(EVIDENCE/'activation-started.json',{'owner_authorized':True})
    try:
        r.compose('stop','gateway'); r.compose('stop','-t','90','game')
        state = r.state('game')['State']
        assert not state['Running'] and state['ExitCode'] == 0 and not state.get('OOMKilled')
        assert not r.state('gateway')['State']['Running']
        data = saved_state(); before_market = b.market()
        save(EVIDENCE/'stopped-state.json',data); save(EVIDENCE/'market-before.json',before_market)
        save(EVIDENCE/'backup.json',r.database_backup())
        for name in ('items','spells'):
            path = ROOT/'data/server/shared'/name
            shutil.copyfile(path,STAGE/'private-backup'/('cache-'+name))
        assert saved_state() == data; untouched(p)
        for component in m['components']:
            name = Path(component).stem
            save(EVIDENCE/(name+'-attempted.json'),{'sha256':m['files'][component]})
            sql((STAGE/component).read_text())
            save(EVIDENCE/(name+'-committed.json'),{'status':'success'})
        assert saved_state() == data; untouched(p,True)
        r.select(p['new_image_id'])
        # Generate using the exact candidate loader with game/world stopped, then
        # require startup's second generation to be byte-identical.
        r.compose('run','--rm','--no-deps','--entrypoint','/opt/nightcap/bin/shared_memory','game')
        expected_caches = {n:{'bytes':(ROOT/'data/server/shared'/n).stat().st_size,'sha256':sha(ROOT/'data/server/shared'/n)} for n in ('items','spells')}
        save(EVIDENCE/'generated-caches.json',expected_caches)
        r.compose('up','-d','--wait','--wait-timeout','240','game')
        first = r.running(p['new_image_id'],binaries()); health(); time.sleep(8)
        current = r.running(p['new_image_id'],binaries())
        assert current['started_at'] == first['started_at']
        rotation = b.verify_market(before_market,current['started_at'])
        assert saved_state() == data; untouched(p,True)
        assert sql('SELECT ruleset_id,rule_name,rule_value FROM rule_values ORDER BY ruleset_id,rule_name;') == p['rules_after']
        caches = {n:{'bytes':(ROOT/'data/server/shared'/n).stat().st_size,'sha256':sha(ROOT/'data/server/shared'/n)} for n in ('items','spells')}
        assert caches == expected_caches, 'Startup cache differs from exact candidate loader'
        assert all(v['bytes'] > 1000000 for v in caches.values())
        r.closed_ports(); assert not r.state('gateway')['State']['Running']
        save(EVIDENCE/'activated-closed.json',{'game':r.compact('game'),'runtime':current,
             'market':rotation,'caches':caches,'player_tables':len(data['player']),'custom_tables':len(data['custom'])})
        print('Runtime verified; access held for signed client.',flush=True)
    except BaseException:
        hold(); raise


def open_access():
    manifest(); p = load(EVIDENCE/'preflight.json'); a = load(EVIDENCE/'activated-closed.json')
    assert not list(EVIDENCE.glob('held-*.json')) and not (EVIDENCE/'opening.json').exists()
    published_client()
    try:
        assert not r.state('gateway')['State']['Running'] and r.compact('game') == a['game']
        assert saved_state() == load(EVIDENCE/'stopped-state.json')
        assert b.verify_market(load(EVIDENCE/'market-before.json'),a['runtime']['started_at']) == a['market']
        for n,record in a['caches'].items():
            assert sha(ROOT/'data/server/shared'/n) == record['sha256']
        untouched(p,True,True); health(); r.closed_ports()
        save(EVIDENCE/'opening.json',{'client_release':2026101902})
        r.compose('up','-d','--wait','--wait-timeout','60','gateway')
        assert r.state('gateway')['State']['Running']
        current = r.running(p['new_image_id'],binaries()); health(); r.closed_ports()
        assert current['started_at'] == a['runtime']['started_at']; untouched(p,True,True)
        save(EVIDENCE/'deployed.json',{**a,'runtime':current,'gateway_open':True,'client_release':2026101902,
             'database_restored':False,'owner_gameplay_accepted':False})
        print('Deployed with access open.',flush=True)
    except BaseException:
        hold(); raise


def initialize():
    global r, b
    manifest()
    for name,path in [('r','/opt/nightcap/releases/zone-hunt-20261009/runtime_ops.py'),('b',str(STAGE/'base_operator.py'))]:
        spec = importlib.util.spec_from_file_location(name,path)
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        globals()[name] = module
    r.STAGE = STAGE; r.EVIDENCE = EVIDENCE; r.sql = sql
    b.r = r; b.sql = sql


if __name__ == '__main__':
    assert __debug__; os.umask(0o077); initialize()
    parser = argparse.ArgumentParser(); parser.add_argument('action',choices=['preflight','activate','open'])
    action = parser.parse_args().action
    with (ROOT/'.deployment.lock').open('a') as lock, open('/var/lock/nightcap-gm.lock','a') as gm:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB); fcntl.flock(gm,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert not (ROOT/'private/gm-maintenance.json').exists() and sql("SELECT IS_FREE_LOCK('nightcap_gm_writes');").strip() == '1'
        {'preflight':preflight,'activate':activate,'open':open_access}[action]()
