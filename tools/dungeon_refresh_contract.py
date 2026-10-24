"""Compile current reward guards without rewriting historical installation SQL.

Preserve the rehearsed schema and every non-item predicate. No database access,
activation, or live-derived acceptance hashes. A paired zone/cache release is
required; run the generated SQL checks against the target before activation.
"""
import json
from pathlib import Path
from dungeon_catalog import items
from dungeon_contract import predicate, render_header
from hate_keeper import refresh_contract

ROOT=Path(__file__).resolve().parents[1]

def refresh():
    path=ROOT/'docs/dungeons/runtime-contract.json'
    contract=json.loads(path.read_text())
    definitions=items()
    from chapterhouse_content import compile_rows
    custom = [dict(values=r) for r in compile_rows()['items']]
    rows=[r['values'] for r in definitions]
    checks=[dict(label=f'items/{i}',
                 sql='SELECT COUNT(*) FROM `items` WHERE '+' OR '.join(predicate(r) for r in rows[i:i+8]),
                 expected=str(len(rows[i:i+8]))) for i in range(0,len(rows),8)]
    old=contract['content']; first=next(i for i,c in enumerate(old) if c['label'].startswith('items/'))
    contract['content']=old[:first]+checks+[c for c in old[first:] if not c['label'].startswith('items/')]
    expansion=ROOT/'docs/dungeons/classic-expansion-20261022/runtime-checks.json'
    if expansion.exists():
        contract['content']=[c for c in contract['content'] if not c['label'].startswith('classic/')]
        contract['content']+=json.loads(expansion.read_text())
    rewards=ROOT/'docs/dungeons/classic-rewards-20261022/runtime-checks.json'
    if rewards.exists():
        contract['content']=[c for c in contract['content'] if not c['label'].startswith('rewards/')]
        contract['content']+=json.loads(rewards.read_text())
    contract=refresh_contract(contract)
    vigil=ROOT/'docs/quests/camil-chapterhouse/runtime-checks.json'
    contract['content']=[c for c in contract['content'] if not c['label'].startswith('vigil/')]
    contract['content']+=json.loads(vigil.read_text())
    contract['schema']=[c for c in contract['schema'] if not c['label'].startswith('nightcap_vigil_')]
    contract['schema']+=json.loads((vigil.parent/'schema-checks.json').read_text())
    from warhelm_content import compile_rows as warhelm_rows
    ashen=ROOT/'docs/quests/warhelm'
    custom += [dict(values=r) for r in warhelm_rows()['items']]
    contract['content']=[c for c in contract['content'] if not c['label'].startswith('compact/')]
    contract['content']+=json.loads((ashen/'runtime-checks.json').read_text())
    contract['schema']=[c for c in contract['schema'] if not c['label'].startswith('nightcap_ashen_')]
    contract['schema']+=json.loads((ashen/'schema-checks.json').read_text())
    path.write_text(json.dumps(contract,indent=2)+'\n',encoding='utf-8',newline='\n')
    (ROOT/'server-mods/code/common/dungeon_contract.h').write_text(
        render_header(contract['schema'],contract['content'],definitions+custom),encoding='utf-8',newline='\n')
    return contract

if __name__=='__main__':
    value=refresh()
    print(json.dumps({'schema_checks':len(value['schema']),'content_checks':len(value['content'])}))
