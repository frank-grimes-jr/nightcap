"""Read-only complete production door capture; stdout contains content only.

Run over SSH on the production host. No files or game state are changed.
"""
import datetime
import json
import subprocess


def query(sql):
    return subprocess.run([
        'docker', 'compose', 'exec', '-T', 'db', 'mariadb',
        '--defaults-extra-file=/run/secrets/db_backup_config',
        '-N', '-B', '--raw', 'peq'], cwd='/opt/nightcap/deploy/production',
        input='START TRANSACTION READ ONLY;\n' + sql + ';\nROLLBACK;',
        text=True, capture_output=True, check=True, timeout=60).stdout


def capture():
    columns = [line.split('\t')[0] for line in query('SHOW COLUMNS FROM doors').splitlines()]
    # Match the exact CAST(... AS CHAR) preimage used by content_patch, including FLOATs.
    fields = ','.join('CAST(`' + c + '` AS CHAR)' for c in columns)
    rows = [dict(zip(columns, json.loads(line))) for line in query(
        'SELECT JSON_ARRAY(' + fields + ') FROM doors ORDER BY id').splitlines()]
    for row in rows:
        for field in ('id', 'keyitem', 'lockpick'):
            row[field] = int(row[field])
    return {'captured_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'environment': 'production', 'doors': rows}


if __name__ == '__main__':
    print(json.dumps(capture(), indent=2))
