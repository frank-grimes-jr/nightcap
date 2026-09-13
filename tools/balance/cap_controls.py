"""Matched native cap experiments in the isolated clone; never a live installer."""
import copy
from collections import defaultdict
import re
import subprocess
from uuid import uuid4

from aa_policy_preflight import read_json
from release_pool_controls import verify as verify_pool
from run_aa_projection import DATABASE, DOCS, RUNTIME, SERVER, command, sql, write


VARIANTS = {'healing300': (250, 300), 'damage300': (300, 250), 'both300': (300, 300)}
RULES = ('Character:ItemSpellDmgCap', 'Character:ItemHealAmtCap')


def prepare(source, binary):
    matrix = copy.deepcopy(source)
    selected = {a['key'] for a in source['allocations']
                if a['spent'] == 0 or any(s['requested'] == 'all' for s in a['aliases'])}
    matrix['cases'] = [c for c in matrix['cases'] if c['allocation_key'] in selected]
    coordinates = [(c['allocation_key'], c['seed'],
                    c['input'].get('encounter', c['input'].get('pet_probe', {}).get('combat'))['npc_id'])
                   for c in matrix['cases']]
    if len(selected) != 9 or len(coordinates) != 54 or len(set(coordinates)) != 54:
        raise ValueError('Expected nine allocations, two bosses and three seeds')
    for key in selected:
        if {(seed, boss) for allocation, seed, boss in coordinates if allocation == key} != {
                (seed, boss) for seed in (1729, 1730, 1731) for boss in (32040, 73057)}:
            raise ValueError('Incomplete paired cap experiment')
    matrix['binary_sha256'] = binary
    matrix['scope'] = 'Matched cap sensitivity: zero, launch maximum and later maximum; fixed source gear, purchases, preparation and NPC data.'
    return matrix


def rule_sql(before, after, procedure):
    if not re.fullmatch(r'cap_[a-z0-9_]{1,55}', procedure):
        raise ValueError('Invalid procedure name')
    if any(type(v) is not int or v not in (250, 300) for pair in (before, after) for v in pair) or any(len(p) != 2 for p in (before, after)):
        raise ValueError('Only the paired 250/300 cap experiment is supported')
    lines = ['DELIMITER //', f'CREATE PROCEDURE `{procedure}`()', 'BEGIN',
             ' DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;',
             ' START TRANSACTION;',
             f" IF DATABASE() <> '{DATABASE}' THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Wrong database'; END IF;",
             " IF EXISTS(SELECT 1 FROM account) OR EXISTS(SELECT 1 FROM character_data) OR EXISTS(SELECT 1 FROM character_alternate_abilities) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Nonempty character fixture'; END IF;",
             " IF (SELECT COUNT(*) FROM rule_values WHERE rule_name IN ('Character:ItemSpellDmgCap','Character:ItemHealAmtCap')) <> 2 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Unexpected cap rule rows'; END IF;"]
    for name, old, new in zip(RULES, before, after):
        lines.append(f" IF (SELECT COUNT(*) FROM rule_values WHERE ruleset_id=1 AND rule_name='{name}' AND rule_value='{old}') <> 1 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Cap precondition changed'; END IF;")
        if old != new:
            lines.append(f" UPDATE rule_values SET rule_value='{new}' WHERE ruleset_id=1 AND rule_name='{name}' AND rule_value='{old}';")
    return '\n'.join(lines + [' COMMIT;', 'END//', f'CALL `{procedure}`()//', f'DROP PROCEDURE `{procedure}`//', 'DELIMITER ;']) + '\n'


def verify(matrix, evidence, baseline, variant, catalog):
    expected_damage, expected_heal = VARIANTS[variant]
    summaries = verify_pool(matrix, evidence, catalog)
    old = {r['id']: r for r in baseline['runs']}
    for run in evidence['runs']:
        player = copy.deepcopy(run['report']['builds'][0])
        original = old[run['id']]['report']['builds'][0]
        if player['spell_damage'] != expected_damage or player['heal_amount'] != expected_heal:
            raise ValueError('Native effective caps differ from experiment')
        player.update(spell_damage=250, heal_amount=250)
        if player != original:
            raise ValueError('Non-cap build state changed')
    groups = defaultdict(list)
    for result in summaries:
        groups[(result['profile'], result['aa_spent'], result['npc_id'])].append(result)
    return [{'profile': p, 'aa_spent': aa, 'npc_id': boss, 'wins': sum(r['won'] for r in rows),
             'samples': len(rows), 'elapsed_seconds_range': [min(r['elapsed_ms'] for r in rows)/1000,
                                                           max(r['elapsed_ms'] for r in rows)/1000],
             'minimum_hp_percent_range': [min(r['minimum_hp_percent'] for r in rows),
                                          max(r['minimum_hp_percent'] for r in rows)]}
            for (p, aa, boss), rows in sorted(groups.items())]


def run():
    output = DOCS / 'cap-experiment-checks.json'
    if output.exists() or any((DOCS / f'cap-{v}.json.gz').exists() for v in VARIANTS):
        raise ValueError('Cap evidence already exists; refusing overwrite')
    binary = read_json(DOCS / 'aa-ownership-after-build.json')['binary_sha256']
    matrix = prepare(read_json(DOCS / 'gear-source-inputs.json'), binary)
    write(DOCS / 'cap-experiment-inputs.json', matrix)
    command(['docker', 'cp', str(DOCS / 'cap-experiment-inputs.json'), SERVER + ':' + RUNTIME + '/cap-experiment-inputs.json'])
    if sql('SELECT (SELECT COUNT(*) FROM account)+(SELECT COUNT(*) FROM character_data)+(SELECT COUNT(*) FROM character_alternate_abilities)+(SELECT COUNT(*) FROM inventory);').strip() != '0':
        raise ValueError('Initial synthetic fixture is not empty')
    if sql("SELECT ENGINE FROM information_schema.TABLES WHERE TABLE_SCHEMA='nightcap_balance_20260912' AND TABLE_NAME='rule_values';").strip() != 'InnoDB':
        raise ValueError('Transactional rule storage is required')
    query = "SELECT ruleset_id,rule_name,rule_value,notes FROM rule_values WHERE rule_name IN ('Character:ItemSpellDmgCap','Character:ItemHealAmtCap') ORDER BY ruleset_id,rule_name;"
    original = sql(query)
    checks = {'binary_sha256': binary, 'original_rules_tsv': original, 'phases': []}
    for variant, caps in VARIANTS.items():
        for mode, before, after in [('apply', (250, 250), caps), ('restore', caps, (250, 250))]:
            write_path = DOCS / f'cap-{variant}-{mode}.sql'
            write_path.write_bytes(rule_sql(before, after, 'cap_' + mode + '_' + uuid4().hex[:12]).encode())
        print('Starting ' + variant + ': 54 matched fights', flush=True)
        sql((DOCS / f'cap-{variant}-apply.sql').read_text(encoding='utf-8'))
        phase = {'variant': variant, 'applied_rules_tsv': sql(query)}
        try:
            # One awaited batch; child cases retain their existing native timeout.
            with (DOCS / f'cap-{variant}-run.log').open('wb') as log:
                completed = subprocess.run(['docker', 'exec', '-w', RUNTIME, SERVER, 'python3',
                    'release_pool_controls.py', '--inputs', 'cap-experiment-inputs.json', '--run',
                    '--output', f'cap-{variant}.json.gz'], stdout=log, stderr=subprocess.STDOUT)
            if completed.returncode:
                raise RuntimeError('Native cap batch failed; inspect captured run log: ' + variant)
            command(['docker', 'cp', SERVER + ':' + RUNTIME + f'/cap-{variant}.json.gz', str(DOCS / f'cap-{variant}.json.gz')])
            phase['groups'] = verify(matrix, read_json(DOCS / f'cap-{variant}.json.gz'),
                                     read_json(DOCS / 'gear-source.json.gz'), variant,
                                     read_json(DOCS / 'native-aa-catalog.json'))
        finally:
            sql((DOCS / f'cap-{variant}-restore.sql').read_text(encoding='utf-8'))
            phase['restored_rules_tsv'] = sql(query)
            phase['restored_exactly'] = phase['restored_rules_tsv'] == original
            checks['phases'].append(phase)
            write(output, checks)
            if not phase['restored_exactly']:
                raise RuntimeError('Cap rules did not restore exactly')
        print('Verified and restored ' + variant, flush=True)
    checks['completed'] = True
    write(output, checks)


if __name__ == '__main__':
    run()
