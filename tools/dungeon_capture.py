"""Read local public content only; never capture players or change PEQ."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ZONES = ('befallen','unrest','highkeep','najena','cazicthule','permafrost','soldungb')

def query(sql):
    result = subprocess.run(['docker','exec','-i','akk-stack-mariadb-1','sh','-lc',
        'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mariadb -uroot -N -B --raw peq'],
        input='START TRANSACTION READ ONLY;\n'+sql+';\nROLLBACK;\n',
        text=True, capture_output=True, check=True)
    return [line.split('\t') for line in result.stdout.splitlines()]

def rows(table, where):
    assert table in {'spawn2','spawnentry','npc_types','spawngroup','zone','items','doors','grid','grid_entries','npc_spells','npc_spells_entries','loottable','loottable_entries','lootdrop','lootdrop_entries'}
    columns = [r[0] for r in query('SHOW COLUMNS FROM `'+table+'`')]
    expression = ','.join("'"+c+"',`"+c+'`' for c in columns)
    return [json.loads(r[0]) for r in query(f'SELECT JSON_OBJECT({expression}) FROM `{table}` WHERE {where}')]

def capture():
    quoted = ','.join("'"+z+"'" for z in ZONES)
    result = {'captured_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'environment':'local', 'scope':'public content; not a production preimage'}
    result['zone'] = rows('zone',f'short_name IN ({quoted}) AND version=0')
    result['spawn2'] = rows('spawn2',f'zone IN ({quoted}) AND version IN (0,-1)')
    group_ids = ','.join(str(r['spawngroupID']) for r in result['spawn2'])
    result['spawnentry'] = rows('spawnentry',f'spawngroupID IN ({group_ids})')
    result['spawngroup'] = rows('spawngroup',f'id IN ({group_ids})')
    npc_ids = ','.join(str(r['npcID']) for r in result['spawnentry'])
    result['npc_types'] = rows('npc_types',f'id IN ({npc_ids})')
    result['doors'] = rows('doors',f'zone IN ({quoted}) AND version IN (0,-1)')
    result['reserved_items'] = rows('items','id BETWEEN 960000 AND 960329')
    result['content_flags'] = query('SELECT flag_name,enabled FROM content_flags ORDER BY flag_name')
    return result

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    data=capture()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({'output':str(args.output),'sha256':hashlib.sha256(args.output.read_bytes()).hexdigest(),
        'rows':{k:len(v) for k,v in data.items() if isinstance(v,list)}}))
