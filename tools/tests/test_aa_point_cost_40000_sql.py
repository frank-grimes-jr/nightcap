"""Rehearse exact forward/inverse SQL in a disposable local MariaDB; never PEQ."""
from pathlib import Path
import json
import subprocess
import time
import uuid

ROOT=Path(__file__).resolve().parents[2]
SQL=ROOT/'docs/ops/aa-point-cost-40000-20261021'
name='nightcap-aa-pacing-test-'+uuid.uuid4().hex[:12]
def run(args,**kw):
    return subprocess.run(args,text=True,capture_output=True,**kw)
def query(sql,ok=True):
    p=run(['docker','exec','-i',name,'mariadb','-uroot','--batch','--skip-column-names','aa_pacing_test'],input=sql)
    if ok and p.returncode: raise RuntimeError(p.stderr)
    return p
schema="""CREATE DATABASE aa_pacing_test; USE aa_pacing_test;
CREATE TABLE rule_values(ruleset_id INT,rule_name VARCHAR(100),rule_value VARCHAR(100),notes TEXT,
 PRIMARY KEY(ruleset_id,rule_name)) ENGINE=InnoDB;
CREATE TABLE rule_sets(ruleset_id INT PRIMARY KEY,name VARCHAR(100)) ENGINE=InnoDB;
CREATE TABLE variables(varname VARCHAR(100) PRIMARY KEY,value VARCHAR(100)) ENGINE=InnoDB;
CREATE TABLE character_data(id INT PRIMARY KEY,aa_points INT,aa_exp INT,spent INT) ENGINE=InnoDB;
INSERT INTO character_data VALUES(1,17,2000,1018);
"""
baseline="""DROP PROCEDURE IF EXISTS nightcap_aa_cost_20261021_forward;
DROP PROCEDURE IF EXISTS nightcap_aa_cost_20261021_rollback;
DELETE FROM rule_values; DELETE FROM rule_sets; DELETE FROM variables;
INSERT INTO rule_sets VALUES(1,'default');
INSERT INTO rule_values VALUES
(1,'AA:ExpPerPoint','4000','retain notes'),(1,'AA:PassiveExpPercent','10',''),
(1,'AA:NormalizedAAEnabled','false',''),(1,'AA:ModernAAScalingEnabled','false',''),
(1,'Other:Sentinel','unchanged','retain notes');
"""
forward=(SQL/'forward.sql').read_text(); rollback=(SQL/'rollback.sql').read_text()
snapshot='SELECT * FROM rule_values ORDER BY ruleset_id,rule_name; SELECT * FROM character_data;'
results=[]
try:
    p=run(['docker','run','-d','--rm','--name',name,'--network','none',
           '-e','MARIADB_ALLOW_EMPTY_ROOT_PASSWORD=1','mariadb:10.11',
           '--skip-networking','--performance-schema=OFF','--innodb-buffer-pool-size=64M'])
    if p.returncode: raise RuntimeError(p.stderr)
    # Wait for final ready server, not its initialization child.
    for _ in range(60):
        p=run(['docker','exec',name,'mariadb','-uroot','-e','SELECT 1'])
        logs=run(['docker','logs',name])
        if p.returncode==0 and 'MariaDB init process done' in logs.stdout+logs.stderr: break
        time.sleep(1)
    else: raise RuntimeError('MariaDB did not initialize')
    p=run(['docker','exec','-i',name,'mariadb','-uroot'],input=schema)
    if p.returncode: raise RuntimeError(p.stderr)
    query(baseline); before=query(snapshot).stdout
    query(forward); after=query(snapshot).stdout
    assert after==before.replace('AA:ExpPerPoint\t4000\t','AA:ExpPerPoint\t40000\t',1)
    results.append('forward changes exactly one value; notes and player rows identical')
    query(rollback); assert query(snapshot).stdout==before
    results.append('inverse exactly restores baseline without touching player rows')
    # A repeated successful forward must fail closed.
    query(forward); before=query(snapshot).stdout
    assert query(forward,ok=False).returncode
    assert query(snapshot).stdout==before
    results.append('repeated forward rejected without further changes')
    variants={
      'wrong threshold':"UPDATE rule_values SET rule_value='8000' WHERE rule_name='AA:ExpPerPoint';",
      'passive changed':"UPDATE rule_values SET rule_value='20' WHERE rule_name='AA:PassiveExpPercent';",
      'normalized enabled':"UPDATE rule_values SET rule_value='true' WHERE rule_name='AA:NormalizedAAEnabled';",
      'modern scaling enabled':"UPDATE rule_values SET rule_value='true' WHERE rule_name='AA:ModernAAScalingEnabled';",
      'alternate override':"INSERT INTO rule_values VALUES(2,'AA:ExpPerPoint','4000','');",
      'missing threshold':"DELETE FROM rule_values WHERE rule_name='AA:ExpPerPoint';",
      'active alternate ruleset':"INSERT INTO variables VALUES('RuleSet','custom');",
      'default identity changed':"UPDATE rule_sets SET name='custom';",
      'noncanonical preimage':"UPDATE rule_values SET rule_value='04000' WHERE rule_name='AA:ExpPerPoint';",
    }
    for label,mutation in variants.items():
        query(baseline+mutation); before=query(snapshot).stdout
        assert query(forward,ok=False).returncode, label
        assert query(snapshot).stdout==before,label
        results.append(label+' rejected with no data change')
    query(baseline); query(forward)
    query("UPDATE rule_values SET rule_value='80000' WHERE rule_name='AA:ExpPerPoint';")
    before=query(snapshot).stdout
    assert query(rollback,ok=False).returncode
    assert query(snapshot).stdout==before
    results.append('rollback preserves later external threshold edit')
    result={'status':'passed','environment':'disposable local mariadb:10.11; no network/volumes','checks':results}
    (SQL/'sql-tests.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
finally:
    # Only this uniquely named container, created by this test, is eligible.
    run(['docker','rm','-f',name])
