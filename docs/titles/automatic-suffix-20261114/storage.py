"""Real, isolated MariaDB transaction fences; never connect to production."""
import json
from pathlib import Path
import subprocess
import time
import uuid

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]


def main():
    token=uuid.uuid4().hex[:12];name='nightcap-title-auto-'+token
    image=subprocess.check_output(['docker','image','inspect','mariadb:10.11','--format','{{.Id}}'],text=True).strip()
    subprocess.run(['docker','run','--pull=never','-d','--network','none','--label','nightcap.title-fixture='+token,
        '--name',name,'-e','MARIADB_ALLOW_EMPTY_ROOT_PASSWORD=1','-e','MARIADB_DATABASE=test',image,'--skip-networking'],check=True,stdout=subprocess.DEVNULL)
    def sql(query):
        return subprocess.check_output(['docker','exec','-i',name,'mariadb','-uroot','-N','test'],input=query,text=True).strip()
    try:
        deadline=time.monotonic()+120
        while time.monotonic()<deadline:
            ready=subprocess.run(['docker','exec',name,'mariadb','-uroot','-N','-e',"SELECT SCHEMA_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME='test'"],capture_output=True)
            comm=subprocess.run(['docker','exec',name,'cat','/proc/1/comm'],capture_output=True)
            if ready.returncode==0 and ready.stdout.strip()==b'test' and b'mariadbd' in comm.stdout:break
            time.sleep(1)
        else:raise RuntimeError('Fixture startup failed')
        sql((ROOT/'docs/titles/setup.sql').read_text(encoding='utf8'))
        sql('UPDATE nightcap_title_settings SET enabled=1 WHERE id=1')
        rows=sql('SELECT enabled,@@in_transaction FROM nightcap_title_settings WHERE id=1 AND catalog_version=1; START TRANSACTION; SELECT enabled,@@in_transaction FROM nightcap_title_settings WHERE id=1 AND catalog_version=1; ROLLBACK; SELECT enabled,@@in_transaction FROM nightcap_title_settings WHERE id=1 AND catalog_version=1;')
        assert rows.splitlines()==['1\t0','1\t1','1\t0']
        sql('START TRANSACTION; INSERT INTO nightcap_title_counters VALUES (42,1,100); ROLLBACK;')
        assert sql('SELECT COUNT(*) FROM nightcap_title_counters')=='0'
        sql('START TRANSACTION; INSERT INTO nightcap_title_counters VALUES (42,1,100); COMMIT;')
        assert sql('SELECT value FROM nightcap_title_counters WHERE character_id=42 AND counter_id=1')=='100'
        sql('INSERT IGNORE INTO nightcap_title_awards VALUES (42,1900000001,1); INSERT IGNORE INTO nightcap_title_awards VALUES (42,1900000001,2);')
        assert sql('SELECT COUNT(*),MIN(earned_at) FROM nightcap_title_awards')=='1\t1'
        report=dict(result='PASS',image=image,network='none',checks=[
            'combined enablement and actual connection transaction state',
            'rolled-back counters do not become eligible',
            'committed counters are read without replay',
            'one stable award remains unique for both title placements'])
        (HERE/'storage-tests.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report))
    finally:
        owner=subprocess.check_output(['docker','inspect','--format','{{index .Config.Labels "nightcap.title-fixture"}}',name],text=True).strip()
        assert owner==token
        subprocess.run(['docker','rm','-f','-v',name],check=True,stdout=subprocess.DEVNULL)


if __name__=='__main__':main()
