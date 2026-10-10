"""Run on OVH with HELPER_SOURCE supplied by the trusted test driver on stdin.

Only fixed, labeled QA containers are changed. Production is inspected for the
runtime image and a before/after start-time comparison.
"""
import base64
import gzip
import json
from pathlib import Path
import subprocess
import tempfile
import time
import types

NAME = 'nightcap-gm-qa-20261010'
LABEL = 'nightcap.gm-fixture=20261010'
def run(*args, input=None):
    return subprocess.check_output(args, input=input, text=True, stderr=subprocess.DEVNULL).strip()
def snapshot():
    rows = json.loads(run('docker', 'inspect', 'nightcap-production-game-1', 'nightcap-production-gateway-1', 'nightcap-production-db-1', 'nightcap-production-web-1', 'nightcap-production-tunnel-1'))
    return {r['Name']: {'id': r['Id'], 'started': r['State']['StartedAt'], 'running': r['State']['Running']} for r in rows}

baseline = snapshot()
game_image = run('docker', 'inspect', '--format', '{{.Image}}', 'nightcap-production-game-1')
module = types.ModuleType('gm_rehearsal')
exec(HELPER_SOURCE, module.__dict__)
created = []
with tempfile.TemporaryDirectory(prefix='nightcap-gm-rehearsal-') as tmp:
    module.ROOT = Path(tmp)
    (module.ROOT / 'private').mkdir(mode=0o700)
    module.MAINTENANCE = module.ROOT / 'private/gm-maintenance.json'
    module.REGISTRY = module.ROOT / 'private/missing-registry.json'
    module.CONTAINERS = {'game': NAME + '-game', 'db': NAME, 'gateway': NAME + '-gateway'}
    try:
        fixture = json.loads(run('docker', 'inspect', NAME))[0]
        assert fixture['Config']['Labels']['nightcap.gm-fixture'] == '20261010'
        for role in ('game', 'gateway'):
            name = module.CONTAINERS[role]
            run('docker', 'run', '-d', '--name', name, '--label', LABEL, '--network', 'none', '--read-only', '--cap-drop', 'ALL',
                '--memory', '128m', '--cpus', '.25', '--tmpfs', '/tmp:rw,size=16m', '--health-cmd', 'true', '--health-interval', '1s',
                '--entrypoint', 'python3', game_image, '-c', 'import time; time.sleep(600)')
            created.append(name)
        run('docker', 'exec', NAME, 'mariadb', '-uroot', '-pgm-fixture-only', '-e', 'CREATE DATABASE IF NOT EXISTS peq; CREATE TABLE IF NOT EXISTS peq.gm_probe(id INT PRIMARY KEY); INSERT IGNORE INTO peq.gm_probe VALUES (1)')
        run('docker', 'exec', '-i', NAME, 'sh', '-c', 'mkdir -p /run/secrets; umask 077; cat > /run/secrets/db_backup_config', input='[client]\nuser=root\npassword=gm-fixture-only\n')
        time.sleep(2)
        stopped = module.maintenance(True)
        assert stopped['maintenance'] and stopped['maintenance_active']
        module.require_offline()
        backup = module.backup()
        with gzip.open(module.ROOT / 'private/gm-backups' / backup, 'rt') as data:
            assert 'gm_probe' in data.read()
        # A live database fence must keep the runtime stopped.
        fence = subprocess.Popen(['docker', 'exec', NAME, 'mariadb', '-uroot', '-pgm-fixture-only', '-N', '-e', "SELECT GET_LOCK('nightcap_gm_writes',0); SELECT SLEEP(4)"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)
        try:
            module.maintenance(False)
            raise AssertionError('Resume ignored database fence')
        except ValueError as error:
            assert 'database action' in str(error)
        assert module.status()['maintenance']
        fence.wait(timeout=10)
        resumed = module.maintenance(False)
        assert resumed['game_running'] and resumed['gateway_running'] and not resumed['maintenance_active']
        assert snapshot() == baseline
        print(json.dumps({'maintenance_shutdown': True, 'backup_gzip_verified': True, 'database_fence_prevents_resume': True, 'health_gated_resume': True, 'production_containers_unchanged': True}))
    finally:
        for name in created:
            details = json.loads(run('docker', 'inspect', name))[0]
            assert details['Config']['Labels']['nightcap.gm-fixture'] == '20261010' and name in (NAME + '-game', NAME + '-gateway')
            run('docker', 'rm', '-f', name)
