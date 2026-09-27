"""Base-item spell/heal progression and target-captured, two-column migrations.

This tool never writes a live database. Capture is read-only; generated SQL must
be rehearsed against a clone and approved through the gameplay release gate.
"""
import argparse
from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from pathlib import Path
import subprocess

TIERS = {200000: (110,5,'Polished'), 400000: (120,12,'Exalted'),
         600000: (135,20,'Ascended'), 800000: (135,20,'Ascended')}
WEAPONS = (0,1,2,3,4,5,7,19,35,45)
ATTRIBUTES = ('astr','asta','adex','aagi','aint','awis','acha')
FIELDS = ('id','Name','slots','itemclass','bagslots','ac','hp','mana',*ATTRIBUTES,
          'damage','delay','itemtype')
STATS = ('spelldmg','healamt')

def quality(base):
    ratio = (100*max(0,base['damage'])//base['delay']
             if base['itemtype'] in WEAPONS and base['delay']>0 else 0)
    return min(100,max(0,base['hp'],base['mana'],base['ac'],
                       2*max(base[f] for f in ATTRIBUTES),ratio))

def stamp(base, ceiling):
    if base['slots']<=0 or base['itemclass']!=0 or base['bagslots']>0:
        return 0
    return ceiling*quality(base)//100

def scaled_stat(native, multiplier, bonus):
    # Keep an item's explicit drawback; a tier must not turn a negative into a boon.
    if native<0: return native
    return int((Decimal(native)*multiplier/100).quantize(Decimal(1),rounding=ROUND_HALF_UP))+bonus

def stamp_sql(alias, ceiling):
    attrs=','.join(f'{alias}.{f}' for f in ATTRIBUTES)
    weapons=','.join(map(str,WEAPONS))
    strength=(f'LEAST(100,GREATEST(0,{alias}.hp,{alias}.mana,{alias}.ac,'
              f'2*GREATEST({attrs}),IF({alias}.itemtype IN ({weapons}) AND {alias}.delay>0,'
              f'FLOOR(100*GREATEST(0,{alias}.damage)/NULLIF({alias}.delay,0)),0)))')
    return (f'IF({alias}.slots>0 AND {alias}.itemclass=0 AND {alias}.bagslots=0,'
            f'FLOOR({ceiling}*{strength}/100),0)')

def stat_sql(alias, stat, multiplier, ceiling):
    return (f'IF({alias}.{stat}<0,{alias}.{stat},'
            f'ROUND({alias}.{stat}*{multiplier}/100)+{stamp_sql(alias,ceiling)})')

def fingerprint(row, base=False):
    fields=FIELDS+STATS if base else FIELDS
    values=[row[f].encode('utf-8').hex().upper() if f=='Name' else str(row[f]) for f in fields]
    return hashlib.sha256('|'.join(values).encode()).hexdigest()

def fingerprint_sql(alias, base=False):
    fields=FIELDS+STATS if base else FIELDS
    parts=[f'HEX({alias}.Name)' if f=='Name' else f'{alias}.`{f}`' for f in fields]
    return "SHA2(CONCAT_WS('|',"+','.join(parts)+'),256)'

def plan(items):
    by_id={r['id']:r for r in items}
    if len(by_id)!=len(items): raise ValueError('Duplicate item IDs')
    result=[]
    for row in sorted(items,key=lambda r:r['id']):
        offset=(row['id']//200000)*200000
        if offset not in TIERS or row['id']>=900000 or row['slots']<=0: continue
        base=by_id.get(row['id']-offset)
        if not base: raise ValueError(f'Missing base for {row["id"]}')
        multiplier,ceiling,tag=TIERS[offset]
        if row['Name']!=base['Name']+f' ({tag})':
            raise ValueError(f'Tier identity collision at {row["id"]}')
        # Reject data which is neither the old published formula nor the new one.
        old=[row[s] for s in STATS]
        new=[scaled_stat(base[s],multiplier,stamp(base,ceiling)) for s in STATS]
        legacy=[int((Decimal(base[s])*multiplier/100).quantize(Decimal(1),rounding=ROUND_HALF_UP))
                +ceiling if base[s]>0 else base[s]+ceiling for s in STATS]
        if old not in (legacy,new): raise ValueError(f'Unexpected existing spell/heal values at {row["id"]}')
        if old!=new:
            result.append(dict(id=row['id'],base_id=base['id'],name=row['Name'],
                               base_hash=fingerprint(base,True),item_hash=fingerprint(row),old=old,new=new))
    return result

def migration_sql(rows, rollback=False):
    if not rows: raise ValueError('Empty migration')
    if len({r['id'] for r in rows})!=len(rows): raise ValueError('Duplicate migration IDs')
    lines=['-- Target-captured spell/heal migration. Do not use --force.',
           '-- Only the two named item columns change. No inventory or rules are rewritten.',
           'CREATE TEMPORARY TABLE nightcap_spell_plan (id INT PRIMARY KEY, base_id INT NOT NULL,',
           'base_hash CHAR(64) NOT NULL,item_hash CHAR(64) NOT NULL,old_d INT NOT NULL,old_h INT NOT NULL,new_d INT NOT NULL,new_h INT NOT NULL) ENGINE=InnoDB;']
    for start in range(0,len(rows),500):
        values=[]
        for row in rows[start:start+500]:
            before,after=(row['new'],row['old']) if rollback else (row['old'],row['new'])
            values.append(f"({row['id']},{row['base_id']},'{row['base_hash']}','{row['item_hash']}',{before[0]},{before[1]},{after[0]},{after[1]})")
        lines.append('INSERT INTO nightcap_spell_plan VALUES '+',\n'.join(values)+';')
    # Cursor FOR UPDATE locks both source and target rows before validating inputs.
    lines.append(f'''DELIMITER //
CREATE PROCEDURE nightcap_apply_spell_plan()
BEGIN
 DECLARE done BOOLEAN DEFAULT FALSE;
 DECLARE item_id INT;
 DECLARE locked_count INT DEFAULT 0;
 DECLARE valid_count INT DEFAULT 0;
 DECLARE locked_items CURSOR FOR SELECT a.id FROM items a
  JOIN nightcap_spell_plan p ON p.id=a.id JOIN items b ON b.id=p.base_id ORDER BY a.id FOR UPDATE;
 DECLARE CONTINUE HANDLER FOR NOT FOUND SET done=TRUE;
 DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;
 IF COALESCE((SELECT ENGINE FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name='items'),'') <> 'InnoDB' THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Items must be transactional';
 END IF;
 START TRANSACTION;
 OPEN locked_items;
 lock_rows: LOOP
  FETCH locked_items INTO item_id;
  IF done THEN LEAVE lock_rows; END IF;
  SET locked_count=locked_count+1;
 END LOOP;
 CLOSE locked_items;
 IF locked_count <> {len(rows)} THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Missing captured items'; END IF;
 SELECT COUNT(*) INTO valid_count FROM items a JOIN nightcap_spell_plan p ON p.id=a.id
  JOIN items b ON b.id=p.base_id WHERE a.spelldmg=p.old_d AND a.healamt=p.old_h
  AND {fingerprint_sql('a')}=p.item_hash AND {fingerprint_sql('b',True)}=p.base_hash;
 IF valid_count <> {len(rows)} THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Item preimage drift'; END IF;
 UPDATE items a JOIN nightcap_spell_plan p ON p.id=a.id SET a.spelldmg=p.new_d,a.healamt=p.new_h;
 SELECT COUNT(*) INTO valid_count FROM items a JOIN nightcap_spell_plan p ON p.id=a.id
  WHERE a.spelldmg=p.new_d AND a.healamt=p.new_h AND {fingerprint_sql('a')}=p.item_hash;
 IF valid_count <> {len(rows)} THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Item afterimage mismatch'; END IF;
 COMMIT;
END//
DELIMITER ;
CALL nightcap_apply_spell_plan();
DROP PROCEDURE nightcap_apply_spell_plan;
DROP TEMPORARY TABLE nightcap_spell_plan;
''')
    return '\n'.join(lines)

def capture_sql():
    pairs=','.join(f"'{f}',`{f}`" for f in FIELDS+STATS)
    return f'START TRANSACTION READ ONLY; SELECT JSON_OBJECT({pairs}) FROM items WHERE id>0 AND id<900000 AND (id<200000 OR slots>0) ORDER BY id; COMMIT;'

def bootstrap_block(table, offset, multiplier, ceiling):
    assignments=',\n      '.join(f'a.{s} = {stat_sql("b",s,multiplier,ceiling)}' for s in STATS)
    return (f'-- BEGIN GENERATED {table} SPELL SCALING\n'
            '-- Generated by tools/tier_spell_scaling.py; strength comes from the unscaled base.\n'
            f'UPDATE {table} a JOIN items b ON b.id=a.id-{offset} SET\n      {assignments};\n'
            f'-- END GENERATED {table} SPELL SCALING')

def verification_sql(include_rules=False):
    blocks=['-- Generated by tools/tier_spell_scaling.py. Every mismatch count must be zero.']
    for offset,(multiplier,ceiling,_) in TIERS.items():
        upper=min(offset+199999,899999)
        mismatches=' OR '.join(f'a.{s}<>{stat_sql("b",s,multiplier,ceiling)}' for s in STATS)
        blocks.append(f"SELECT 'tier_{offset}_mismatches' AS check_name, COUNT(*) AS result FROM items a JOIN items b ON b.id=a.id-{offset} WHERE a.id BETWEEN {offset+1} AND {upper} AND a.slots>0 AND ({mismatches});")
    if include_rules:
        blocks.extend([
            "-- Report current rules separately; this migration does not change them.",
            "SELECT 'spell_rules' AS check_name, rule_name, rule_value FROM rule_values WHERE rule_name IN ('Spells:ItemExtraSpellAmtCalcAsPercent','Spells:FlatItemExtraSpellAmt','Spells:IgnoreSpellDmgLvlRestriction','Spells:DOTsScaleWithSpellDmg','Spells:HOTsScaleWithHealAmt') ORDER BY ruleset_id,rule_name;",
            "SELECT 'item_caps' AS check_name, rule_name, rule_value FROM rule_values WHERE rule_name IN ('Character:ItemSpellDmgCap','Character:ItemHealAmtCap') ORDER BY ruleset_id,rule_name;"
        ])
    return '\n'.join(blocks)+'\n'

def sync_sql(check=False):
    root=Path(__file__).resolve().parents[1]
    path=root/'eq-solo-gm/scripts/tiered_loot_setup.sql'
    text=path.read_text(encoding='utf-8')
    for table,offset,multiplier,ceiling in [('tg','p_off','(p_offn*100)','p_spellstat'),('tge','800000','135','@ss_ascended')]:
        pattern=f'-- BEGIN GENERATED {table} SPELL SCALING.*?-- END GENERATED {table} SPELL SCALING'
        text,n=re.subn(pattern,lambda _:bootstrap_block(table,offset,multiplier,ceiling),text,flags=re.S)
        if n!=1: raise ValueError('Expected one bootstrap block for '+table)
    verify=root/'eq-solo-gm/scripts/verify_spelldmg_healamt.sql'
    for target,content in [(path,text),(verify,verification_sql(include_rules=True))]:
        if check:
            if target.read_text(encoding='utf-8')!=content: raise ValueError('Generated SQL drift: '+str(target))
        else: target.write_text(content,encoding='utf-8')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--capture',type=Path)
    p.add_argument('--input',type=Path)
    p.add_argument('--output',type=Path)
    p.add_argument('--sync-sql',action='store_true')
    p.add_argument('--check',action='store_true')
    a=p.parse_args()
    if a.sync_sql: sync_sql(a.check)
    if a.capture:
        if a.capture.exists(): raise ValueError('Capture already exists')
        a.capture.parent.mkdir(parents=True,exist_ok=True)
        with a.capture.open('w',encoding='utf-8') as stream:
            subprocess.run(['docker','exec','-i','akk-stack-mariadb-1','mariadb','-ueqemu','-peqemu',
                            '--batch','--raw','--skip-column-names','peq'],input=capture_sql(),text=True,
                           stdout=stream,check=True)
    if a.input:
        rows=plan([json.loads(line) for line in a.input.read_text(encoding='utf-8').splitlines()])
        a.output.mkdir(exist_ok=False,parents=True)
        (a.output/'plan.json').write_text(json.dumps(rows,indent=2)+'\n')
        for name,rollback in [('forward',False),('rollback',True)]:
            (a.output/(name+'.sql')).write_text(migration_sql(rows,rollback),encoding='utf-8')
        report={'changed':len(rows),'tiers':dict(Counter(r['id']//200000 for r in rows)),
                'input_sha256':hashlib.sha256(a.input.read_bytes()).hexdigest(),
                'spell_before_after':dict(Counter(f"{r['old'][0]}->{r['new'][0]}" for r in rows))}
        (a.output/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({'changed':len(rows),'output':str(a.output)}))

if __name__=='__main__': main()
