"""Compose companion effects, sourced item parity and preserved starter budgets."""
from copy import deepcopy
from decimal import Decimal
import gzip,json
from pathlib import Path
import pet_content,wpm_content,starter_retune,thj_item_parity
from dungeon_catalog import legacy_items as dungeon_items

ROOT=Path(__file__).resolve().parents[1]
RELEASE=ROOT/'docs/releases/thj-parity-20261018/content'

def capture():
    return json.loads(gzip.decompress((ROOT/'tools/fixtures/thj-combined-preimages-20261018.json.gz').read_bytes()))

def same(actual,expected):
    if actual is None or expected is None:return actual is expected
    if isinstance(expected,(int,float)):
        try:return Decimal(str(actual))==Decimal(str(expected))
        except Exception:return False
    return str(actual)==str(expected)

def original_items():
    rows={}
    for source in capture()['tables']['items']:
        row=dict(source);row['id']=int(row['id'])
        for field in thj_item_parity.FIELDS:
            if field in row:row[field]=int(row[field])
        rows[row['id']]=row
    return rows

def after_companions(before):
    result=deepcopy(before)
    for module in (pet_content,wpm_content):
        for old,new in module.gear_changes():
            row=result[old['id']]
            for field,value in new.items():
                if value==old[field]:continue
                if not same(row[field],old[field]):
                    raise ValueError(f'Companion overlap/preimage drift: {old["id"]}/{field}')
                row[field]=value
    return result

def proposed_items(before):
    result=thj_item_parity.propose(before)
    reference=json.loads((ROOT/'docs/items/starter-retune-reference.json').read_text(encoding='utf-8'))
    original=dungeon_items()
    starter,dungeon=starter_retune.propose(reference,original)
    thj_ids={t['base_id']+o for t in thj_item_parity.catalog()['items'] for o in (0,200000,400000,600000,800000)}
    if thj_ids & set(starter):raise ValueError('Starter exemption overlaps THJ target')
    pairs=[(row,starter[row['id']]) for f in reference['families'] for row in f['tiers']]
    pairs.extend((old['values'],new['values']) for old,new in zip(original,dungeon))
    for old,new in pairs:
        row=result[old['id']]
        for field,value in old.items():
            if not same(row[field],value):raise ValueError(f'Starter/dungeon preimage drift: {old["id"]}/{field}: {row[field]} != {value}')
        for field,value in new.items():
            if value!=old[field]:row[field]=value
    return result

def item_changes():
    before=original_items()
    after=proposed_items(after_companions(before))
    return [(before[i],r) for i,r in sorted(after.items()) if any(not same(before[i][k],v) for k,v in r.items())]

def recovery_changes():
    # Keep companion effects/sockets: owned augment instances may occupy them.
    baseline=after_companions(original_items());final=proposed_items(baseline)
    return [(final[i],r) for i,r in sorted(baseline.items()) if any(not same(final[i][k],v) for k,v in r.items())]

if __name__=='__main__':
    from thj_item_migration import migration
    RELEASE.mkdir(parents=True,exist_ok=True)
    pairs=item_changes()
    columns=capture()['schemas']['items']['columns']
    for rollback in (False,True):
        selected=recovery_changes() if rollback else pairs
        alternate=None if rollback else after_companions(original_items())
        (RELEASE/('items-rollback.sql' if rollback else 'items-forward.sql')).write_text(migration(selected,columns,alternate),encoding='utf-8')
    (RELEASE/'pet-content-forward.sql').write_text(pet_content.migration(include_gear=False),encoding='utf-8')
    from wpm_migration import migration as group_migration
    (RELEASE/'wpm-content-forward.sql').write_text(group_migration(wpm_content.groups(include_gear=False),'nightcap_wpm_items_20261018'),encoding='utf-8')
    rules=[{'ruleset_id':1,'rule_name':'Spells:'+name,'rule_value':'true','notes':note} for name,note in (
        ('NightcapTHJDamageScaling','Player/permanent-pet item SD adds to direct damage; half SD per DoT tick before native critical ratio. Healing retains its separate legacy policy'),
        ('NightcapHeroicSpellScaling','Player heroic INT/WIS add 0.1 percent per point to final direct damage/healing; excludes DoTs and HoTs'))]
    existing=capture()['tables']['rule_values']
    for mode in ('forward','disable','enable'):
        groups=[]
        for row in rules:
            key={k:row[k] for k in ('ruleset_id','rule_name')}
            old=[r for r in existing if int(r['ruleset_id'])==1 and r['rule_name']==row['rule_name']] if mode=='forward' else [dict(row,rule_value='true' if mode=='disable' else 'false')]
            if mode=='forward' and old:raise ValueError('New spell rule already occupied')
            groups.append(dict(table='rule_values',key=key,before=old,after=[dict(row,rule_value='false' if mode=='disable' else 'true')]))
        (RELEASE/f'rules-{mode}.sql').write_text(group_migration(groups,'nightcap_thj_rules_20261018'),encoding='utf-8')
    changes=[{'id':old['id'],'name':old['Name'],'fields':{k:{'old':old[k],'new':v} for k,v in new.items() if not same(old[k],v)}} for old,new in pairs]
    (RELEASE/'item-deltas.json').write_text(json.dumps(changes,indent=2)+'\n',encoding='utf-8')
    print('Combined changed definitions:',len(pairs))
