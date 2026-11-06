"""One-shot production operation: remove NPC Death Touch. Execute over SSH stdin.

Template: @REMOVE_SQL@ / @QUEST_FILES@ are filled with remove.sql and the edited
quest files (old sha256 from the quests repo parent commit) before sending.
Closed access, verified stopped backup, guarded SQL, quest swap, healthy restart.
Never auto-restores a database; on uncertain mutation access stays closed.
"""
import base64, datetime, fcntl, gzip, hashlib, json, os, shutil, subprocess, time
from pathlib import Path

ROOT = Path('/opt/nightcap/deploy/production')
QUESTS = ROOT/'data/server/quests'
OUT = Path('/opt/nightcap/backups/no-death-touch-20261103')
DB = ['docker', 'compose', 'exec', '-T', 'db', 'mariadb',
      '--defaults-extra-file=/run/secrets/db_backup_config', '--batch', '--raw',
      '--skip-column-names', 'peq']
DT = '(982, 2859, 3087, 7477)'
PRESERVED = 'CHECKSUM TABLE inventory,character_data,character_currency,character_multiclass,zone_state_spawns;'
REMOVE_SQL = base64.b64decode('@REMOVE_SQL@').decode()
QUEST_FILES = json.loads(base64.b64decode('@QUEST_FILES@'))  # path -> [old sha256, new b64]
EXPECTED_ROWS = 17


def run(args, data=None, timeout=120):
    r = subprocess.run(args, cwd=ROOT, input=data, text=True, capture_output=True, timeout=timeout)
    if r.returncode:
        raise RuntimeError(r.stderr[-4000:])
    return r.stdout


def sql(q):
    return run(DB, q)


def save(name, data):
    (OUT/name).write_text(data if isinstance(data, str) else json.dumps(data, indent=2)+'\n')


def sha(b):
    return hashlib.sha256(b).hexdigest()


def fingerprint():
    return run(['docker', 'compose', 'exec', '-T', 'game', 'sha256sum',
                '/opt/nightcap/bin/world', '/opt/nightcap/bin/zone', '/opt/nightcap/bin/shared_memory'])


def start_and_wait():
    run(['docker', 'compose', 'start', 'game'])
    for _ in range(90):
        state = json.loads(run(['docker', 'inspect', 'nightcap-production-game-1']))[0]['State']
        if state.get('Health', {}).get('Status') == 'healthy':
            return state
        time.sleep(1)
    raise RuntimeError('Game did not become healthy; gateway remains stopped')


def backup():
    cmd = ['docker', 'compose', 'exec', '-T', 'db', 'mariadb-dump',
           '--defaults-extra-file=/run/secrets/db_backup_config', '--single-transaction',
           '--routines', '--triggers', '--events', 'peq']
    digest = hashlib.sha256(); tail = b''; has_inventory = False
    with (OUT/'dump.stderr').open('wb') as errors, gzip.open(OUT/'peq-before.sql.gz', 'wb') as stream:
        p = subprocess.Popen(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=errors)
        while chunk := p.stdout.read(1024*1024):
            has_inventory |= b'CREATE TABLE `inventory`' in tail+chunk
            tail = (tail+chunk)[-4096:]; digest.update(chunk); stream.write(chunk)
        assert p.wait(timeout=60) == 0, 'Backup command failed'
    assert has_inventory and b'Dump completed' in tail, 'Incomplete backup'
    verified = hashlib.sha256()
    with gzip.open(OUT/'peq-before.sql.gz', 'rb') as stream:
        while chunk := stream.read(1024*1024):
            verified.update(chunk)
    assert digest.digest() == verified.digest(), 'Backup verification failed'
    save('backup.json', dict(uncompressed_sha256=digest.hexdigest(), gzip_verified=True,
                             bytes=(OUT/'peq-before.sql.gz').stat().st_size))


def swap_quests():
    for rel, (old, new) in QUEST_FILES.items():
        p = QUESTS/rel; st = p.stat(); data = base64.b64decode(new)
        tmp = p.with_name(p.name+'.no-death-touch.tmp')
        tmp.write_bytes(data); os.chown(tmp, st.st_uid, st.st_gid); os.chmod(tmp, st.st_mode & 0o777)
        os.replace(tmp, p)
        assert sha(p.read_bytes()) == sha(data), rel


def apply():
    os.umask(0o077)
    with (ROOT/'.deployment.lock').open('a') as lock, open('/var/lock/nightcap-gm.lock', 'a') as gm:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        fcntl.flock(gm, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert not (ROOT/'private/gm-maintenance.json').exists()
        assert sql("SELECT IS_FREE_LOCK('nightcap_gm_writes');").strip() == '1'
        OUT.mkdir(mode=0o700, exist_ok=True)
        assert not (OUT/'activation-started').exists(), 'One-shot activation already started; inspect evidence'
        # Preflight: exact expected state, else touch nothing.
        assert sql(f'SELECT COUNT(*) FROM npc_spells_entries WHERE spellid IN {DT};').strip() == str(EXPECTED_ROWS)
        assert sql("SHOW TABLES LIKE 'nightcap_death_touch_backup_20261103';").strip() == ''
        for rel, (old, _) in QUEST_FILES.items():
            assert sha((QUESTS/rel).read_bytes()) == old, 'Quest drift: '+rel
        assert shutil.disk_usage(ROOT).free > 400*1024**2, 'Not enough disk for backup'
        for rel in QUEST_FILES:
            dst = OUT/'quests-before'/rel; dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(QUESTS/rel, dst)
        binaries = fingerprint(); save('native-before.sha256', binaries)
        touched = False
        try:
            (OUT/'activation-started').touch(exist_ok=False)
            run(['docker', 'compose', 'stop', 'gateway'])
            run(['docker', 'compose', 'stop', '-t', '90', 'game'], timeout=180)
            backup()
            preserved = sql(PRESERVED); save('preserved-before.txt', preserved)
            touched = True
            result = sql(REMOVE_SQL).split()
            assert result == [str(EXPECTED_ROWS), '0'], result
            assert sql(PRESERVED) == preserved, 'Player/zone state changed'
            swap_quests()
            state = start_and_wait()
            assert fingerprint() == binaries
            assert sql(f'SELECT COUNT(*) FROM npc_spells_entries WHERE spellid IN {DT};').strip() == '0'
            run(['docker', 'compose', 'start', 'gateway'])
            save('result.json', dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                 removed_rows=EXPECTED_ROWS, remaining=0, quests_replaced=sorted(QUEST_FILES),
                 native_hashes_unchanged=True, player_state_checksums_preserved=True,
                 runtime_started_at=state['StartedAt'], gateway='started', player_qa='pending'))
            print((OUT/'result.json').read_text(), flush=True)
        except Exception:
            if not touched:
                start_and_wait(); run(['docker', 'compose', 'start', 'gateway'])
            raise


apply()
