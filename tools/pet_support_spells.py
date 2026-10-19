"""Re-slot PoP pet buff lines so distinct classes coexist under native stacking."""
import argparse
import gzip
import json
from pathlib import Path
from rabid_bear import predicate, sql_value

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'tools/fixtures/pet-support-20261018.json.gz'
NECRO = (661, 1414, 3305)
BEASTLORD = (1430, 2619)
IDS = (*NECRO, *BEASTLORD)
FIELDS = ('effectid', 'effect_base_value', 'effect_limit_value', 'max', 'formula')


def fixture_rows():
    return json.loads(gzip.decompress(FIXTURE.read_bytes()))['tables']['spells_new']


def afterimage(row):
    if row['id'] not in IDS or row['targettype'] != 14 or row['goodEffect'] != 1:
        raise ValueError('Unexpected pet-support spell identity')
    moves = {3: 7, 4: 8, 6: 9} if row['id'] in NECRO else {3: 10, 4: 11, 5: 2, 6: 12}
    if (row['effectid3'], row['effectid4'], row['effectid6']) != (4, 11, 1):
        raise ValueError('Unexpected STR/haste/AC effects')
    result = dict(row)
    for old, new in moves.items():
        if row[f'effectid{new}'] not in (10, 254) or row[f'effect_base_value{new}'] != 0:
            raise ValueError('Destination effect slot is occupied')
        for prefix in FIELDS:
            result[f'{prefix}{new}'] = row[f'{prefix}{old}']
            result[f'{prefix}{old}'] = 254 if prefix == 'effectid' else 100 if prefix == 'formula' else 0
    return result


def migration(rows, rollback=False):
    selected = {r['id']: r for r in rows if r['id'] in IDS}
    if set(selected) != set(IDS):
        raise ValueError('Incomplete pet-support snapshot')
    lines = ['DELIMITER //', 'CREATE PROCEDURE nightcap_pet_support_20261018()', 'BEGIN',
             ' DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;', ' START TRANSACTION;']
    for sid in IDS:
        original = selected[sid]
        after = afterimage(original)
        before, target = (after, original) if rollback else (original, after)
        fields = [k for k in original if original[k] != after[k]]
        lines += [f' IF NOT EXISTS (SELECT 1 FROM spells_new WHERE {predicate(target)}) THEN',
                  f'  IF NOT EXISTS (SELECT 1 FROM spells_new WHERE {predicate(before)} FOR UPDATE) THEN',
                  f"   SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Pet support {sid} preimage drift';", '  END IF;',
                  '  UPDATE spells_new SET ' + ','.join('`'+k+'`='+sql_value(target[k]) for k in fields) + f' WHERE id={sid};',
                  "  IF ROW_COUNT()<>1 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Pet support write count'; END IF;", ' END IF;']
    lines += [' COMMIT;', 'END//', 'DELIMITER ;', 'CALL nightcap_pet_support_20261018();',
              'DROP PROCEDURE nightcap_pet_support_20261018;', '']
    return '\n'.join(lines)


def client_spells(raw):
    originals = {r['id']: r for r in fixture_rows() if r['id'] in IDS}
    output, seen = [], set()
    for line in raw.decode('latin1').splitlines(keepends=True):
        ending = '\r\n' if line.endswith('\r\n') else '\n' if line.endswith('\n') else ''
        fields = (line[:-len(ending)] if ending else line).split('^')
        if len(fields) != 237:
            raise ValueError('Expected 237-field RoF2 spell row')
        sid = int(fields[0])
        if sid in originals:
            if sid in seen:
                raise ValueError('Duplicate pet-support spell')
            seen.add(sid)
            original = originals[sid]
            target = afterimage(original)
            indices = {k: i for i, k in enumerate(original)}
            changed = [k for k in original if original[k] != target[k]]
            values = [fields[indices[k]] for k in changed]
            if fields[1] != original['name'] or values not in ([str(original[k]) for k in changed], [str(target[k]) for k in changed]):
                raise ValueError('Pet-support client preimage drift')
            for k in changed:
                fields[indices[k]] = str(target[k])
        output.append('^'.join(fields) + ending)
    if seen != set(IDS):
        raise ValueError('Client is missing pet-support spells')
    return ''.join(output).encode('latin1')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    for rollback in (False, True):
        (args.output / ('pet-support-rollback.sql' if rollback else 'pet-support-forward.sql')).write_text(
            migration(fixture_rows(), rollback), encoding='utf-8', newline='\n')


if __name__ == '__main__':
    main()
