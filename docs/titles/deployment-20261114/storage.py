"""Isolated real-MariaDB migration, rollback, party-batch and burst controls."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import time
import uuid
import schema

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]


def main():
    name='nightcap-title-release-'+uuid.uuid4().hex[:10]
    def docker(*args,**kwargs):
        return subprocess.run(['docker',*args],check=True,capture_output=True,**kwargs)
    def sql(statement):
        return docker('exec','-i',name,'mariadb','-uroot','-N','-B','test',input=statement.encode()).stdout.decode().strip()
    checks=[]
    def check(label,condition):
        assert condition,label;checks.append(label);print('PASS '+label,flush=True)
    try:
        docker('run','-d','--name',name,'--network','none','-e','MARIADB_ALLOW_EMPTY_ROOT_PASSWORD=1','-e','MARIADB_DATABASE=test','mariadb:10.11','--skip-networking')
        for _ in range(60):
            ready=subprocess.run(['docker','exec',name,'mariadb','-uroot','-N','-e',"SELECT SCHEMA_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME='test'"],capture_output=True)
            comm=subprocess.run(['docker','exec',name,'cat','/proc/1/comm'],capture_output=True)
            if ready.returncode==0 and ready.stdout.strip()==b'test' and b'mariadbd' in comm.stdout:break
            time.sleep(1)
        else:raise RuntimeError('Isolated MariaDB not ready')
        sql("CREATE TABLE command_settings(command VARCHAR(128) PRIMARY KEY,access INT NOT NULL,aliases VARCHAR(512) NOT NULL) ENGINE=InnoDB; INSERT INTO command_settings VALUES ('existing',80,'oldalias'); CREATE TABLE titles(id INT UNSIGNED PRIMARY KEY) ENGINE=InnoDB")
        setup=(ROOT/'docs/titles/setup.sql').read_text(encoding='utf-8')
        sql(setup);expected=schema.structure(sql)
        check('strict numeric schemas, InnoDB and primary keys',len(expected['tables'])==3 and not expected['triggers'] and len(expected['constraints'])==3)
        sql('DROP TABLE nightcap_title_awards,nightcap_title_counters,nightcap_title_settings') # this isolated fixture only
        before=schema.commands(sql)
        schema.install(sql,setup,expected,before)
        check('full activation preserves other commands',schema.without_title(schema.commands(sql))==before)
        schema.require_installed(sql,expected,1)
        try:schema.install(sql,setup,expected,before);raise RuntimeError('unsafe replay accepted')
        except AssertionError:checks.append('terminal/foreign schema replay rejected')
        sql("UPDATE command_settings SET access=100 WHERE command='titles'")
        try:schema.require_installed(sql,expected,1);raise RuntimeError('access drift accepted')
        except AssertionError:checks.append('command privilege drift rejected')
        sql("UPDATE command_settings SET access=0 WHERE command='titles'")
        award='INSERT IGNORE INTO nightcap_title_awards VALUES (42,1900000001,12345)'
        with ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(lambda _:sql(award),range(12)))
        check('concurrent awards remain unique',sql('SELECT COUNT(*) FROM nightcap_title_awards')=='1')
        sql('UPDATE nightcap_title_settings SET enabled=0 WHERE id=1 AND catalog_version=1 AND enabled=1')
        schema.require_installed(sql,expected,0)
        check('disable retains earned awards',sql('SELECT COUNT(*) FROM nightcap_title_awards')=='1')
        sql('UPDATE nightcap_title_settings SET enabled=1 WHERE id=1')
        measurements=[]
        for size in [1,6,72]:
            ids=','.join(str(i) for i in range(1000,1000+size))
            values=','.join(f'({i},1,1),({i},2,1)' for i in range(1000,1000+size))
            batch='SELECT enabled FROM nightcap_title_settings WHERE id=1 AND catalog_version=1; INSERT INTO nightcap_title_counters(character_id,counter_id,value) VALUES '+values+' ON DUPLICATE KEY UPDATE value=LEAST(value+1,10000); SELECT character_id,counter_id,value FROM nightcap_title_counters WHERE character_id IN ('+ids+'); SELECT character_id,title_id FROM nightcap_title_awards WHERE character_id IN ('+ids+');'
            sql('DELETE FROM nightcap_title_counters')
            start=time.perf_counter();sql(batch*50);elapsed=time.perf_counter()-start
            check(f'{size}-member burst preserves every personal count',sql('SELECT MIN(value),MAX(value),COUNT(*) FROM nightcap_title_counters')==f'50\t50\t{size*2}')
            measurements.append(dict(participants=size,kills=50,statements_per_kill=4,elapsed_seconds=elapsed,
                mean_seconds_per_kill=elapsed/50,scope='real SQL burst in disposable network-disabled MariaDB; includes container-client startup; not a production latency claim'))
        sql('UPDATE nightcap_title_counters SET value=10000');sql(batch)
        check('party counter saturation',sql('SELECT MIN(value),MAX(value) FROM nightcap_title_counters')=='10000\t10000')
        (HERE/'schema-expected.json').write_text(json.dumps(expected,indent=2)+'\n',encoding='utf-8')
        (HERE/'storage-tests.json').write_text(json.dumps(dict(status='PASS',checks=checks,measurements=measurements),indent=2)+'\n',encoding='utf-8')
    finally:subprocess.run(['docker','rm','-f','-v',name],capture_output=True)


if __name__=='__main__':main()
