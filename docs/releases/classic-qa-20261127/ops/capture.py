"""Capture LocalDev and OVH read-only release preimages into private staging."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
COUNT = HERE.parents[2]/'dungeons/readiness-20261106/deployment/world_count.py'
SSH = [str(Path('C:/Windows/System32/OpenSSH/ssh.exe')), '-i', str(Path.home()/'.ssh/nightcap_ovh'),
       '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', '-o', 'StrictHostKeyChecking=yes',
       'ubuntu@135.148.47.202']


def capture(target, stage):
    game = 'akk-stack-eqemu-server-1' if target == 'local' else 'nightcap-production-game-1'

    def docker(*args, data=None):
        import shlex
        command = ['docker', *args]
        if target == 'production':
            command = [*SSH, shlex.join(['sudo', '-n', *command])]
        return subprocess.check_output(command, input=data, timeout=180)

    state = json.loads(docker('exec', '-i', game, 'python3', '-', data=(HERE/'probe.py').read_bytes()))
    for name, encoded in state['quests'].items():
        raw = base64.b64decode(encoded, validate=True)
        path = stage/'before'/name
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and path.read_bytes() != raw:
            raise ValueError(f'Preimage changed since first capture: {name}')
        path.write_bytes(raw)
        state['quests'][name] = hashlib.sha256(raw).hexdigest()
    state['players'] = json.loads(docker('exec', '-i', game, 'python3', '-', data=COUNT.read_bytes()))
    state['image'] = docker('inspect', '--format', '{{.Image}}', game).decode().strip()
    state['image_ref'] = docker('inspect', '--format', '{{.Config.Image}}', game).decode().strip()
    state['health'] = docker('inspect', '--format', '{{.State.Health.Status}}', game).decode().strip()
    assert state['health'] == 'healthy'
    assert type(state['players']) is int and state['players'] >= 0
    print(json.dumps(state, indent=2))
    (stage/'capture.json').write_text(json.dumps(state, indent=2)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('target', choices=['production', 'local'])
    parser.add_argument('stage', type=Path)
    args = parser.parse_args()
    capture(args.target, args.stage)

