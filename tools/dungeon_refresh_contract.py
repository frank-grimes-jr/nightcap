"""Compile current reward guards without rewriting historical installation SQL.

Preserve rehearsed schema and current reviewed non-item predicates. No database
access, activation or live-derived acceptance hashes. Build matching zone guards
for the reviewed target cache; run SQL/cache checks before activation.
"""
import json
import re
from pathlib import Path
from dungeon_catalog import items
from dungeon_contract import predicate, render_header
from hate_keeper import refresh_contract

ROOT=Path(__file__).resolve().parents[1]

def expedition_augments(contract, custom):
    # Apply reviewed release deltas; never learn acceptance from mutable live rows.
    audit=json.loads((ROOT/'docs/audits/augments-20261106/item-preimages.json').read_text())
    updates=[r for r in audit if r['zone'] in ('chapterhouse','kael')]
    assert len(updates)==8 and len({r['before']['id'] for r in updates})==8
    definitions={r['values']['id']:r['values'] for r in custom}
    for release in updates:
        item=definitions[int(release['before']['id'])]
        prefix='vigil' if release['zone']=='chapterhouse' else 'compact'
        for field,after in release['after'].items():
            before=release['before'][field]
            if before==after: continue
            assert str(item.get(field,0))==before,(item['id'],field,'Compiler preimage drift')
            value=after if field=='lore' else int(after)
            old_term=predicate({field:item.get(field,0)})[1:-1]
            new_term=predicate({field:value})[1:-1]
            matches=0
            for check in contract['content']:
                if not check['label'].startswith(prefix+'/items/'): continue
                clauses=check['sql'].split(' OR ')
                for i,clause in enumerate(clauses):
                    if f"`id` <=> {item['id']} AND " not in clause: continue
                    if field in item:
                        clauses[i],count=re.subn(re.escape(old_term)+r'(?= AND |\))',lambda _:new_term,clause)
                        assert count==1,(item['id'],field,'SQL preimage drift')
                    else:
                        # Inactive effects historically omitted their metadata.
                        assert f'`{field}`' not in clause and clause.endswith(')')
                        clauses[i]=clause[:-1]+' AND '+new_term+')'
                    matches+=1
                check['sql']=' OR '.join(clauses)
            assert matches==1,(item['id'],field,'Missing or duplicate item predicate')
            item[field]=value


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
    # Preserve the reviewed 223-point layout and boss landmarks, including density.
    hate=ROOT/'docs/dungeons/hate-boss-placement-20261030/runtime-checks.json'
    contract['content']=[c for c in contract['content'] if not c['label'].startswith(('hate-layout/','hate-density/'))]
    contract['content']+=json.loads(hate.read_text())
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
    expedition_augments(contract,custom)
    path.write_text(json.dumps(contract,indent=2)+'\n',encoding='utf-8',newline='\n')
    (ROOT/'server-mods/code/common/dungeon_contract.h').write_text(
        render_header(contract['schema'],contract['content'],definitions+custom),encoding='utf-8',newline='\n')
    return contract

if __name__=='__main__':
    value=refresh()
    print(json.dumps({'schema_checks':len(value['schema']),'content_checks':len(value['content'])}))
