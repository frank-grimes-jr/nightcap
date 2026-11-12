"""Real MariaDB controls in a disposable, network-disabled database container."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]


def main():
    name = 'nightcap-title-test-' + uuid.uuid4().hex[:10]
    results = []

    def docker(*args, **kwargs):
        return subprocess.run(['docker', *args], check=True, capture_output=True, **kwargs)

    def sql(statement):
        return docker('exec', '-i', name, 'mariadb', '-uroot', '-N', '-B', 'test',
                      input=statement.encode()).stdout.decode().strip()

    def check(label, condition):
        assert condition, label
        results.append(label)
        print('PASS ' + label, flush=True)

    try:
        docker('run', '-d', '--name', name, '--network', 'none', '-e',
               'MARIADB_ALLOW_EMPTY_ROOT_PASSWORD=1', '-e', 'MARIADB_DATABASE=test',
               'mariadb:10.11', '--skip-networking')
        for _ in range(60):
            ready = subprocess.run(['docker', 'exec', name, 'mariadb', '-uroot', '-N', '-e',
                                    "SELECT SCHEMA_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME='test'"],
                                   capture_output=True)
            # Final entrypoint database must be available, not just bootstrap.
            cmd = subprocess.run(['docker', 'exec', name, 'cat', '/proc/1/comm'], capture_output=True)
            if ready.returncode == 0 and ready.stdout.strip() == b'test' and b'mariadbd' in cmd.stdout:
                break
            time.sleep(1)
        else:
            raise RuntimeError('isolated MariaDB did not become ready')
        setup = (ROOT/'docs/titles/setup.sql').read_text(encoding='utf-8')
        sql(setup)
        check('new installation disabled', sql('SELECT catalog_version,enabled FROM nightcap_title_settings WHERE id=1') == '1\t0')
        check('three InnoDB tables', sql("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='test' AND engine='InnoDB' AND table_name LIKE 'nightcap_title_%'") == '3')
        check('award unique identity', sql("SELECT GROUP_CONCAT(column_name ORDER BY seq_in_index) FROM information_schema.statistics WHERE table_schema='test' AND table_name='nightcap_title_awards' AND index_name='PRIMARY'") == 'character_id,title_id')
        sql('UPDATE nightcap_title_settings SET enabled=1 WHERE id=1 AND catalog_version=1 AND enabled=0')
        award = 'INSERT IGNORE INTO nightcap_title_awards VALUES (42,1900000001,123456)'
        sql(award); sql(award)
        check('idempotent award and first timestamp preserved', sql('SELECT COUNT(*),MIN(earned_at) FROM nightcap_title_awards WHERE character_id=42') == '1\t123456')
        sql(setup)
        check('reapply preserves active control and awards', sql('SELECT enabled FROM nightcap_title_settings WHERE id=1') == '1' and sql('SELECT COUNT(*) FROM nightcap_title_awards') == '1')
        upsert = 'INSERT INTO nightcap_title_counters VALUES (42,1,1),(42,2,1) ON DUPLICATE KEY UPDATE value=LEAST(value+1,10000)'
        with ThreadPoolExecutor(max_workers=4) as workers:
            list(workers.map(lambda _: sql(upsert), range(40)))
        check('concurrent counters atomic without lost increments', sql('SELECT SUM(value),COUNT(*) FROM nightcap_title_counters WHERE character_id=42') == '80\t2')
        sql('UPDATE nightcap_title_counters SET value=10000 WHERE character_id=42'); sql(upsert)
        check('counter saturation', sql('SELECT MIN(value),MAX(value) FROM nightcap_title_counters') == '10000\t10000')
        with ThreadPoolExecutor(max_workers=4) as workers:
            list(workers.map(lambda _: sql(award), range(12)))
        check('concurrent grants stay unique', sql('SELECT COUNT(*) FROM nightcap_title_awards WHERE character_id=42') == '1')
        sql('INSERT INTO nightcap_title_awards VALUES (43,1900000001,123457)')
        check('awards are per character', sql('SELECT COUNT(DISTINCT character_id) FROM nightcap_title_awards') == '2')
        sql('UPDATE nightcap_title_settings SET enabled=0 WHERE id=1 AND enabled=1')
        check('disable preserves earned state', sql('SELECT COUNT(*) FROM nightcap_title_awards') == '2' and sql('SELECT SUM(value) FROM nightcap_title_counters') == '20000')
        report = dict(status='PASS', checks=results, scope='Disposable MariaDB10.11, network none; no runtime/player DB access')
        (ROOT/'docs/titles/storage-tests.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    finally:
        # This exact container was created above; no existing container/volume is removed.
        subprocess.run(['docker', 'rm', '-f', '-v', name], capture_output=True)


if __name__ == '__main__':
    main()
