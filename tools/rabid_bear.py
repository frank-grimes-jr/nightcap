"""Generate paired Rabid Bear content/client changes; never connect or install."""
import argparse
import gzip
import json
from pathlib import Path

ROOTS = (2750, 8216, 11279, 12644, 13795, 16668, 23599, 27493)
ILLUSION = 30709
ILLUSION_NAME = 'Illusion: Rabid Bear'
IDS = (*ROOTS, ILLUSION)


def changes(spell_id):
    result = {'buffdurationformula': 50, 'buffduration': 0, 'short_buff_box': 0}
    if spell_id == ILLUSION:
        result['name'] = ILLUSION_NAME
    return result


def validate(rows):
    selected = {r['id']: r for r in rows if r['id'] in IDS}
    if set(selected) != set(IDS):
        raise ValueError('Missing canonical Rabid Bear definitions')
    for sid, row in selected.items():
        if row['goodEffect'] != 1 or row['targettype'] != 6:
            raise ValueError('Expected beneficial self buff')
        if sid == ILLUSION:
            if row['effectid1'] != 58 or row['effect_base_value1'] != 43:
                raise ValueError('Expected independent bear illusion')
        elif row['effectid2'] != 374 or row['effect_limit_value2'] != ILLUSION:
            raise ValueError('Expected cast-time application of independent illusion')
    return selected


def sql_value(value):
    if value is None:
        return 'NULL'
    if isinstance(value, (int, float)):
        return str(value)
    return "CONVERT(X'" + str(value).encode('utf-8').hex() + "' USING utf8mb4)"


def predicate(row):
    return ' AND '.join('`' + k + '` <=> ' + sql_value(v) for k, v in row.items())


def migration(rows, rollback=False):
    selected = validate(rows)
    lines = ['DELIMITER //', 'CREATE PROCEDURE nightcap_rabid_bear_20261018()', 'BEGIN',
             ' DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;',
             ' START TRANSACTION;']
    for sid in IDS:
        original = selected[sid]
        after = {**original, **changes(sid)}
        before, target = (after, original) if rollback else (original, after)
        # Complete spell-row equality catches drift in proc/illusion mechanics too.
        lines += [f' IF NOT EXISTS (SELECT 1 FROM spells_new WHERE {predicate(target)}) THEN',
                  f'  IF NOT EXISTS (SELECT 1 FROM spells_new WHERE {predicate(before)} FOR UPDATE) THEN',
                  f"   SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rabid Bear {sid} preimage drift';", '  END IF;',
                  '  UPDATE spells_new SET ' + ','.join('`' + k + '`=' + sql_value(target[k]) for k in changes(sid)) +
                  f' WHERE id={sid};',
                  "  IF ROW_COUNT()<>1 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rabid Bear write count'; END IF;",
                  ' END IF;']
    lines += [' COMMIT;', 'END//', 'DELIMITER ;', 'CALL nightcap_rabid_bear_20261018();',
              'DROP PROCEDURE nightcap_rabid_bear_20261018;', '']
    return '\n'.join(lines)


def client_spells(raw):
    """Idempotent transform of the complete existing 237-field RoF2 file."""
    output, seen = [], set()
    for line in raw.decode('latin1').splitlines(keepends=True):
        ending = '\r\n' if line.endswith('\r\n') else '\n' if line.endswith('\n') else ''
        fields = (line[:-len(ending)] if ending else line).split('^')
        if len(fields) != 237:
            raise ValueError('Expected 237-field RoF2 spell row')
        sid = int(fields[0])
        if sid in IDS:
            if sid in seen:
                raise ValueError('Duplicate Rabid Bear spell')
            seen.add(sid)
            if fields[83] != '1' or fields[98] != '6' or fields[16] not in ('4', '50'):
                raise ValueError('Unexpected Rabid Bear spell policy')
            if sid == ILLUSION:
                if fields[86] != '58' or fields[20] != '43' or fields[1] not in ('Rabid Bear Effect', ILLUSION_NAME):
                    raise ValueError('Unexpected Rabid Bear illusion')
                fields[1] = ILLUSION_NAME
            elif fields[87] != '374' or fields[33] != str(ILLUSION) or fields[1] != 'Rabid Bear':
                raise ValueError('Unexpected Rabid Bear benefit/illusion link')
            fields[16], fields[17], fields[154] = '50', '0', '0'
        output.append('^'.join(fields) + ending)
    if seen != set(IDS):
        raise ValueError('Client is missing Rabid Bear definitions')
    return ''.join(output).encode('latin1')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    raw = args.snapshot.read_bytes()
    snapshot = json.loads(gzip.decompress(raw) if args.snapshot.suffix == '.gz' else raw)
    rows = snapshot['tables']['spells_new']
    args.output.mkdir(parents=True, exist_ok=True)
    for rollback in (False, True):
        (args.output / ('rabid-rollback.sql' if rollback else 'rabid-forward.sql')).write_text(
            migration(rows, rollback), encoding='utf-8', newline='\n')
    print(json.dumps({'status': 'generated_not_applied', 'spells': list(IDS)}))


if __name__ == '__main__':
    main()
