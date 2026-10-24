"""Read-only production content capture for the Paineel passage to The Hole.

Run on the production host over SSH; stdout contains public door/item definitions.
"""
import datetime
import json
import subprocess


def query(statement):
    result = subprocess.run([
        'docker', 'compose', 'exec', '-T', 'db', 'mariadb',
        '--defaults-extra-file=/run/secrets/db_backup_config',
        '-N', '-B', '--raw', 'peq',
    ], cwd='/opt/nightcap/deploy/production',
        input='START TRANSACTION READ ONLY;\n' + statement + ';\nROLLBACK;',
        text=True, capture_output=True, check=True, timeout=60)
    return result.stdout


def capture():
    columns = [line.split('\t')[0] for line in query('SHOW COLUMNS FROM doors').splitlines()]
    fields = ','.join('`' + c + '`' for c in columns)
    doors = [dict(zip(columns, json.loads(line))) for line in query(
        "SELECT JSON_ARRAY(" + fields + ") FROM doors WHERE zone IN ('paineel','hole') ORDER BY id"
    ).splitlines()]
    return {
        'captured_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'environment': 'production',
        'doors': doors,
        'keys': [json.loads(line) for line in query(
            'SELECT JSON_ARRAY(id,Name) FROM items WHERE id IN (6378,6379,6380) ORDER BY id'
        ).splitlines()],
    }


if __name__ == '__main__':
    print(json.dumps(capture(), indent=2) + '\n')
