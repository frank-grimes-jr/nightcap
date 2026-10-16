"""Extract a pinned Classic CT content closure; never execute donor SQL.

The parser accepts only mysqldump literal INSERT rows from an explicit public
content allowlist. DDL, triggers, accounts, players and executable expressions
are not imported. The resulting JSON is suitable for a separate staging DB.
"""
import argparse
import hashlib
import json
import re
import tarfile
from pathlib import Path

ARCHIVE_SHA256 = 'f49d712b45a193f737cb0f4de07fec7bf43c6c813e389ff9e7521b3915529b09'
TABLES = {'zone','spawn2','spawngroup','spawnentry','npc_types','npc_spells',
          'npc_spells_entries','npc_spells_effects','npc_spells_effects_entries',
          'loottable','loottable_entries','lootdrop','lootdrop_entries','items',
          'grid','grid_entries','doors','npc_faction','npc_faction_entries','faction_list'}
TOKEN = re.compile(r"\s*(NULL|-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?|'(?:\\.|''|[^'\\])*'|[(),;])", re.S)

def literal_rows(text):
    row = None
    position = 0
    for match in TOKEN.finditer(text):
        if text[position:match.start()].strip():
            raise ValueError('Nonliteral donor SQL')
        position = match.end()
        value = match[1]
        if value == '(':
            if row is not None: raise ValueError('Nested expression')
            row = []
        elif value == ')':
            if row is None: raise ValueError('Unexpected row end')
            yield row
            row = None
        elif value in ',;':
            continue
        else:
            if row is None: raise ValueError('Value outside row')
            if value == 'NULL': result = None
            elif value.startswith("'"):
                escapes = {'0':'\0','n':'\n','r':'\r','t':'\t','b':'\b','Z':'\x1a'}
                result = re.sub(r'\\(.)', lambda m: escapes.get(m[1],m[1]), value[1:-1]).replace("''", "'")
            else:
                result = float(value) if any(c in value.lower() for c in '.e') else int(value)
            row.append(result)
    if text[position:].strip() or row is not None: raise ValueError('Incomplete donor SQL')

def extract(path):
    assert hashlib.sha256(path.read_bytes()).hexdigest() == ARCHIVE_SHA256, 'Donor archive changed'
    with tarfile.open(path) as archive:
        sql = archive.extractfile('quarm_2023-10-01-00:19.sql').read().decode('latin1')
    tables = {}
    for name in sorted(TABLES):
        ddl = re.search(r'CREATE TABLE `'+name+r'` \((.*?)\) ENGINE=', sql, re.S)
        if not ddl: continue
        columns = re.findall(r'^  `([^`]+)`', ddl[1], re.M)
        rows = []
        for insert in re.finditer(r'^INSERT INTO `'+name+r'` VALUES (.*);$',sql,re.M):
            for values in literal_rows(insert[1]):
                assert len(values)==len(columns), name
                rows.append(dict(zip(columns,values)))
        tables[name] = rows
    def selected(table, predicate):
        return [r for r in tables.get(table,[]) if predicate(r)]
    def classic(row):
        # Quarm uses 1 for Classic (Nightcap uses 0). The archive explicitly
        # disables its Classic Avatar point; this private restoration enables
        # only that audited point, never the level-60 revamp population.
        return row.get('min_expansion',0)<=1 and (
            row.get('enabled',1)==1 or row.get('id')==11448207)
    out = {'zone': selected('zone',lambda r:r['short_name']=='cazicthule'),
           'spawn2':selected('spawn2',lambda r:r['zone']=='cazicthule' and classic(r)),
           'doors':selected('doors',lambda r:r['zone']=='cazicthule' and classic(r))}
    groups={r['spawngroupID'] for r in out['spawn2']}
    out['spawngroup']=selected('spawngroup',lambda r:r['id'] in groups)
    out['spawnentry']=selected('spawnentry',lambda r:r['spawngroupID'] in groups and classic(r))
    npcs={r['npcID'] for r in out['spawnentry']}
    out['npc_types']=selected('npc_types',lambda r:r['id'] in npcs)
    for table, parent, field in [('loottable','npc_types','loottable_id'),
                                ('npc_spells','npc_types','npc_spells_id'),
                                ('npc_spells_effects','npc_types','npc_spells_effects_id'),
                                ('npc_faction','npc_types','npc_faction_id')]:
        ids={r[field] for r in out[parent]}-{0}
        if table=='npc_spells':
            while True:
                extended=ids|{r['parent_list'] for r in tables[table] if r['id'] in ids}-{0}
                if extended==ids: break
                ids=extended
        out[table]=selected(table,lambda r:r['id'] in ids)
    for table,parent,field in [('loottable_entries','loottable','loottable_id'),
                               ('npc_spells_entries','npc_spells','npc_spells_id'),
                               ('npc_spells_effects_entries','npc_spells_effects','npc_spells_effects_id'),
                               ('npc_faction_entries','npc_faction','npc_faction_id')]:
        ids={r['id'] for r in out[parent]}
        out[table]=selected(table,lambda r:r[field] in ids)
    ids={r['lootdrop_id'] for r in out['loottable_entries']}
    out['lootdrop']=selected('lootdrop',lambda r:r['id'] in ids)
    out['lootdrop_entries']=selected('lootdrop_entries',lambda r:r['lootdrop_id'] in ids and classic(r))
    ids={r['item_id'] for r in out['lootdrop_entries']}|{r['keyitem'] for r in out['doors']}|{r['altkeyitem'] for r in out['doors']}
    out['items']=selected('items',lambda r:r['id'] in ids)
    ids={r['faction_id'] for r in out['npc_faction_entries']}
    out['faction_list']=selected('faction_list',lambda r:r['id'] in ids)
    grids={r['pathgrid'] for r in out['spawn2']}-{0}
    out['grid']=selected('grid',lambda r:r['zoneid']==48 and r['id'] in grids)
    out['grid_entries']=selected('grid_entries',lambda r:r['zoneid']==48 and r['gridid'] in grids)
    assert len(out['zone'])==1
    assert any(r['name']=='Avatar_of_Fear' and r['level']==39 for r in out['npc_types']), 'Missing Classic Avatar'
    out['source']={'archive_sha256':ARCHIVE_SHA256,'git_blob':'6317bb5055c128bd7fe0a10e086391b84618e03c',
                   'url':'https://github.com/SecretsOTheP/EQMacEmu/blob/main/utils/sql/database_full/quarm_2023-10-01-00_19.tar.gz'}
    return out

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    data=extract(args.archive)
    args.output.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({k:len(v) for k,v in data.items() if isinstance(v,list)}))
