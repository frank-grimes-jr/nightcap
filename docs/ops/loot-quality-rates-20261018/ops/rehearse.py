"""Real MariaDB tests on session-local temporary tables only; no persistent writes.

POLICY_SOURCE is the operator prefix before DB configuration, supplied by runner.
"""
import json
import subprocess

exec(POLICY_SOURCE)
DB=['docker','compose','exec','-T','db','mariadb',
    '--defaults-extra-file=/run/secrets/db_backup_config','--batch','--raw','--skip-column-names','peq']

def run(sql):
    return subprocess.run(DB,cwd='/opt/nightcap/deploy/production',input=sql,
                          text=True,capture_output=True)

setup="CREATE TEMPORARY TABLE rule_values (ruleset_id INT, rule_name VARCHAR(100), rule_value VARCHAR(100), notes TEXT) ENGINE=InnoDB; "
for n,(a,b) in CHANGES.items():
    setup+=f"INSERT INTO rule_values VALUES (1,'{n}','{a}','preserve notes'); "
setup+="INSERT INTO rule_values VALUES (1,'Unrelated:Rule','unchanged','keep'); "+GUARD_TABLE
query='SELECT ruleset_id,rule_name,rule_value,notes FROM rule_values ORDER BY rule_name; '
before=run(setup+query); assert before.returncode==0
roundtrip=run(setup+'START TRANSACTION; '+FORWARD+query+INVERSE+query+'ROLLBACK;')
assert roundtrip.returncode==0, roundtrip.stderr
expected=before.stdout
for n,(a,b) in CHANGES.items():
    expected=expected.replace(n+'\t'+a+'\t',n+'\t'+b+'\t')
assert roundtrip.stdout==expected+before.stdout
cases={
 'drift':"UPDATE rule_values SET rule_value='999' WHERE rule_name='Zone:LootTierRareChance'; ",
 'missing':"DELETE FROM rule_values WHERE rule_name='Zone:LootTierEpicChance'; ",
 'case_only_drift':"UPDATE rule_values SET rule_name='zone:LootTierRareChance' WHERE rule_name='Zone:LootTierRareChance'; ",
 'already_applied':FORWARD,
}
for label,mutation in cases.items():
    result=run(setup+mutation+'START TRANSACTION; '+FORWARD+'COMMIT;')
    assert result.returncode!=0 and 'CONSTRAINT' in result.stderr, label
print(json.dumps({'status':'passed','temporary_table_only':True,
                  'cases':['forward_inverse_exact_rows_and_notes',*cases]}))
