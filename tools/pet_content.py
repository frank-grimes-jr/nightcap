"""Generate reviewed pet/WPM content; offline only, with guarded activation SQL."""
import argparse
import gzip
import json
from pathlib import Path
from rabid_bear import predicate, sql_value

ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / 'docs/releases/thj-pet-scaling-20261018/content'
FIXTURE = ROOT / 'tools/fixtures/pet-content-20261018.json.gz'
BASE_IDS = (180610, 180611)
SPELL_IDS = tuple(range(42830, 42838))
WEAPONS = (20627, 22946, 26740, 31232)
DROP_ID = 988610
QUALITIES = ('', ' (Polished)', ' (Exalted)', ' (Ascended)')
# Calibration uses canonical EQ heal/rune magnitudes, not asserted THJ numbers.
HEALS = (95, 175, 250, 350)
RUNES = (55, 118, 168, 230)


def snapshot():
    return json.loads(gzip.decompress(FIXTURE.read_bytes()))


def spell_rows():
    originals = {r['id']: r for r in snapshot()['tables']['spells_new']}
    output = []
    for tier in range(4):
        for kind in range(2):
            row = dict(originals[481 if kind else 12])
            row.update(id=42830 + tier * 2 + kind, name=('Runic' if kind else 'Healing') + f' Fragment {tier+1}',
                       targettype=6, mana=0, cast_time=0, recovery_time=0, recast_time=0,
                       buffdurationformula=4 if kind else 0, buffduration=10 if kind else 0,
                       short_buff_box=0, goodEffect=1, spellgroup=42830 + kind)
            for i in range(1, 17): row[f'classes{i}'] = 255
            for i in range(1, 5):
                row[f'components{i}'] = -1
                row[f'component_counts{i}'] = 1
                row[f'NoexpendReagent{i}'] = -1
            row.update(effectid1=55 if kind else 0, effect_base_value1=(RUNES if kind else HEALS)[tier],
                       effect_limit_value1=0, formula1=100, max1=0)
            if set(row) != set(originals[12]): raise ValueError('Unexpected spell column name')
            output.append(row)
    return output


def item_rows():
    template = next(r for r in snapshot()['tables']['items'] if r['id'] == 51722)
    output = []
    for tier in range(4):
        for kind in range(2):
            row = dict(template)
            row.update(id=BASE_IDS[kind] + tier*200000,
                       Name=('Runic' if kind else 'Healing') + ' Fragment of Truth' + QUALITIES[tier],
                       lore='Nightcap combat fragment', loregroup=0, price=0, sellrate=0,
                       augtype=136, augrestrict=2, proceffect=42830+tier*2+kind,
                       procname=('Runic' if kind else 'Healing') + f' Fragment {tier+1}',
                       proctype=0, proclevel=1, proclevel2=1, procrate=0, reqlevel=0, reclevel=0,
                       classes=65535, races=65535, nopet=0, norent=1, nodrop=1,
                       comment='Nightcap THJ pet scaling calibration 20261018',
                       serialized=None, serialization=None)
            output.append(row)
    return output


def gear_changes():
    targets = json.loads((RELEASE / 'pet-gear-targets.json').read_text())['targets']
    rows = snapshot()['tables']['items']
    found, changes = set(), []
    for original in rows:
        after = dict(original)
        if original['Name'].endswith(' (Ascended)'):
            name = original['Name'].removesuffix(' (Ascended)')
            if name in targets:
                found.add(name)
                for key, value in targets[name].items(): after[key] = max(original[key], value)
        if original['id'] % 200000 in WEAPONS:
            sockets = [original[f'augslot{i}type'] for i in range(1,7)]
            if len([v for v in sockets if v in (4,8)]) != 1:
                raise ValueError('Unexpected combat sockets: '+original['Name'])
            free = next((i for i in range(1,7) if original[f'augslot{i}type']==0), None)
            if free is None: raise ValueError('No free combat socket')
            after[f'augslot{free}type'] = next(v for v in sockets if v in (4,8))
            after[f'augslot{free}visible'] = 1
        if original != after: changes.append((original,after))
    if found != set(targets): raise ValueError('Missing guide item families: '+str(set(targets)-found))
    return changes


def insert(table, row):
    return 'INSERT INTO '+table+' ('+','.join('`'+k+'`' for k in row)+') VALUES ('+','.join(sql_value(v) for v in row.values())+');'


def new_rows():
    result = [('spells_new', r, {'id':r['id']}) for r in spell_rows()]
    result += [('items', r, {'id':r['id']}) for r in item_rows()]
    result.append(('lootdrop', dict(id=DROP_ID,name='Nightcap fragments of truth',min_expansion=3,max_expansion=-1,
                                   content_flags=None,content_flags_disabled=None), {'id':DROP_ID}))
    for tier, chance in enumerate((30,15,4,1)):
        for kind in range(2):
            row = dict(lootdrop_id=DROP_ID,item_id=BASE_IDS[kind]+tier*200000,item_charges=1,equip_item=0,
                       chance=chance,disabled_chance=0,trivial_min_level=0,trivial_max_level=0,multiplier=1,
                       npc_min_level=0,npc_max_level=0,min_expansion=3,max_expansion=-1,
                       content_flags=None,content_flags_disabled=None)
            result.append(('lootdrop_entries',row,{'lootdrop_id':DROP_ID,'item_id':row['item_id']}))
    # This is the captured Seru template with an existing populated loot table.
    row = dict(loottable_id=13516,lootdrop_id=DROP_ID,multiplier=1,droplimit=1,mindrop=1,probability=100)
    result.append(('loottable_entries',row,{'loottable_id':13516,'lootdrop_id':DROP_ID}))
    return result


def migration(acquisition_rollback=False):
    lines=['DELIMITER //','CREATE PROCEDURE nightcap_pet_content_20261018()','BEGIN',
           ' DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;',
           ' SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;',' START TRANSACTION;']
    link = new_rows()[-1][1]
    tables=('loottable_entries',) if acquisition_rollback else ('items','spells_new','lootdrop','lootdrop_entries','loottable_entries')
    for table in tables:
        lines.append(f" IF (SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='{table}' AND ENGINE='InnoDB')<>1 OR EXISTS (SELECT 1 FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=DATABASE() AND EVENT_OBJECT_TABLE='{table}') THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Unexpected content storage'; END IF;")
    if acquisition_rollback:
        lines += [f' IF EXISTS (SELECT 1 FROM loottable_entries WHERE lootdrop_id={DROP_ID}) THEN',
                  f"  IF (SELECT COUNT(*) FROM loottable_entries WHERE {predicate(link)})<>1 OR (SELECT COUNT(*) FROM loottable_entries WHERE lootdrop_id={DROP_ID})<>1 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Fragment acquisition drift'; END IF;",
                  f'  DELETE FROM loottable_entries WHERE {predicate(link)};', ' END IF;']
    else:
        npc=next(r for r in snapshot()['tables']['npc_types'] if r['id']==159691)
        identity={k:npc[k] for k in ('id','name','loottable_id')}
        lines.append(f" IF NOT EXISTS (SELECT 1 FROM npc_types WHERE {predicate(identity)}) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Seru identity drift'; END IF;")
        baseline=snapshot()['tables']['loottable_entries']
        # The coordinated WPM migration owns this additional Seru drop. Permit
        # its exact row on retry without requiring or creating it here.
        wpm_link=dict(loottable_id=13516,lootdrop_id=988622,multiplier=1,droplimit=1,mindrop=1,probability=100)
        allowed=' OR '.join('('+predicate(r)+')' for r in baseline+[link,wpm_link])
        lines.append(f" IF EXISTS (SELECT 1 FROM loottable_entries WHERE (loottable_id=13516 OR lootdrop_id={DROP_ID}) AND NOT ({allowed}) FOR UPDATE) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Seru acquisition drift'; END IF;")
        for row in baseline:
            lines.append(f" IF NOT EXISTS (SELECT 1 FROM loottable_entries WHERE {predicate(row)} FOR UPDATE) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Seru original loot drift'; END IF;")
        ids=','.join(str(r['id']) for r in item_rows())
        lines.append(f" IF EXISTS (SELECT 1 FROM lootdrop_entries WHERE lootdrop_id={DROP_ID} AND item_id NOT IN ({ids}) FOR UPDATE) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Fragment drop has unexpected items'; END IF;")
        for original, after in gear_changes():
            lines += [f' IF NOT EXISTS (SELECT 1 FROM items WHERE {predicate(after)}) THEN',
                      f"  IF NOT EXISTS (SELECT 1 FROM items WHERE {predicate(original)} FOR UPDATE) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Guide gear preimage drift'; END IF;",
                      '  UPDATE items SET '+','.join('`'+k+'`='+sql_value(v) for k,v in after.items() if v!=original[k])+f" WHERE id={after['id']};",' END IF;']
        for table,row,key in new_rows():
            lines += [f' IF NOT EXISTS (SELECT 1 FROM {table} WHERE {predicate(row)}) THEN',
                      f"  IF EXISTS (SELECT 1 FROM {table} WHERE {predicate(key)} FOR UPDATE) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Occupied fragment identity'; END IF;",
                      '  '+insert(table,row),' END IF;']
    lines += [' COMMIT;','END//','DELIMITER ;','CALL nightcap_pet_content_20261018();','DROP PROCEDURE nightcap_pet_content_20261018;','']
    return '\n'.join(lines)


def client_rows():
    return {str(r['id']): '^'.join('' if v is None else str(v) for v in r.values()) for r in spell_rows()}


def client_spells(raw):
    expected=client_rows(); seen=set(); output=[]
    for line in raw.decode('latin1').splitlines():
        fields=line.split('^')
        if len(fields)!=237 or fields[0] in seen: raise ValueError('Malformed or duplicate client spell')
        seen.add(fields[0])
        if fields[0] in expected and line!=expected[fields[0]]: raise ValueError('Fragment client identity drift')
        output.append(line)
    output.extend(row for sid,row in expected.items() if sid not in seen)
    return ('\r\n'.join(output)+'\r\n').encode('latin1')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=RELEASE)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    for rollback in (False,True):
        name='pet-content-acquisition-rollback.sql' if rollback else 'pet-content-forward.sql'
        (args.output/name).write_text(migration(rollback),encoding='utf-8',newline='\n')
    print(json.dumps({'status':'generated_not_applied','new_items':len(item_rows()),'new_spells':len(spell_rows()),'gear_definitions':len(gear_changes())}))


if __name__=='__main__': main()
