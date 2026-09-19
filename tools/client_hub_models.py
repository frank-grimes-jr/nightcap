"""Zone-local model imports. The archive codes are verified in EQEmu's race inventory."""
from pok_compact_hub import MODELS


def add_models(raw):
    lines = raw.decode('ascii').splitlines()
    if not lines or not lines[0].isdigit() or int(lines[0]) != len(lines)-1:
        raise ValueError('Invalid PoK model list count')
    entries = []
    seen = set()
    for line in lines[1:]:
        pair = line.lower().split(',')
        if len(pair) != 2 or any(not part or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789_' for c in part) for part in pair):
            raise ValueError('Invalid PoK model import')
        if pair[0] in seen:
            raise ValueError('Duplicate PoK model code')
        seen.add(pair[0]); entries.append(line)
    for model in MODELS.values():
        entry = model['model']+','+model['archive'].removesuffix('.eqg')
        if model['model'] in seen:
            if entry not in [line.lower() for line in entries]:
                raise ValueError('Conflicting hub model import')
        else:
            entries.append(entry); seen.add(model['model'])
    return (str(len(entries))+'\r\n'+'\r\n'.join(entries)+'\r\n').encode('ascii')
