"""Disposable, isolated GM database fixture. Never attaches to production networks."""
import json
import subprocess
import sys
import time

NAME = 'nightcap-gm-qa-20261010'
LABEL = 'nightcap.gm-fixture=20261010'

def run(*args):
    return subprocess.check_output(args, text=True, stderr=subprocess.DEVNULL).strip()

def remove():
    for resource in ('container', 'network'):
        found = run('docker', resource, 'ls', '-q', '--filter', 'label=' + LABEL)
        for resource_id in found.splitlines():
            details = json.loads(run('docker', resource, 'inspect', resource_id))[0]
            name = details['Name'].lstrip('/')
            if name != NAME: raise RuntimeError('Fixture identity mismatch')
            args = ['docker', resource, 'rm']
            if resource == 'container': args.append('-f')
            run(*args, resource_id)

if sys.argv[-1] == 'cleanup':
    remove()
    print(json.dumps({'removed': NAME}))
else:
    image = run('docker', 'inspect', '--format', '{{.Image}}', 'nightcap-production-db-1')
    if run('docker', 'ps', '-aq', '--filter', 'name=^/' + NAME + '$'):
        raise RuntimeError('Fixture already exists; inspect or clean it before starting')
    run('docker', 'network', 'create', '--internal', '--label', LABEL, NAME)
    try:
        run('docker', 'run', '-d', '--name', NAME, '--label', LABEL, '--network', NAME,
            '--memory', '512m', '--cpus', '1', '--tmpfs', '/var/lib/mysql:rw,size=256m',
            '-e', 'MARIADB_ROOT_PASSWORD=gm-fixture-only', '-e', 'MARIADB_ROOT_HOST=%', image)
        for _ in range(90):
            try:
                run('docker', 'exec', NAME, 'mariadb', '-uroot', '-pgm-fixture-only', '-N', '-e', 'SELECT 1')
                break
            except subprocess.CalledProcessError: time.sleep(1)
        else: raise RuntimeError('Fixture database did not become ready')
        details = json.loads(run('docker', 'inspect', NAME))[0]
        assert list(details['NetworkSettings']['Networks']) == [NAME]
        assert not details['HostConfig']['PortBindings']
        print(json.dumps({'name': NAME, 'host': details['NetworkSettings']['Networks'][NAME]['IPAddress'], 'port': 3306}))
    except Exception:
        remove()
        raise
