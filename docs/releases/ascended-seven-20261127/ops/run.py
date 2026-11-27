"""Package, stage and collect the paired zone/rule deployment using the prior release primitives."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tarfile
import tempfile

HERE = Path(__file__).resolve().parent
PREVIOUS = HERE.parents[1]/'classic-qa-20261127/ops'
sys.path.insert(0, str(PREVIOUS))
from capture import SSH, COUNT
from upload import INSTALL
from runtime_errors import PATTERNS

NAME = 'ascended-seven-20261127'
PRIVATE = Path('E:/EQ_Local_Dev/artifacts')/NAME/'ops'
REMOTE_ROOT = '/opt/nightcap/releases/' + NAME + '-'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def read(path):
    return json.loads(path.read_bytes())


def make(target, stage, binary, digest, source):
    capture = read(stage/'capture.json')
    prior = read(PREVIOUS/(target+'-verified.json'))
    for key in ('image', 'binaries', 'quests', 'cache', 'running'):
        assert capture[key] == prior[key], key
    assert re.fullmatch('[0-9a-f]{40}', source)
    assert sha(binary) == digest and digest != capture['binaries']['zone']
    shutil.copyfile(binary, stage/'zone')
    shutil.copyfile(HERE/'release.py', stage/'release.py')
    shutil.copyfile(PREVIOUS/'probe.py', stage/'probe.py')
    shutil.copyfile(COUNT, stage/'world_count.py')
    # Keep the proven snapshot, world, backup and compose primitives. Change
    # only the archive directory so the inherited dump stays with this release.
    original = (PREVIOUS/'release.py').read_bytes()
    archive = b'/mnt/archive/classic-qa-20261127'
    assert original.count(archive) == 1
    (stage/'common.py').write_bytes(original.replace(archive, b'/mnt/archive/ascended-seven-20261127'))
    names = ('release.py', 'probe.py', 'world_count.py', 'common.py')
    m = {key: capture[key] for key in ('binaries', 'quests', 'cache')}
    m.update(base_image=capture['image'], base_tag=capture['image_ref'], source=source,
             zone=digest, operator={name:sha(stage/name) for name in names})
    save(stage/'manifest.json', m)


def remote(*args, data=None):
    return subprocess.check_output([*SSH, shlex.join(['sudo', '-n', *args])], input=data, timeout=1200)


def upload(stage, dest):
    pin = sha(stage/'manifest.json')
    names = ['manifest.json', 'zone', *read(stage/'manifest.json')['operator']]
    with tempfile.TemporaryFile() as stream:
        with tarfile.open(fileobj=stream, mode='w:gz', compresslevel=2) as archive:
            for name in names:
                archive.add(stage/name, arcname=name, recursive=False)
        stream.seek(0)
        install = INSTALL.replace('classic-qa-20261127-', NAME+'-')
        command = shlex.join(['sudo','-n','python3','-c',install,pin,*names])
        output = subprocess.check_output([*SSH,command], stdin=stream, timeout=300)
        assert output.decode().strip() == dest


def receipt(target, stage, dest):
    def entry(name):
        if target == 'local':
            return read(stage/(name + '.json'))
        return json.loads(remote('cat', dest + '/' + name + '.json'))
    result = entry('activation-complete')
    m = read(stage/'manifest.json')
    prep = entry('prepared')
    assert prep['manifest'] == sha(stage/'manifest.json') and result['source'] == m['source']
    assert result['admission_open'] and prep['image'] == result['image']
    result.update(previous_image=m['base_image'], backup_sha256=entry('activation-backup')['sha256'],
                  prepared=prep, stage=(str(stage) if target == 'local' else dest), player_qa='pending')
    script = """
import json,re,subprocess,sys
game=sys.argv[1]
d=json.loads(subprocess.check_output(['docker','inspect',game]))[0]
log=subprocess.check_output(['docker','logs','--since',d['State']['StartedAt'],game],stderr=subprocess.STDOUT)
counts={key:len(re.findall(value.encode(),log,re.I)) for key,value in json.loads(sys.argv[2]).items()}
print(json.dumps(dict(health=d['State']['Health']['Status'],restarts=d['RestartCount'],errors=counts)))
"""
    if target == 'local':
        logs = subprocess.check_output([sys.executable,'-c',script,'akk-stack-eqemu-server-1',json.dumps(PATTERNS)])
    else:
        assert remote('docker','inspect','--format','{{.State.Running}}','nightcap-production-gateway-1').strip() == b'true'
        logs = remote('python3','-c',script,'nightcap-production-game-1',json.dumps(PATTERNS))
    result['post_boot'] = json.loads(logs)
    assert result['post_boot']['health'] == 'healthy' and result['post_boot']['restarts'] == 0
    assert not any(result['post_boot']['errors'].values())
    save(HERE/(target+'-verified.json'), result)
    print(json.dumps(result))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('target', choices=('local','production'))
    p.add_argument('action', choices=('package','upload','prepare','activate','verify','rollback','receipt'))
    p.add_argument('binary', type=Path, nargs='?')
    p.add_argument('digest', nargs='?')
    p.add_argument('source', nargs='?')
    a = p.parse_args()
    stage = PRIVATE/a.target
    if a.action == 'package':
        make(a.target, stage, a.binary, a.digest, a.source)
    else:
        dest = REMOTE_ROOT + sha(stage/'manifest.json')[:12]
        if a.action == 'upload':
            assert a.target == 'production'
            upload(stage, dest)
        elif a.action == 'receipt':
            receipt(a.target, stage, dest)
        elif a.target == 'local':
            subprocess.run([sys.executable, '-B', stage/'release.py', a.action], check=True)
        else:
            print(remote('python3', '-B', dest+'/release.py', a.action).decode().strip())
