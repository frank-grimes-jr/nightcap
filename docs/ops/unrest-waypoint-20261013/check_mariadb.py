"""Disposable, network-isolated MariaDB rehearsal using synthetic records only."""
import ast
import json
import subprocess
import time
from pathlib import Path

SQL = Path(__file__).resolve().parent
ROOT = SQL.parents[2]
NAME = 'nightcap-unrest-sql-test-20261013'

def run(args, **kwargs):
    return subprocess.run(args, text=True, capture_output=True, check=True, **kwargs)

tree = ast.parse((ROOT / 'tools/tests/test_unrest_waypoint.py').read_text())
setup = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == 'setUp')
fixture = next(n.args[0].value for n in ast.walk(setup) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == 'executescript')
fixture = fixture.replace('zone TEXT', 'zone VARCHAR(32)')
tables = ('nightcap_waypoints','spawn2','zone_state_spawns','nightcap_character_waypoints')
container = None
checks = []
try:
    container = run(['docker','run','-d','--network','none','--name',NAME,'--tmpfs','/var/lib/mysql','-e','MYSQL_ALLOW_EMPTY_PASSWORD=1','--entrypoint','docker-entrypoint.sh','akk-stack-mariadb','mysqld']).stdout.strip()
    for _ in range(30):
        ready = subprocess.run(['docker','exec',container,'mariadb-admin','-uroot','ping'],capture_output=True)
        process = subprocess.run(['docker','exec',container,'cat','/proc/1/comm'],capture_output=True,text=True)
        if process.returncode != 0:
            raise RuntimeError(run(['docker','logs',container]).stdout)
        if ready.returncode == 0 and process.stdout.strip() in ('mysqld','mariadbd'):
            break
        time.sleep(1)
    else:
        raise RuntimeError('Isolated MariaDB did not become ready')
    def sql(text, check=True):
        return subprocess.run(['docker','exec','-i',container,'mariadb','-uroot','--batch','--raw','--skip-column-names'],input=text,text=True,capture_output=True,check=check)
    def reset():
        sql('DROP DATABASE IF EXISTS unrest_test; CREATE DATABASE unrest_test; USE unrest_test;'+fixture)
    def snapshot():
        return {t:sql('USE unrest_test; SELECT * FROM '+t+' ORDER BY 1;').stdout for t in tables}
    reset()
    before = snapshot()
    forward = (SQL/'forward.sql').read_text()
    rollback = (SQL/'rollback.sql').read_text()
    sql('USE unrest_test;'+forward)
    got = sql("USE unrest_test; SELECT x,y,z,heading FROM spawn2 WHERE id=3266123; SELECT x,y,z,heading FROM nightcap_waypoints WHERE zone='unrest';").stdout
    assert got == '52\t-38\t3\t0\n'*2, got
    assert snapshot()['nightcap_character_waypoints'] == before['nightcap_character_waypoints']
    checks.append('forward portal/recall and discoveries')
    sql("USE unrest_test; UPDATE zone_state_spawns SET hp=12345,loot_data='new activity' WHERE id=1;")
    sql('USE unrest_test;'+rollback)
    assert sql('USE unrest_test; SELECT x,y,z,heading,hp,loot_data FROM zone_state_spawns WHERE id=1;').stdout == '118\t881\t3.75\t0\t12345\tnew activity\n'
    after = snapshot()
    assert all(after[t] == before[t] for t in ('spawn2','nightcap_waypoints','nightcap_character_waypoints'))
    checks.append('inverse preserves newer activity and restores durable placement')
    for drift in ("UPDATE spawn2 SET x=x+1 WHERE id=3266123;", "UPDATE nightcap_waypoints SET x=x+1 WHERE zone='unrest';", "UPDATE spawn2 SET x=x+1 WHERE id=3266037;"):
        reset()
        sql('USE unrest_test;'+drift)
        before = snapshot()
        result = sql('USE unrest_test;'+forward,check=False)
        assert result.returncode != 0 and 'CONSTRAINT' in result.stderr
        assert snapshot() == before
        checks.append('preimage rejection preserves all synthetic tables: '+drift)
    reset()
    sql('USE unrest_test;'+forward)
    before = snapshot()
    assert sql('USE unrest_test;'+forward,check=False).returncode != 0
    assert snapshot() == before
    checks.append('repeat fails closed without further changes')
    reset()
    sql('USE unrest_test; DELETE FROM zone_state_spawns;')
    sql('USE unrest_test;'+forward)
    assert snapshot()['zone_state_spawns'] == ''
    checks.append('absent saved state')
    result={'checks':checks,'passed':len(checks),'version':sql('SELECT VERSION();').stdout.strip(),'scope':'Synthetic fixture in disposable local network-isolated MariaDB; not production deployment or gameplay QA.'}
    (SQL/'mariadb-checks.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
finally:
    if container:
        run(['docker','rm','-f',container])
