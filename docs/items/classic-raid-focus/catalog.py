"""Apply the approved worn and focus tuples to existing stock definitions."""
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
# Each family receives a single effect at every quality. These are the actual
# stock spell IDs. Existing same-category gear effects retain native selection.
POLICY={1552:2343,1240:2349,20705:3889,14337:2337,11611:2346,11624:3889}
FIELDS=('worneffect','worntype','wornlevel','wornlevel2','focuseffect','focustype','focuslevel','focuslevel2')


def changes():
    audit=json.loads((HERE/'audit.json').read_bytes())
    rows={}
    for base,effect in POLICY.items():
        for tier in range(4):
            key=base+200000*tier
            record=next(row for row in audit['items'] if int(row['id'])==key)
            source=tuple(int(record[f]) for f in FIELDS)
            assert source==(-1,0,0,0,-1,0,0,0)
            target=(effect,2,0,0,*source[4:]) if effect==3889 else (*source[:4],effect,6,0,0)
            rows[key]=(record,source,target)
    return rows


def generate(action):
    if action not in ('before','forward','verify','rollback'):
        raise ValueError(action)
    sql=['START TRANSACTION;','CREATE TEMPORARY TABLE raid_focus_guard(ok TINYINT NOT NULL CHECK(ok=1));']
    for key,(row,before,after) in changes().items():
        if action=='rollback':before,after=after,before
        anchor=f"id={key} AND BINARY Name=X'{row['Name'].encode().hex()}'"
        for f in ('classes','slots','itemtype','clickeffect','proceffect','scrolleffect','bardeffect','haste'):
            anchor+=f" AND {f}={int(row[f])}"
        def matches(values):
            return ' AND '.join(f'{f}={v}' for f,v in zip(FIELDS,values,strict=True))
        a,b=matches(before),matches(after)
        allowed=b if action=='verify' else a if action=='before' else f'(({a}) OR ({b}))'
        sql.append(f'INSERT INTO raid_focus_guard SELECT COUNT(*)=1 FROM items WHERE {anchor} AND {allowed} FOR UPDATE;')
        if action in ('forward','rollback'):
            fields=','.join(f'{f}={end}' for f,start,end in zip(FIELDS,before,after,strict=True) if start!=end)
            sql.append(f'UPDATE items SET {fields} WHERE {anchor} AND {a};')
            sql.append(f'INSERT INTO raid_focus_guard SELECT COUNT(*)=1 FROM items WHERE {anchor} AND {b};')
    return '\n'.join(sql+['COMMIT;','DROP TEMPORARY TABLE raid_focus_guard;'])
