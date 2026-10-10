"""Fixed owner operations over authenticated SSH stdin; no public listener.

REQUEST is decoded by the trusted caller. Never include secrets in diagnostics.
"""
import datetime
import fcntl
import gzip
import ipaddress
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path('/opt/nightcap/deploy/production')
REGISTRY = ROOT / 'private/player-access/credentials.json'
MAINTENANCE = ROOT / 'private/gm-maintenance.json'
CONTAINERS = {role: 'nightcap-production-' + role + '-1' for role in ('game', 'db', 'gateway')}


def containers():
    raw = subprocess.check_output(['docker', 'inspect', *CONTAINERS.values()], timeout=10)
    roles = {name: role for role, name in CONTAINERS.items()}
    return {roles[x['Name'].lstrip('/')]: x for x in json.loads(raw)}


def status():
    state = containers()
    env = state['gateway']['Config']['Env'] or []
    active = 'PLAYER_ACCESS_FILE=/run/nightcap-access/credentials.json' in env
    return {'environment': 'production', 'label': 'OVH production',
            'game_running': state['game']['State']['Running'],
            'gateway_running': state['gateway']['State']['Running'],
            'access_registry_ready': REGISTRY.is_file(), 'credential_gateway_active': active,
            'maintenance_active': MAINTENANCE.is_file(),
            'maintenance': MAINTENANCE.is_file() and not state['game']['State']['Running'] and not state['gateway']['State']['Running']}


def require_offline():
    state = status()
    if not state['maintenance']:
        raise ValueError('Start maintenance in the GM tool before editing game data. This disconnects all players.')


def backup(tables=None):
    allowed = {'login_accounts', 'account', 'character_data', 'character_currency', 'character_skills',
               'character_multiclass', 'rule_values', 'variables', 'gm_progression_kills', 'merchantlist'}
    if tables is not None and (not isinstance(tables, list) or not tables or any(t not in allowed for t in tables)):
        raise ValueError('Unsupported backup scope')
    directory = ROOT / 'private/gm-backups'
    directory.mkdir(mode=0o700, exist_ok=True)
    os.chmod(directory, 0o700)
    name = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ') + '.sql.gz'
    path = directory / (name + '.partial')
    with path.open('xb') as target:
        os.chmod(path, 0o600)
        with gzip.GzipFile(fileobj=target, mode='wb') as output:
            proc = subprocess.Popen(['docker', 'exec', CONTAINERS['db'], 'mariadb-dump',
                '--defaults-extra-file=/run/secrets/db_backup_config', '--single-transaction', '--quick',
                '--routines', '--events', '--triggers', 'peq', *(tables or [])], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            import threading
            timer = threading.Timer(180, proc.kill)
            timer.start()
            try:
                import shutil
                shutil.copyfileobj(proc.stdout, output)
                if proc.wait(timeout=180) != 0:
                    raise ValueError('Database backup failed; no GM change was made')
            finally:
                timer.cancel()
                if proc.poll() is None: proc.kill()
        target.flush()
        os.fsync(target.fileno())
    if path.stat().st_size < 100:
        raise ValueError('Database backup was empty; no GM change was made')
    path.rename(directory / name)
    return name


def maintenance(start):
    state = status()
    if start:
        if not MAINTENANCE.exists():
            if not state['game_running'] or not state['gateway_running']:
                raise ValueError('Runtime is already partly stopped. Resolve its state before starting maintenance.')
            fd = os.open(MAINTENANCE, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, 'w') as output:
                json.dump({'started': datetime.datetime.now(datetime.timezone.utc).isoformat()}, output)
                output.flush(); os.fsync(output.fileno())
        # Stop the whole supervised runtime. Never kill an individual zone.
        subprocess.run(['docker', 'stop', '-t', '20', CONTAINERS['gateway']], check=True, capture_output=True, timeout=30)
        subprocess.run(['docker', 'stop', '-t', '100', CONTAINERS['game']], check=True, capture_output=True, timeout=115)
        require_offline()
    else:
        if not MAINTENANCE.exists():
            raise ValueError('No GM maintenance session to resume')
        # Every SQL writer takes this connection-scoped fence before its SSH lease.
        # If SSH drops, an in-flight query/transaction still holds the fence until
        # rollback/commit completes. Do not start native saves over that work.
        free = subprocess.check_output(['docker', 'exec', CONTAINERS['db'], 'mariadb',
            '--defaults-extra-file=/run/secrets/db_backup_config', '-N', '-e',
            "SELECT IS_FREE_LOCK('nightcap_gm_writes')"], text=True, timeout=10).strip()
        if free != '1': raise ValueError('A GM database action is still in progress. Wait before resuming the game.')
        subprocess.run(['docker', 'start', CONTAINERS['game']], check=True, capture_output=True, timeout=20)
        import time
        for _ in range(90):
            game = containers()['game']
            if game['State'].get('Health', {}).get('Status') == 'healthy': break
            time.sleep(1)
        else: raise ValueError('Game did not become healthy; gateway stays closed. Retry Resume after checking runtime health.')
        subprocess.run(['docker', 'start', CONTAINERS['gateway']], check=True, capture_output=True, timeout=20)
        if not status()['gateway_running']: raise ValueError('Gateway did not start; maintenance remains active')
        MAINTENANCE.unlink()
    return status()


def connection():
    state = containers()
    shared = set(state['game']['NetworkSettings']['Networks']) & set(state['db']['NetworkSettings']['Networks'])
    if len(shared) != 1:
        raise ValueError('Unexpected production database network')
    network = shared.pop()
    host = state['db']['NetworkSettings']['Networks'][network]['IPAddress']
    if network != 'nightcap-production_database' or not any(ipaddress.ip_address(host) in ipaddress.ip_network(cidr) for cidr in ('10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16')):
        raise ValueError('Unexpected production database network')
    db = json.loads((ROOT / 'private/eqemu_config.json').read_text())['server']['database']
    if db['db'] != 'peq' or int(db['port']) != 3306:
        raise ValueError('Unexpected production database identity')
    return {'host': host, 'port': 3306, 'user': db['username'], 'password': db['password'], 'database': 'peq'}


def password_mode():
    config = json.loads((ROOT / 'private/login.json').read_text())
    mode = config.get('security', {}).get('mode', 14)
    if mode != 14:
        raise ValueError('The deployed login hash mode changed; review it before resetting passwords')
    return {'mode': mode}


def access_module():
    # Deployed with the reviewed access package. No request chooses this path.
    sys.path.insert(0, str(ROOT))
    import player_access
    return player_access


def execute(request):
    operation = request.get('operation')
    expected = {'connection': set(), 'status': set(), 'password_mode': set(),
                'access_list': set(), 'access_issue': {'player'},
                'access_revoke': {'credential_id'}, 'access_initialize': set(),
                'maintenance_start': set(), 'maintenance_end': set(), 'lease': {'offline', 'backup', 'tables'}}
    if operation not in expected or set(request) != {'operation'} | expected[operation]:
        raise ValueError('Unsupported production request')
    if operation == 'connection':
        return connection()
    if operation == 'status':
        return status()
    if operation == 'password_mode':
        return password_mode()
    if operation in ('maintenance_start', 'maintenance_end'):
        return maintenance(operation == 'maintenance_start')
    if operation == 'lease':
        if request['offline']: require_offline()
        receipt = backup(request['tables']) if request['backup'] else None
        if request['offline']: require_offline()
        return {'backup': receipt}
    if operation == 'access_list' and not REGISTRY.is_file():
        return {'ready': False, 'credentials': []}
    access = access_module()
    if operation == 'access_initialize':
        access.initialize(REGISTRY, 65532)
        return {'initialized': True, 'credential_gateway_active': status()['credential_gateway_active']}
    if operation == 'access_list':
        if not REGISTRY.is_file():
            return {'ready': False, 'credentials': []}
        with access.locked(REGISTRY):
            rows = access.read_registry(REGISTRY)['credentials']
        return {'ready': True, 'credentials': [{k: r[k] for k in ('id', 'player', 'created')} for r in rows]}
    if operation == 'access_revoke':
        return access.revoke(REGISTRY, request['credential_id'])
    # Keep the private delivery file if a response is lost. Nothing writes a code
    # into stdout except this explicit authenticated operator issuance response.
    delivery = ROOT / 'private/gm-delivery'
    delivery.mkdir(mode=0o700, exist_ok=True)
    os.chmod(delivery, 0o700)
    import secrets
    path = delivery / (secrets.token_hex(16) + '.txt')
    issued = access.issue(REGISTRY, request['player'], path)
    return {k: issued[k] for k in ('id', 'player', 'created')} | {'code': path.read_text().strip()}


if __name__ == '__main__':
    try:
        if 'REQUEST' not in globals(): REQUEST = json.loads(sys.stdin.readline(16385))
        with open('/var/lock/nightcap-gm.lock', 'a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            answer = execute(REQUEST)
            print(json.dumps({'ok': True, 'result': answer}), flush=True)
            if REQUEST.get('operation') == 'lease': sys.stdin.readline(16)
    except ValueError as exc:
        print(json.dumps({'ok': False, 'error': str(exc)}))
    except Exception:
        print(json.dumps({'ok': False, 'error': 'Production operation unavailable; verify the reviewed admin helper and server state.'}))
