"""Read-only complete production door capture; stdout contains content only.

Run over SSH on the production host. No files or game state are changed.
"""
import datetime
import json
import subprocess


def query(sql):
    return subprocess.run([
        'sudo', '-n', 'docker', 'compose', 'exec', '-T', 'db', 'mariadb',
        '--defaults-extra-file=/run/secrets/db_backup_config',
        '-N', '-B', '--raw', 'peq'], cwd='/opt/nightcap/deploy/production',
        input='START TRANSACTION READ ONLY;\n' + sql + ';\nROLLBACK;',
        text=True, capture_output=True, check=True, timeout=60).stdout


def capture():
    definitions = [line.split('\t') for line in query('SHOW COLUMNS FROM doors').splitlines()]
    columns = [line[0] for line in definitions]
    floats = [line[0] for line in definitions if line[1].lower().startswith('float')]
    # Match the exact CAST(... AS CHAR) preimage used by content_patch, including FLOATs.
    fields = ','.join('CAST(`' + c + '` AS CHAR)' for c in columns)
    exact_fields = ','.join("'" + c + "',CAST(`" + c + '` AS DOUBLE)' for c in floats)
    rows = []
    float_preimages = {}
    for line in query('SELECT JSON_ARRAY(' + fields + '),JSON_OBJECT(' + exact_fields +
                      ') FROM doors ORDER BY id').splitlines():
        values, exact = line.split('\t', 1)
        row = dict(zip(columns, json.loads(values)))
        for field in ('id', 'keyitem', 'lockpick'):
            row[field] = int(row[field])
        rows.append(row)
        # Preserve float32 storage for exact reconstruction in an isolated rehearsal.
        float_preimages[str(row['id'])] = json.loads(exact)
    return {'captured_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'environment': 'production', 'doors': rows,
            'create_table': query('SHOW CREATE TABLE doors').split('\t', 1)[1].strip(),
            'float_preimages': float_preimages}


if __name__ == '__main__':
    print(json.dumps(capture(), indent=2))
