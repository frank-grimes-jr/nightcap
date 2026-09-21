"""Read-only source capture for the tunnel services candidate (never applies SQL)."""
import argparse
import json
from pathlib import Path
import subprocess
from pok_hub_migration import sql_value

ROOT = Path(__file__).resolve().parents[1]


def query(sql, container, root_env=False):
    command=['docker', 'exec', '-i', container]
    if root_env:
        # Resolve the container's existing secret internally; never print it or
        # put it in host command arguments. The query remains SELECT/SHOW only.
        command += ['sh','-c','MYSQL_PWD="${MARIADB_ROOT_PASSWORD:-$MYSQL_ROOT_PASSWORD}" exec mariadb -uroot peq --batch --raw --skip-column-names']
    else:
        command += ['mysql','-ueqemu','-peqemu','peq','--batch','--raw','--skip-column-names']
    result = subprocess.run(command, input=sql,
        text=True, encoding='utf-8', capture_output=True, timeout=120)
    if result.returncode:
        raise RuntimeError(result.stderr)
    return result.stdout


def capture(container, root_env=False):
    schemas = {}
    def rows(table, where):
        if table not in schemas:
            columns = [s.split('\t')[0] for s in query(f'SHOW COLUMNS FROM `{table}`;', container,root_env).splitlines()]
            create = query(f'SHOW CREATE TABLE `{table}`;', container,root_env).split('\t', 1)[1].strip()
            schemas[table] = {'columns': columns, 'create': create}
        fields = ','.join(sql_value(c) + f',CAST(`{c}` AS CHAR)' for c in schemas[table]['columns'])
        return [json.loads(line) for line in query(f'SELECT JSON_OBJECT({fields}) FROM `{table}` WHERE {where};', container,root_env).splitlines()]

    audit = json.loads((ROOT/'docs/pok/hub-stock-audit.json').read_bytes())
    legal_spells = sorted({s['spell_id'] for s in audit['stock'] if s['classes_at_level_50']})
    spells = rows('spells_new', 'id IN ('+','.join(map(str, legal_spells))+')')
    merchants = rows('npc_types', "id BETWEEN 202000 AND 202999 AND class=41 AND lastname LIKE '%Supplies%'")
    stock = rows('merchantlist', 'merchantid IN ('+','.join({n['merchant_id'] for n in merchants})+
        ") AND min_expansion<=0 AND (max_expansion<0 OR max_expansion>=0) AND COALESCE(content_flags,'')='' AND COALESCE(content_flags_disabled,'')=''")
    item_ids = {int(r['item']) for r in stock}
    for spell in spells:
        item_ids.update(int(spell[f'components{i}']) for i in range(1, 5) if int(spell[f'components{i}']) > 0)
    # Starter templates, basics, instruments and traditional portable tradeskill containers.
    item_ids.update((1060, 9997, 9998, 9999, 5023, 13000, 13001, 13011, 13012, 13005, 13006, 13009))
    items = rows('items', 'id IN ('+','.join(map(str, sorted(item_ids)))+')')
    existing = list(range(997900, 997916))+[999220,999225,999226,999237,999238,999239]+list(range(999500,999510))+list(range(999520,999526))
    identities = ','.join(map(str, existing))
    scopes = {
        'npc_types': f'id IN ({identities}) OR id BETWEEN 999600 AND 999799 OR merchant_id BETWEEN 999600 AND 999639',
        'spawngroup': f'id IN ({identities}) OR id BETWEEN 999600 AND 999799',
        'spawnentry': f'spawngroupID IN ({identities}) OR npcID IN ({identities}) OR spawngroupID BETWEEN 999600 AND 999799 OR npcID BETWEEN 999600 AND 999799',
        'spawn2': f'spawngroupID IN ({identities}) OR id BETWEEN 999600 AND 999799 OR spawngroupID BETWEEN 999600 AND 999799',
        'merchantlist': 'merchantid BETWEEN 999600 AND 999639',
        'object': 'id BETWEEN 999600 AND 999619',
        'grid': 'zoneid=22 AND id BETWEEN 999700 AND 999719',
        'grid_entries': 'zoneid=22 AND gridid BETWEEN 999700 AND 999719',
        'items': 'id BETWEEN 998600 AND 998639 OR id=12832',
        'nightcap_market_actors': 'zone_id=22 OR npc_id BETWEEN 999600 AND 999799',
        'zone_state_spawns': f'zone_id=22 AND instance_id=0 AND is_corpse=0 AND is_zone=0 AND (npc_id IN ({identities}) OR npc_id BETWEEN 999600 AND 999799 OR spawngroup_id IN ({identities}) OR spawngroup_id BETWEEN 999600 AND 999799 OR spawn2_id IN (SELECT id FROM spawn2 WHERE spawngroupID IN ({identities}) OR spawngroupID BETWEEN 999600 AND 999799))',
    }
    before = {table: rows(table, scope) for table, scope in scopes.items()}
    # All use existing Classic appearance tuples proven in EC.
    templates = rows('npc_types', 'id IN (22033,22087,22092,22083,22082,22116,22088,22086,22118,22073)')
    objects = rows('object', 'id IN (103173,103174,103175,103180,103183,103187)')
    return dict(schemas=schemas, scopes=scopes, rows=before, source=dict(
        spells=spells, merchants=merchants, stock=stock, items=items, templates=templates,
        objects=objects), status='read_only_local_capture_not_production_preimage')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--container', default='akk-stack-mariadb-1')
    p.add_argument('--root-env',action='store_true',help='Use the container existing root-password environment for an on-host read-only capture')
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise ValueError('Refusing to overwrite source evidence')
    data = capture(a.container,a.root_env)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(data, separators=(',', ':'))+'\n')
    print(json.dumps({k:len(v) for k,v in data['source'].items()}))
