"""Guarded empty-slot focus/worn additions to existing stock item definitions."""
import gzip,json
from functools import lru_cache
from pathlib import Path
HERE=Path(__file__).resolve().parent
FLOAT_COLUMNS={'items': ['sellrate'], 'zone': ['safe_x', 'safe_y', 'safe_z', 'safe_heading', 'graveyard_id', 'underworld', 'minclip', 'maxclip', 'fog_minclip', 'fog_maxclip', 'walkspeed', 'fog_minclip1', 'fog_maxclip1', 'fog_minclip2', 'fog_maxclip2', 'fog_minclip3', 'fog_maxclip3', 'fog_minclip4', 'fog_maxclip4', 'fog_density', 'gravity']}
FIELDS=('worneffect','worntype','wornlevel','wornlevel2','focuseffect','focustype','focuslevel','focuslevel2')

@lru_cache(maxsize=1)
def changes():
    data=json.loads(gzip.decompress((HERE/'targets.json.gz').read_bytes()))
    items={r['id']:r for r in data['items']}
    policy=json.loads((HERE/'policy.json').read_text())['families']
    result={}
    for key,entry in policy.items():
        base=int(key)
        for tier in range(4):
            row=items[base+200000*tier]
            before=tuple(row[f] for f in FIELDS)
            updated=list(before)
            if 'focus' in entry:
                assert before[4:]==(-1,0,0,0), (base,'occupied focus')
                updated[4:]=[entry['focus'],6,0,0]
            if 'worn' in entry:
                assert before[:4] in ((-1,0,0,0),(0,0,0,0)), (base,'occupied worn')
                updated[:4]=[entry['worn'],2,0,0]
            assert updated!=list(before)
            assert row['Name']==items[base]['Name']+('',' (Polished)',' (Exalted)',' (Ascended)')[tier]
            assert row['classes']==items[base]['classes'] and row['slots']==items[base]['slots']
            result[row['id']]=(row,before,tuple(updated))
    return result

def literal(value):
    if value is None:return 'NULL'
    if isinstance(value,(int,float)):return str(value)
    return "CONVERT(X'"+str(value).encode().hex()+"' USING utf8mb4)"

def field_literal(table,column,value):
    result=literal(value)
    return 'CAST('+result+' AS FLOAT)' if column in FLOAT_COLUMNS.get(table,()) else result

def generate(action):
    if action not in ('before','forward','verify','rollback'):raise ValueError(action)
    sql=['START TRANSACTION;','CREATE TEMPORARY TABLE classic_equipment_guard(ok TINYINT NOT NULL CHECK(ok=1));']
    for key,(row,old,new) in sorted(changes().items()):
        if action=='rollback':old,new=new,old
        # Guard every retained field, including clicks, procs, stats, restrictions
        # and all six sockets. Fail closed on concurrent content edits.
        anchor=' AND '.join(('BINARY ' if isinstance(v,str) else '')+'`'+k+'` <=> '+field_literal('items',k,v) for k,v in sorted(row.items()) if k not in FIELDS)
        def match(values):return ' AND '.join('`'+f+'`='+str(v) for f,v in zip(FIELDS,values,strict=True))
        a,b=match(old),match(new)
        allowed=b if action=='verify' else a if action=='before' else '(('+a+') OR ('+b+'))'
        sql.append('INSERT INTO classic_equipment_guard SELECT COUNT(*)=1 FROM items WHERE '+anchor+' AND '+allowed+' FOR UPDATE;')
        if action in ('forward','rollback'):
            updates=','.join('`'+f+'`='+str(v) for f,u,v in zip(FIELDS,old,new,strict=True) if u!=v)
            sql.append('UPDATE items SET '+updates+' WHERE '+anchor+' AND '+a+';')
            sql.append('INSERT INTO classic_equipment_guard SELECT COUNT(*)=1 FROM items WHERE '+anchor+' AND '+b+';')
    return '\n'.join(sql+['COMMIT;','DROP TEMPORARY TABLE classic_equipment_guard;'])
