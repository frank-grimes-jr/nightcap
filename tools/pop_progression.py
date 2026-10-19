"""Stage earned level-65/PoP access and audited native-vendor scroll additions.

This generator never connects, installs, grants levels, or edits character data.
The live Classic profile remains selected until the complete release is activated.
"""
import argparse
import gzip
import json
from pathlib import Path
from rabid_bear import predicate,sql_value
from pet_content import insert
from generate_pet_spell_catalog import SOURCE_SHA256

ROOT=Path(__file__).resolve().parents[1]
RELEASE=ROOT/'docs/releases/thj-pet-scaling-20261018/content/progression'
FIXTURE=ROOT/'tools/fixtures/pop-progression-20261018.json.gz'
PROFILE=dict(expansion=4,name='Planes of Power',max_level=65,aa_open=True,aa_policy='config/aa-policy.json',luclin_models=False)


def snapshot(): return json.loads(gzip.decompress(FIXTURE.read_bytes()))


def additions(data=None):
    data=data or snapshot()
    if data['original_spells_sha256']!=SOURCE_SHA256: raise ValueError('Original spell source drift')
    spells=data['original_spells'];items={}
    for row in data['tables']['items']:
        sid=row['scrolleffect'];entry=spells.get(str(sid))
        if row['itemtype']!=20 or not entry or len(entry['levels'])!=16: raise ValueError('Invalid native-vendor scroll')
        if not 0<row['id']<=1048575: raise ValueError('Scroll exceeds client item-link limit')
        if sid not in items or row['id']<items[sid]['id']: items[sid]=row
    result=[]
    for cid in range(1,17):
        merchant=99299+cid
        current=[r for r in data['tables']['merchantlist'] if r['merchantid']==merchant]
        if not current: raise ValueError('Missing class merchant')
        existing={r['item'] for r in current};slot=max(r['slot'] for r in current)
        stock=json.loads((ROOT/'docs/pok/hub-stock-audit.json').read_text())['stock']
        existing_spells={r['spell_id'] for r in stock if r['item_id'] in existing}
        selected=[r for sid,r in items.items() if 51<=spells[str(sid)]['levels'][cid-1]<=65 and r['id'] not in existing and sid not in existing_spells]
        selected.sort(key=lambda r:(spells[str(r['scrolleffect'])]['levels'][cid-1],r['Name'],r['id']))
        for item in selected:
            slot+=1
            if slot>500: raise ValueError('RoF2 class merchant exceeds 500 slots')
            # The class hub retains its existing faction/status/pricing contract.
            row=dict(current[0],slot=slot,item=item['id'])
            result.append(row)
    return result


def migration(set_rules=True):
    data=snapshot();rows=additions(data)
    lines=['DELIMITER //','CREATE PROCEDURE nightcap_pop_progression_20261018()','BEGIN',
           ' DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;',
           ' SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;',' START TRANSACTION;']
    for table in ('merchantlist','rule_values'):
        lines.append(f" IF (SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='{table}' AND ENGINE='InnoDB')<>1 OR EXISTS (SELECT 1 FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=DATABASE() AND EVENT_OBJECT_TABLE='{table}') THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Unexpected progression storage'; END IF;")
    for npc in data['tables']['npc_types']:
        if 997900<=npc['id']<=997915:
            identity={k:npc[k] for k in ('id','name','merchant_id','class')}
            lines.append(f" IF NOT EXISTS (SELECT 1 FROM npc_types WHERE {predicate(identity)}) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Class merchant identity drift'; END IF;")
    # Require every existing row, including its restrictions, before adding stock.
    baseline=data['tables']['merchantlist']
    # Reject unknown destinations as well as changed existing rows. A rerun may
    # contain any subset of our exact afterimages, but no unrelated new stock.
    for cid in range(1,17):
        merchant=99299+cid
        allowed=[r for r in baseline+rows if r['merchantid']==merchant]
        slots=','.join(str(r['slot']) for r in allowed)
        lines.append(f" IF EXISTS (SELECT 1 FROM merchantlist WHERE merchantid={merchant} AND slot NOT IN ({slots}) FOR UPDATE) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Unknown hub stock destination'; END IF;")
    for start in range(0,len(baseline),50):
        batch=baseline[start:start+50]
        where=' OR '.join('('+predicate(r)+')' for r in batch)
        lines.append(f" IF (SELECT COUNT(*) FROM merchantlist WHERE {where} FOR UPDATE)<>{len(batch)} THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Existing hub stock drift'; END IF;")
    used={r['item'] for r in rows}
    for item in data['tables']['items']:
        if item['id'] not in used: continue
        lines.append(f" IF NOT EXISTS (SELECT 1 FROM items WHERE {predicate(item)}) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='PoP scroll definition drift'; END IF;")
        spell=data['original_spells'][str(item['scrolleffect'])]
        identity={'id':item['scrolleffect'],'name':spell['name']}
        lines.append(f" IF NOT EXISTS (SELECT 1 FROM spells_new WHERE {predicate(identity)}) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='PoP spell identity drift'; END IF;")
    for old in data['tables']['rule_values']:
        value='4' if old['rule_name']=='Expansion:CurrentExpansion' else '65'
        after=dict(old,rule_value=value)
        if set_rules:
            lines += [f' IF NOT EXISTS (SELECT 1 FROM rule_values WHERE {predicate(after)}) THEN',
                      f"  IF NOT EXISTS (SELECT 1 FROM rule_values WHERE {predicate(old)} FOR UPDATE) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Era rule preimage drift'; END IF;",
                      f"  UPDATE rule_values SET rule_value={sql_value(value)} WHERE ruleset_id=1 AND rule_name={sql_value(old['rule_name'])};",' END IF;']
        else:
            lines.append(f" IF NOT EXISTS (SELECT 1 FROM rule_values WHERE {predicate(after)}) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='PoP restock requires its paired era profile'; END IF;")
    for row in rows:
        key={k:row[k] for k in ('merchantid','slot')}
        lines += [f' IF NOT EXISTS (SELECT 1 FROM merchantlist WHERE {predicate(row)}) THEN',
                  f"  IF EXISTS (SELECT 1 FROM merchantlist WHERE {predicate(key)} FOR UPDATE) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='PoP merchant destination occupied'; END IF;",
                  '  '+insert('merchantlist',row),' END IF;']
    lines += [' COMMIT;','END//','DELIMITER ;','CALL nightcap_pop_progression_20261018();','DROP PROCEDURE nightcap_pop_progression_20261018;','']
    return '\n'.join(lines)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=RELEASE)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    data=snapshot();rows=additions(data)
    (args.output/'forward.sql').write_text(migration(),encoding='utf-8',newline='\n')
    (args.output/'vendor_restock.sql').write_text(migration(False),encoding='utf-8',newline='\n')
    (args.output/'era.json').write_text(json.dumps(PROFILE,indent=2)+'\n')
    policy=json.loads((ROOT/'docs/pok/catalog-policy.json').read_text())
    policy.update(expansion=4,max_level=65,source='pop-progression-20261018.json.gz')
    policy['merchants']=[dict(npc_id=r['id'],merchant_id=r['merchant_id'],name=r['name'])
                         for r in sorted(data['tables']['npc_types'],key=lambda r:r['id'])
                         if 997900<=r['id']<=997915]
    (args.output/'catalog-policy.json').write_text(json.dumps(policy,indent=2)+'\n')
    report={'status':'staged_not_activated','captured_utc':data['captured_utc'],
            'level_grants':0,'existing_stock_preserved':len(data['tables']['merchantlist']),
            'new_stock_rows':len(rows),'new_unique_scrolls':len({r['item'] for r in rows}),
            'source':'Existing native vendors/spawns available through expansion 4, original class levels 51..65.',
            'new_rows_by_class':{str(cid):sum(r['merchantid']==99299+cid for r in rows) for cid in range(1,17)},
            'early_mage_epic':'Manifest Elements retains canonical Mage level 59; no free epic or level bypass.',
            'activation_gates':['paired world/zone/client/cache','native travel and encounter QA','fresh preservation preflight','guarded maintenance activation'],
            'rollback':'Preserve earned levels, spellbooks, items and AAs. Do not de-level characters or restore old snapshots.'}
    (args.output/'plan.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))


if __name__=='__main__':main()
