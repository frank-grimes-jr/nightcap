"""Guarded, Classic-only item plan. Camil appearance is a separate QA-gated step."""
import argparse
import json
from pathlib import Path
from pok_hub_migration import predicate, sql_value

ITEM_ID=990500
NAME='Winged Helm of the Dawn'
CHANGES={
    'id':str(ITEM_ID),'Name':NAME,'lore':NAME,'source':'NIGHTCAP_CUSTOM',
    'material':'90','color':'0','classes':'4','races':'4095','slots':'4',
    'ac':'18','hp':'25','mana':'25','asta':'5','awis':'7',
    'mr':'10','fr':'5','cr':'5','dr':'0','pr':'0',
    'augslot1type':'0','augslot2type':'0',
    'created':'2026-10-04 00:00:00','updated':'2026-10-04 00:00:00',
    'verified':None,
}

def plan(template):
    if str(template['id'])!='4851' or template['Name']!='Valorium Helmet':
        raise ValueError('Expected original Valorium Helmet template 4851')
    missing=CHANGES.keys()-template.keys()
    if missing:raise ValueError('Item schema mismatch: '+str(sorted(missing)))
    row=dict(template);row.update(CHANGES)
    for name in ('haste','regen','manaregen','enduranceregen','herosforgemodel',
                 'elitematerial','heroic_str','heroic_sta','heroic_agi','heroic_dex',
                 'heroic_wis','heroic_int','heroic_cha','spelldmg','healamt',
                 'reqlevel','reclevel'):
        if int(row[name])!=0:raise ValueError('Later-era template power: '+name)
    for name in ('clickeffect','proceffect','worneffect','focuseffect','scrolleffect','bardeffect'):
        if int(row[name])!=-1:raise ValueError('Unexpected template effect: '+name)
    if any(int(row[f'augslot{i}type']) for i in range(1,7)):
        raise ValueError('Unexpected augment slot')
    return row

def wrap(body,commit=True):
    return ('DELIMITER //\nBEGIN NOT ATOMIC\nDECLARE n BIGINT;\n'
      'DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;\n'
      'SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;\nSTART TRANSACTION;\n'
      "SELECT COUNT(*) INTO n FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='items' AND ENGINE='InnoDB';\n"
      "IF n<>1 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Item engine drift'; END IF;\n"
      "SELECT COUNT(*) INTO n FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=DATABASE() AND EVENT_OBJECT_TABLE='items';\n"
      "IF n<>0 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Item trigger drift'; END IF;\n"
      +body+('\nCOMMIT;' if commit else '\nROLLBACK;')+'\nEND //\nDELIMITER ;\n')

def forward(template,commit=True):
    row=plan(template)
    changes=','.join(f'`{k}`={sql_value(v)}' for k,v in CHANGES.items())
    return wrap(
      f'SELECT COUNT(*) INTO n FROM items WHERE id={ITEM_ID} OR Name={sql_value(NAME)} FOR UPDATE;\n'
      "IF n<>0 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Helmet ID or name occupied'; END IF;\n"
      f'SELECT COUNT(*) INTO n FROM items WHERE id=4851 AND {predicate(template)} FOR UPDATE;\n'
      "IF n<>1 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Valorium template drift'; END IF;\n"
      'CREATE TEMPORARY TABLE nightcap_winged_helmet LIKE items;\n'
      'INSERT INTO nightcap_winged_helmet SELECT * FROM items WHERE id=4851;\n'
      f'UPDATE nightcap_winged_helmet SET {changes};\n'
      'INSERT INTO items SELECT * FROM nightcap_winged_helmet;\n'
      f'SELECT COUNT(*) INTO n FROM items WHERE id={ITEM_ID} AND {predicate(row)};\n'
      "IF n<>1 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Helmet postcondition failed'; END IF;\n"
      'DROP TEMPORARY TABLE nightcap_winged_helmet;',commit)

def rollback(template):
    row=plan(template)
    return wrap(f'SELECT COUNT(*) INTO n FROM items WHERE id={ITEM_ID} AND {predicate(row)} FOR UPDATE;\n'
      "IF n<>1 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Helmet rollback drift'; END IF;\n"
      f'DELETE FROM items WHERE id={ITEM_ID};')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--snapshot',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();s=json.loads(a.snapshot.read_text());t=next(r for r in s['rows']['items'] if r['id']=='4851')
    a.output.mkdir(parents=True,exist_ok=False)
    for name,sql in [('forward.sql',forward(t)),('rehearse.sql',forward(t,False)),('rollback.sql',rollback(t))]:
        (a.output/name).write_text(sql,encoding='utf-8')
    (a.output/'item.json').write_text(json.dumps(plan(t),indent=2)+'\n')
