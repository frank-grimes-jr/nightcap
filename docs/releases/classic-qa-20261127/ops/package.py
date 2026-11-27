"""Apply reviewed quest hunks to captured runtime files, preserving other lines."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

from capture import COUNT, HERE

ROOT = HERE.parents[3]
QUESTS = ('quests/fearplane/Cazic_Thule.lua', 'quests/global/global_player.lua')
PREDECESSOR = '34de795f61e495221d5fbc36e2240a96f694b10c68f70c4d8de9623571c805aa'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def merge_quest(old, new, active):
    stock, edited = (text.splitlines() for text in (old, new))
    raw = active.splitlines(keepends=True)
    current = [line.rstrip(b'\r\n') for line in raw]
    patches = []
    for group in difflib.SequenceMatcher(None, stock, edited, autojunk=False).get_grouped_opcodes(3):
        start, end = group[0][1], group[-1][2]
        matches = [pos for pos in range(len(current) - (end-start) + 1)
                   if current[pos:pos+end-start] == stock[start:end]]
        if len(matches) != 1:
            raise ValueError('Quest hunk absent or ambiguous on this runtime')
        for action, a, b, c, d in group:
            if action == 'equal':
                continue
            pos = matches[0]+a-start
            sample = raw[min(pos, len(raw)-1)]
            eol = b'\r\n' if sample.endswith(b'\r\n') else b'\n'
            patches.append((pos, pos+b-a, [s+eol for s in edited[c:d]]))
    if not patches:
        raise ValueError('No reviewed changes to quest')
    for pos, end, replacement in reversed(patches):
        raw[pos:end] = replacement
    return b''.join(raw)


def package(stage, binary, pin, base_ref, source_ref):
    capture = json.loads((stage/'capture.json').read_bytes())
    assert capture['binaries']['zone'] == PREDECESSOR
    for rev in (base_ref, source_ref):
        assert re.fullmatch('[0-9a-f]{40}', rev)
    assert re.fullmatch('[0-9a-f]{64}', pin) and sha(binary.read_bytes()) == pin != PREDECESSOR
    keys = {}
    for name in QUESTS:
        tracked = 'server-mods/'+name
        def blob(rev):
            return subprocess.check_output(['git', 'show', rev+':'+tracked], cwd=ROOT)
        active = (stage/'before'/name).read_bytes()
        assert sha(active) == capture['quests'][name]
        result = merge_quest(blob(base_ref), blob(source_ref), active)
        dst = stage/'after'/name
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(result)
        keys[name] = sha(result)
    shutil.copyfile(binary, stage/'zone')
    shutil.copyfile(COUNT, stage/'world_count.py')
    for name in ('release.py','probe.py','install_quests.py'):
        shutil.copyfile(HERE/name, stage/name)
    sql = [area+'-'+phase+'.sql' for area in ('recall','cazic') for phase in ('forward','rollback')]
    for name in sql:
        source = subprocess.check_output(['git', 'show', source_ref+':docs/releases/classic-qa-20261127/'+name], cwd=ROOT)
        (stage/name).write_bytes(source)
    packaged = ['release.py','probe.py','install_quests.py','world_count.py',*sql]
    record = dict(source=source_ref, base_source=base_ref, base_image=capture['image'],
                  base_tag=capture['image_ref'], binaries=capture['binaries'], cache=capture['cache'],
                  zone=pin, before=capture['quests'], after=keys,
                  operator={n:sha((stage/n).read_bytes()) for n in packaged})
    (stage/'manifest.json').write_text(json.dumps(record,indent=2)+'\n')
    return record


if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('stage',type=Path)
    p.add_argument('binary',type=Path)
    p.add_argument('pin')
    p.add_argument('base_ref')
    p.add_argument('source_ref')
    a=p.parse_args()
    print(json.dumps(package(a.stage,a.binary,a.pin,a.base_ref,a.source_ref),indent=2))

