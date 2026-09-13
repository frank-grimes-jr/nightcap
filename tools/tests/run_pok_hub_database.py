"""Exercise generated SQL only in a newly created, isolated MariaDB schema."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pok_hub_migration import insert, sql_value

DOCS = Path(__file__).resolve().parents[2]/'docs/pok'
DATABASE = 'nightcap_pok_qa_' + uuid4().hex[:12]


def sql(statement, expect_error=None):
    assert DATABASE.startswith('nightcap_pok_qa_') and len(DATABASE)==28
    result = subprocess.run(['docker','exec','-i','akk-stack-mariadb-1','sh','-c',
                             'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot --batch --raw --skip-column-names'],
                            input='USE `' + DATABASE + '`;\n'+statement, text=True, encoding='utf-8',
                            capture_output=True, timeout=120)
    if expect_error:
        if result.returncode == 0 or expect_error not in result.stderr:
            raise AssertionError('Expected rejection absent: '+result.stderr[-1200:])
    elif result.returncode:
        raise RuntimeError(result.stderr[-2000:])
    return result.stdout


def snapshot(reference):
    queries=[]
    for table, scope in reference['scopes'].items():
        columns = list(reference['rows'][table][0])
        fields = ','.join(sql_value(c)+f',CAST(`{c}` AS CHAR)' for c in columns)
        queries.append(f'SELECT {sql_value(table)},JSON_OBJECT({fields}) FROM `{table}` WHERE {scope};')
    rows={t:[] for t in reference['scopes']}
    for line in sql('\n'.join(queries)).splitlines():
        table,payload=line.split('\t',1)
        rows[table].append(json.loads(payload))
    return normalize(rows)


def normalize(rows):
    return {t:sorted(json.dumps(r,sort_keys=True) for r in rr) for t,rr in rows.items()}


def main():
    print('Isolated schema: '+DATABASE,flush=True)
    before=json.loads((DOCS/'hub-before.json').read_bytes())
    after=json.loads((DOCS/'hub-after.json').read_bytes())
    forward=(DOCS/'hub-forward.sql').read_text(encoding='utf-8')
    rollback=(DOCS/'hub-rollback.sql').read_text(encoding='utf-8')
    # Create fails on collision. No existing schema is reused, dropped, or restored.
    result=subprocess.run(['docker','exec','-i','akk-stack-mariadb-1','sh','-c',
                           'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot'],
                          input='CREATE DATABASE `'+DATABASE+'`;',text=True,capture_output=True,timeout=30)
    if result.returncode:
        raise RuntimeError(result.stderr)
    setup=[]
    for table,schema in before['schemas'].items():
        setup.append(schema['create']+';')
        setup += [insert(table,row) for row in before['rows'][table]]
    sql('\n'.join(setup))
    baseline=snapshot(before)
    assert baseline==normalize(before['rows']), 'Fixture differs from original snapshot'
    cases=[]
    sql(forward)
    assert snapshot(after)==normalize(after['rows']), 'Forward content differs from reviewed plan'
    cases.append('forward_exact_afterimage')
    sql(forward,expect_error='PoK preimage count drift')
    assert snapshot(after)==normalize(after['rows'])
    cases.append('repeat_apply_rejected_without_changes')
    sql(rollback)
    assert snapshot(before)==baseline
    cases.append('rollback_exact_preimage')
    sql("UPDATE npc_types SET lastname='QA drift' WHERE id=999220;")
    drift=snapshot(before)
    sql(forward,expect_error='PoK preimage row drift')
    assert snapshot(before)==drift
    sql('UPDATE npc_types SET lastname='+sql_value(next(n['lastname'] for n in before['rows']['npc_types'] if n['id']=='999220'))+' WHERE id=999220;')
    cases.append('changed_existing_npc_rejected_without_changes')
    sql('INSERT INTO spawn2 (id,zone) VALUES (997900,\'QA reserved ID\');')
    drift=snapshot(before)
    sql(forward,expect_error='PoK preimage count drift')
    assert snapshot(before)==drift
    sql('DELETE FROM spawn2 WHERE id=997900;')
    cases.append('occupied_new_spawn_id_rejected_without_changes')
    # A late engine failure must undo earlier merchant/NPC inserts and updates.
    sql("ALTER TABLE merchantlist ADD CONSTRAINT qa_reject_hub CHECK (merchantid NOT BETWEEN 99300 AND 99315);")
    sql(forward,expect_error='qa_reject_hub')
    assert snapshot(before)==baseline
    sql('ALTER TABLE merchantlist DROP CONSTRAINT qa_reject_hub;')
    cases.append('late_write_failure_rolls_back_all_content')
    sql(forward)
    sql("UPDATE npc_types SET lastname='Later content edit' WHERE id=997900;")
    drift=snapshot(after)
    sql(rollback,expect_error='PoK preimage row drift')
    assert snapshot(after)==drift
    sql('UPDATE npc_types SET lastname='+sql_value(next(n['lastname'] for n in after['rows']['npc_types'] if n['id']=='997900'))+' WHERE id=997900;')
    sql(rollback)
    assert snapshot(before)==baseline
    cases.append('rollback_preserves_unexpected_later_edits')
    # Legacy equivalence uses a controlled spell catalog; its class data can be
    # widened independently to demonstrate that the new hub never reads it.
    audit=json.loads((DOCS/'hub-stock-audit.json').read_bytes())
    restock=(DOCS.parents[1]/'eq-solo-gm/scripts/vendor_restock.sql').read_text(encoding='utf-8')
    legacy=(DOCS.parents[1]/'tools/templates/vendor_restock-archetype.sql').read_text(encoding='utf-8')
    sql('CREATE TABLE spells_new (id INT PRIMARY KEY,'+','.join('classes'+str(i)+' INT NOT NULL DEFAULT 255' for i in range(1,17))+') ENGINE=InnoDB;')
    spells={i['spell_id']:i['original_class_levels'] for i in audit['stock']}
    sql('INSERT INTO spells_new VALUES '+','.join('('+','.join(map(str,[spell]+levels))+')' for spell,levels in spells.items())+';')
    sql(legacy)
    legacy_result=snapshot(before)
    sql(restock)
    assert snapshot(before)==legacy_result
    cases.append('pre_migration_restock_matches_legacy')
    # Only this newly-created QA schema is reset to the captured fixture.
    sql('DELETE FROM merchantlist;'+''.join(insert('merchantlist',r) for r in before['rows']['merchantlist']))
    sql(forward)
    sql(restock)
    assert snapshot(after)==normalize(after['rows'])
    sql('UPDATE spells_new SET '+','.join('classes'+str(i)+'=1' for i in range(1,17))+';')
    sql(restock)
    assert snapshot(after)==normalize(after['rows'])
    cases.append('hub_restock_preserves_routing_despite_widened_classes')
    sql("UPDATE rule_values SET rule_value='10' WHERE rule_name='Character:MaxLevel';")
    sql(restock)
    observed=json.loads(sql("SELECT JSON_OBJECT('rows',COUNT(*),'max',MAX(slot)) FROM merchantlist WHERE merchantid BETWEEN 99300 AND 99315;"))
    from pok_hub import build_plan
    plan=build_plan(audit)
    expected=sum(i['class_level']<=10 for m in plan['merchants'] for i in m['items'])
    assert observed['rows']==expected
    for m in plan['merchants']:
        items=sql('SELECT item FROM merchantlist WHERE merchantid='+str(m['merchant_id'])+' ORDER BY slot;').splitlines()
        assert items==[str(i['item_id']) for i in m['items'] if i['class_level']<=10]
    cases.append('lower_cap_uses_original_class_levels_and_contiguous_slots')
    sql("UPDATE rule_values SET rule_value='60' WHERE rule_name='Character:MaxLevel';")
    drift=snapshot(after)
    sql(restock,expect_error='Review arrival-hub catalog')
    assert snapshot(after)==drift
    sql("UPDATE rule_values SET rule_value='50' WHERE rule_name='Character:MaxLevel'; UPDATE rule_values SET rule_value='1' WHERE rule_name='Expansion:CurrentExpansion';")
    drift=snapshot(after)
    sql(restock,expect_error='Review arrival-hub catalog')
    assert snapshot(after)==drift
    cases.append('unreviewed_cap_and_expansion_refuse_before_writes')
    sql("UPDATE rule_values SET rule_value='50junk' WHERE rule_name='Character:MaxLevel';")
    drift=snapshot(after)
    sql(restock,expect_error='Missing or invalid level cap')
    assert snapshot(after)==drift
    sql("UPDATE rule_values SET rule_value='50' WHERE rule_name='Character:MaxLevel';")
    cases.append('malformed_level_cap_rejected_without_changes')
    sql("UPDATE rule_values SET rule_value='0' WHERE rule_name='Expansion:CurrentExpansion';")
    sql(restock)
    sql("UPDATE npc_types SET name='Changed merchant' WHERE id=997900;")
    drift=snapshot(after)
    sql(restock,expect_error='Arrival merchant identities changed')
    assert snapshot(after)==drift
    sql('UPDATE npc_types SET name='+sql_value(next(n['name'] for n in after['rows']['npc_types'] if n['id']=='997900'))+' WHERE id=997900;')
    cases.append('restock_rejects_changed_merchant_identity')
    drift=snapshot(after)
    marker='DROP TEMPORARY TABLE nightcap_pok_desired_stock;'
    assert restock.count(marker)==1
    fault=restock.replace(marker,"SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='injected after restock insert';\n"+marker)
    sql(fault,expect_error='injected after restock insert')
    assert snapshot(after)==drift
    cases.append('late_restock_failure_restores_previous_stock')
    sql(restock)
    assert snapshot(after)==normalize(after['rows'])
    sql(rollback)
    assert snapshot(before)==baseline
    report={'database':DATABASE,'cases':cases,'passed':len(cases),'restored_exact_preimage':True,
            'scope':'Real MariaDB content tables. No PEQ writes, zone restart, client, or in-game QA.',
            'sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in
                      [DOCS/'hub-before.json',DOCS/'hub-after.json',DOCS/'hub-forward.sql',DOCS/'hub-rollback.sql',DOCS.parents[1]/'eq-solo-gm/scripts/vendor_restock.sql']}}
    (DOCS/'hub-database-tests.json').write_bytes((json.dumps(report,indent=2)+'\n').encode())
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
