"""Replace only the packaged Lua scripts on the stopped game's data volume."""
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path('/srv/nightcap')
ALLOW = {'quests/global/global_player.lua', 'quests/fearplane/Cazic_Thule.lua'}


def install(request):
    assert set(request) == ALLOW
    changes = []
    for name, row in request.items():
        destination = ROOT/name
        assert destination.resolve() == destination and destination.is_file()
        old = destination.read_bytes()
        actual = hashlib.sha256(old).hexdigest()
        new = base64.b64decode(row['data'], validate=True)
        assert hashlib.sha256(new).hexdigest() == row['want']
        assert actual in (row['from'], row['want']), name
        if actual != row['want']:
            changes.append((destination, old, new))
    for destination, old, new in changes:
        st = destination.stat()
        with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as tmp:
            tmp.write(new)
            tmp.flush()
            os.fsync(tmp.fileno())
            os.fchown(tmp.fileno(), st.st_uid, st.st_gid)
            os.fchmod(tmp.fileno(), st.st_mode & 0o777)
        try:
            subprocess.run(['luac','-p',tmp.name],check=True)
            assert destination.read_bytes() == old
            os.replace(tmp.name, destination)
        finally:
            Path(tmp.name).unlink(missing_ok=True)


if __name__ == '__main__':
    install(json.loads(sys.stdin.buffer.read()))

