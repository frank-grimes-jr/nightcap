"""Capture only public content/schema evidence for the Epic 0.5 candidate."""
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def sql(query):
    command = ['docker', 'exec', '-i', 'akk-stack-eqemu-server-1', 'mysql',
               '-h', 'mariadb', '-ueqemu', '-peqemu', 'peq', '-N', '-B', '--raw']
    result = subprocess.run(command, input=query, text=True, capture_output=True,
                            encoding='utf-8', timeout=90)
    if result.returncode:
        raise RuntimeError(result.stderr)
    return result.stdout


def capture():
    catalog = json.loads((ROOT / 'docs/adventure-journal/catalog.json').read_text())
    objectives = [o for chapter in catalog['shared'] + catalog['paths']
                  for o in chapter['objectives'] if 'npc' in o]
    ids = ','.join(str(v) for v in sorted({o['npc'] for o in objectives}))
    fields = ['id', 'name', 'level', 'hp', 'mindmg', 'maxdmg', 'npc_spells_id', 'special_abilities']
    pairs = ','.join("'" + f + "',n.`" + f + "`" for f in fields)
    for alias, prefix in [('s', 'spawn'), ('e', 'entry')]:
        for field in ['min_expansion', 'max_expansion', 'content_flags', 'content_flags_disabled']:
            pairs += ", '" + prefix + '_' + field + "'," + alias + '.' + field
    pairs += ", 'condition',s._condition,'chance',e.chance,'min_time',e.min_time,'max_time',e.max_time"
    query = ('SELECT JSON_OBJECT(' + pairs + ", 'zone',s.zone,'version',s.version) "
             'FROM npc_types n JOIN spawnentry e ON e.npcID=n.id '
             'JOIN spawn2 s ON s.spawngroupID=e.spawngroupID '
             f'WHERE n.id IN ({ids}) AND s.version=0 ORDER BY n.id,s.id;')
    snapshot = {'scope': 'read-only local PEQ content; not production acceptance',
                'npcs': [json.loads(line) for line in sql(query).splitlines()], 'schemas': {}}
    for table in ('tasks', 'task_activities', 'spells_new', 'items'):
        columns = []
        for line in sql('SHOW COLUMNS FROM `' + table + '`;').splitlines():
            name, kind, nullable, key, default, extra = line.split('\t')
            columns.append({'name': name, 'type': kind, 'default': None if default == 'NULL' else default})
        snapshot['schemas'][table] = columns
    query = ('SELECT id FROM tasks WHERE id BETWEEN 9500 AND 9507;'
             'SELECT taskid FROM task_activities WHERE taskid BETWEEN 9500 AND 9507;'
             'SELECT id FROM spells_new WHERE id BETWEEN 42800 AND 42805;'
             'SELECT id FROM items WHERE id=900501;')
    if sql(query).strip():
        raise ValueError('Reserved content IDs are occupied; review before generating')
    destination = ROOT / 'docs/adventure-journal/content-snapshot.json'
    destination.write_text(json.dumps(snapshot, indent=2) + '\n', encoding='utf-8')
    print(f'Captured {len(snapshot["npcs"])} NPC definitions and four schemas; reserved IDs free.')


if __name__ == '__main__':
    capture()
