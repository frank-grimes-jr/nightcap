"""Exercise migration refusal and atomicity against a disposable MariaDB schema."""
import json
from pathlib import Path
import secrets
import subprocess

ROOT = Path(__file__).resolve().parents[2]
RELEASE = ROOT / 'docs/releases/remove-item-lore-20261012'
DB = 'nightcap_lore_guards_' + secrets.token_hex(6)


def sql(source, database=True, check=True):
    result = subprocess.run(['docker', 'exec', '-i', 'akk-stack-mariadb-1', 'sh', '-c',
        'MYSQL_PWD="${MARIADB_ROOT_PASSWORD:-$MYSQL_ROOT_PASSWORD}" exec mariadb -uroot --batch --raw --skip-column-names'],
        input=(f'USE `{DB}`;\n' if database else '') + source,
        text=True, capture_output=True, timeout=90)
    if check and result.returncode:
        raise RuntimeError(result.stderr)
    return result


def snapshot():
    return sql('SELECT * FROM rule_values ORDER BY ruleset_id,rule_name;').stdout


def main():
    checks = []
    sql(f'CREATE DATABASE `{DB}`;', False)
    try:
        sql('CREATE TABLE rule_values LIKE peq.rule_values; CREATE TABLE rule_sets LIKE peq.rule_sets; CREATE TABLE variables LIKE peq.variables;')
        for label, drift in [
            ('baseline', ''),
            ('missing rule', "DELETE FROM rule_values WHERE rule_name='Items:DisableLore';"),
            ('already enabled', "UPDATE rule_values SET rule_value='true' WHERE rule_name='Items:DisableLore';"),
            ('case drift', "UPDATE rule_values SET rule_value='False' WHERE rule_name='Items:DisableLore';"),
            ('other ruleset', "INSERT INTO rule_values(ruleset_id,rule_name,rule_value) VALUES(2,'Items:DisableLore','false');"),
            ('legacy override', "INSERT INTO variables(varname,value,information) VALUES('disablelore','1','test');"),
            ('selected ruleset', "INSERT INTO variables(varname,value,information) VALUES('RuleSet','pop+','test');"),
            ('renamed default', "UPDATE rule_sets SET name='changed' WHERE ruleset_id=1;")]:
            sql("DELETE FROM rule_values; DELETE FROM rule_sets; DELETE FROM variables; INSERT INTO rule_sets(ruleset_id,name) VALUES(1,'default'); INSERT INTO rule_values(ruleset_id,rule_name,rule_value,notes) VALUES(1,'Items:DisableLore','false','preserve me'),(1,'Items:FreeTrade','true','unrelated');" + drift)
            before = snapshot()
            result = sql((RELEASE/'activate.sql').read_text(), check=False)
            if label == 'baseline':
                assert result.returncode == 0, result.stderr
                assert snapshot() == before.replace('Items:DisableLore\tfalse', 'Items:DisableLore\ttrue')
                sql((RELEASE/'rollback.sql').read_text())
                assert snapshot() == before
                checks.append('activation changes only requested value; immediate rollback restores exact rows')
            else:
                assert result.returncode != 0, label
                assert snapshot() == before, label
                sql('DROP PROCEDURE nightcap_enable_no_lore_20261012;')
                checks.append(label + ' rejected without rule changes')
        (RELEASE/'migration-check.json').write_text(json.dumps({'status':'passed','scope':'Disposable schema; PEQ unchanged','checks':checks},indent=2)+'\n')
        print(f'Passed {len(checks)} migration scenarios.')
    finally:
        sql(f'DROP DATABASE `{DB}`;', False)


if __name__ == '__main__':
    main()
