"""Read-only snapshot from inside the live game. Return only public scripts and hashes."""
import base64
import hashlib
import json
from pathlib import Path

game = Path('/srv/nightcap')
native = Path('/opt/nightcap/bin')
scripts = ('quests/fearplane/Cazic_Thule.lua', 'quests/global/global_player.lua')
binary_names = ('world', 'zone', 'ucs', 'loginserver', 'shared_memory')


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def snapshot():
    binaries = {name: digest(native/name) for name in binary_names}
    running = {}
    for proc in Path('/proc').glob('[0-9]*'):
        try:
            executable = (proc/'exe').readlink()
            if executable.name in binaries and executable.parent == native:
                assert digest(proc/'exe') == binaries[executable.name]
                running[executable.name] = running.get(executable.name, 0) + 1
        except (FileNotFoundError, ProcessLookupError):
            continue
    assert running == {'world': 1, 'zone': 12, 'ucs': 1, 'loginserver': 1}, running
    return {
        'binaries': binaries, 'running': running,
        'cache': {name: digest(game/'shared'/name) for name in ('items', 'spells')},
        'quests': {name: base64.b64encode((game/name).read_bytes()).decode() for name in scripts},
    }


if __name__ == '__main__':
    print(json.dumps(snapshot()))

