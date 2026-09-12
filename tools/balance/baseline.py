"""Read-only reconciliation checks; never repairs or restarts a server."""
import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path


EXPECTED_RULES = {
    'Character:AAExpMinLevel': '1',
    'Character:ItemSpellDmgCap': '250',
    'Character:ItemHealAmtCap': '250',
    'Spells:ItemExtraSpellAmtCalcAsPercent': 'true',
    'Spells:FlatItemExtraSpellAmt': 'true',
    'Spells:IgnoreSpellDmgLvlRestriction': 'true',
    'Spells:DOTsScaleWithSpellDmg': 'true',
    'Spells:HOTsScaleWithHealAmt': 'true',
    'Spells:DOTBonusDamageSplitOverDuration': 'true',
    'Spells:HOTBonusHealingSplitOverDuration': 'true',
}


def validate_cpp_summary(output, returncode):
    matches = re.findall(r'Total: (\d+) tests, (\d+)% correct', output)
    if returncode or len(matches) != 1 or int(matches[0][0]) == 0 or matches[0][1] != '100':
        raise ValueError('C++ suite did not report one complete, nonempty 100% passing run')
    return int(matches[0][0])


def validate_rules(actual, expected):
    return {key: {'expected': value, 'actual': actual.get(key)}
            for key, value in expected.items() if actual.get(key) != value}


def normalized_hash(path):
    return hashlib.sha256(path.read_bytes().replace(b'\r\n', b'\n')).hexdigest()


def compare_mirror(mirror, runtime):
    files = sorted(path for path in mirror.rglob('*') if path.is_file())
    if not files:
        raise ValueError('Mirror is empty or missing')
    result = {'checked': len(files), 'missing': [], 'mismatches': [], 'sha256_lf': {}}
    for path in files:
        relative = path.relative_to(mirror)
        key = relative.as_posix()
        live = runtime / relative if relative.parts[0] == 'code' else runtime / 'server' / relative
        result['sha256_lf'][key] = normalized_hash(path)
        if not live.is_file():
            result['missing'].append(key)
        elif normalized_hash(path) != normalized_hash(live):
            result['mismatches'].append(key)
    return result


def query_json(sql):
    """Execute fixed SELECT queries in one read-only transaction, one JSON row per line."""
    result = subprocess.run([
        'docker', 'exec', 'akk-stack-mariadb-1', 'mysql', '-ueqemu', '-peqemu',
        'peq', '--batch', '--raw', '--skip-column-names', '-e',
        'START TRANSACTION READ ONLY; ' + sql + '; COMMIT;'
    ], capture_output=True, text=True, encoding='utf-8', check=True)
    return [json.loads(line) for line in result.stdout.splitlines() if line.strip()]


def database_checks():
    rule_rows = query_json("SELECT JSON_OBJECT('name',rule_name,'value',rule_value) FROM rule_values WHERE ruleset_id=1")
    rules = {row['name']: row['value'] for row in rule_rows}
    tiers = []
    # Check every existing worn variant, including items with nonzero base bonuses.
    for offset, multiplier, stamp in ((200000, '1.10', 5), (400000, '1.20', 12),
                                      (600000, '1.35', 20), (800000, '1.35', 20)):
        upper = offset + (99999 if offset == 800000 else 199999)
        row = query_json(f"""SELECT JSON_OBJECT('offset',{offset},'items',COUNT(*),
            'mismatches',COALESCE(SUM(
                a.spelldmg <> IF(b.spelldmg>0,ROUND(b.spelldmg*{multiplier}),b.spelldmg)+{stamp}
                OR a.healamt <> IF(b.healamt>0,ROUND(b.healamt*{multiplier}),b.healamt)+{stamp}
            ),0)) FROM items a JOIN items b ON b.id=a.id-{offset}
            WHERE a.id BETWEEN {offset+1} AND {upper} AND a.slots>0""")[0]
        tiers.append(row)
    return {'rules': {key: rules.get(key) for key in EXPECTED_RULES},
            'rule_mismatches': validate_rules(rules, EXPECTED_RULES), 'tier_stamps': tiers}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path, required=True, help='Active akk-stack directory')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--database', action='store_true')
    parser.add_argument('--cpp-tests', action='store_true')
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[2]
    mirror = compare_mirror(repo / 'server-mods', args.runtime)
    report = {'captured_at': datetime.now(timezone.utc).isoformat(), 'mirror': mirror}
    failures = bool(mirror['missing'] or mirror['mismatches'])
    if args.database:
        report['database'] = database_checks()
        failures |= bool(report['database']['rule_mismatches'])
        failures |= any(row['items'] == 0 or row['mismatches'] for row in report['database']['tier_stamps'])
    if args.cpp_tests:
        result = subprocess.run(['docker', 'exec', '-w', '/home/eqemu/server',
                                 'akk-stack-eqemu-server-1', '/home/eqemu/code/build/bin/tests'],
                                capture_output=True, text=True, encoding='utf-8')
        try:
            report['cpp_tests'] = {'passed': validate_cpp_summary(result.stdout, result.returncode)}
        except ValueError as error:
            failures = True
            report['cpp_tests'] = {'error': str(error), 'output': result.stdout, 'stderr': result.stderr}
    report['passed'] = not failures
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: value for key, value in report.items() if key != 'mirror'}, indent=2))
    print(f'Mirror: {mirror["checked"]} checked; {len(mirror["mismatches"])} mismatched; {len(mirror["missing"])} missing')
    return int(failures)


if __name__ == '__main__':
    raise SystemExit(main())
