"""Exercise market SQL in a disposable schema; never writes live PEQ."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import re
import secrets
import subprocess

ROOT=Path(__file__).resolve().parents[2]


def sql(text, check=True):
    run=subprocess.run(['docker','exec','-i','akk-stack-mariadb-1','sh','-c',
        'MYSQL_PWD="${MARIADB_ROOT_PASSWORD:-$MYSQL_ROOT_PASSWORD}" exec mariadb -uroot --batch --raw --skip-column-names'],
        input=text,text=True,capture_output=True,timeout=120)
    if check and run.returncode:
        raise RuntimeError(run.stderr[-3000:])
    return run


def atomic_trace(trace):
    body=[]
    for index,q in enumerate(trace[1:],1):
        if q.startswith('SELECT'):
            q=re.sub(r'^SELECT .*? FROM ', 'SELECT COUNT(*) INTO n FROM ',q,count=1)
            expected=0 if index==6 and 'INSERT INTO inventory' in trace[7] else 1
            body.extend([q+';',f"IF n<>{expected} THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='rejected predicate {index}'; END IF;"])
        else:
            body.append(q+';')
            if q.startswith(('INSERT','UPDATE','DELETE')):
                body.append("IF ROW_COUNT()<>1 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='rejected mutation'; END IF;")
    return "DELIMITER //\nBEGIN NOT ATOMIC\nDECLARE n BIGINT;\nDECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;\n"+'\n'.join(body)+"\nEND //\nDELIMITER ;\n"


def run(evidence):
    trace=json.loads((evidence/'market-sql.json').read_text())
    generated=ROOT/'docs/economy/generated'
    catalog=json.loads((generated/'catalog.json').read_text())
    placement=json.loads((generated/'placement.json').read_text())
    schema='nightcap_market_test_'+secrets.token_hex(5)
    if not re.fullmatch('nightcap_market_test_[a-f0-9]{10}',schema):
        raise ValueError('Unsafe disposable schema name')
    ids=','.join(str(i['id']) for i in catalog['items'])
    npcs=','.join(str(m['npc_id']) for m in placement['merchants'])
    merchants=','.join(str(m['merchant_id']) for m in placement['merchants'])
    templates=','.join(str(t['template']) for t in placement['traders'])
    native=['items','npc_types','merchantlist','spawnentry','spawngroup','spawn2','zone_state_spawns','rule_values','inventory','character_currency']
    checks=[]
    def q(text, check=True):return sql('USE '+schema+';\n'+text,check)
    def verify(condition,label):
        if not condition:raise AssertionError(label)
        checks.append(label)
    try:
        sql('CREATE DATABASE '+schema+';')
        q('\n'.join('CREATE TABLE '+t+' LIKE peq.'+t+';' for t in native)+
          f'\nINSERT INTO items SELECT * FROM peq.items WHERE id IN({ids});'+
          f'\nINSERT INTO npc_types SELECT * FROM peq.npc_types WHERE id IN({npcs},{templates});'+
          f'\nINSERT INTO merchantlist SELECT * FROM peq.merchantlist WHERE merchantid IN({merchants});'+
          '\nINSERT INTO rule_values SELECT * FROM peq.rule_values WHERE ruleset_id=1;')
        q((ROOT/'server-mods/sql/2026-09-20-living-economy.sql').read_text())
        q((generated/'content.sql').read_text())
        verify(q('SELECT COUNT(*) FROM nightcap_market_actors;').stdout.strip()=='22','22 actors installed')
        verify(q('SELECT COUNT(*) FROM spawn2;').stdout.strip()=='10','10 new spawns')
        verify(q((generated/'content.sql').read_text(),False).returncode!=0,'duplicate setup rejected')
        q('CALL nightcap_market_rotate(0,4,2.5);')
        verify(q('SELECT epoch FROM nightcap_market_state;').stdout.strip()=='0','disabled startup does not rotate')
        q('UPDATE nightcap_market_state SET enabled=1; CALL nightcap_market_rotate(0,4,2.5);')
        counts=q('SELECT kind,COUNT(*) FROM nightcap_market_offers GROUP BY kind ORDER BY kind;').stdout.strip()
        verify(counts=='find\t10\nsell\t6\nbuy\t4','bounded find/sell/buy allocation')
        verify(q('SELECT COUNT(*) FROM nightcap_market_offers WHERE remaining<>1;').stdout.strip()=='0','every generated item quantity one')
        before=q('SELECT epoch,npc_id,item_id,price_cp,remaining FROM nightcap_market_offers ORDER BY npc_id;').stdout
        q('SELECT * FROM nightcap_market_offers;')
        verify(before==q('SELECT epoch,npc_id,item_id,price_cp,remaining FROM nightcap_market_offers ORDER BY npc_id;').stdout,'reading/reopening does not restock')
        verify(q('CALL nightcap_market_rotate(0,5,2.5);',False).returncode!=0,'earning-rule drift rejects rotation')
        verify(before==q('SELECT epoch,npc_id,item_id,price_cp,remaining FROM nightcap_market_offers ORDER BY npc_id;').stdout,'failed rotation retains exact prior stock')
        q('UPDATE nightcap_market_catalog SET min_expansion=1; CALL nightcap_market_rotate(0,4,2.5);')
        verify(q('SELECT COUNT(*) FROM nightcap_market_offers;').stdout.strip()=='0','future era catalog excluded')
        q('UPDATE nightcap_market_catalog SET min_expansion=0; CALL nightcap_market_rotate(0,4,2.5);')
        verify(q('SELECT epoch FROM nightcap_market_state;').stdout.strip()=='3','only successful world rotations increment epoch')
        q("INSERT INTO items(id,Name,nodrop,norent,stackable,maxcharges,itemclass) VALUES(1001,'Market Test',1,1,0,0,0);"
          "INSERT INTO nightcap_market_catalog VALUES(1001,'tunnel',0,-1,10000,10000,7000,'test',CURRENT_DATE);"
          "UPDATE nightcap_market_state SET epoch=1; DELETE FROM nightcap_market_offers;"
          "INSERT INTO nightcap_market_offers VALUES(999500,1,22,'sell',1001,10000,1);"
          "INSERT INTO character_currency(id,platinum) VALUES(77,100),(78,100);")
        def snapshot():
            return q("SELECT 'wallet',id,platinum,gold,silver,copper FROM character_currency ORDER BY id;"
                     "SELECT 'item',character_id,slot_id,item_id FROM inventory ORDER BY character_id;"
                     "SELECT 'stock',remaining FROM nightcap_market_offers;"
                     "SELECT 'audit',COUNT(*) FROM nightcap_market_trades;").stdout
        pristine=snapshot()
        for end in (8,9,10,11):
            q(';\n'.join(trace['buy'][1:end])+ ';\nROLLBACK;')
            verify(snapshot()==pristine,f'rollback after statement {end} preserves wallet/item/stock/audit')
        buy=atomic_trace(trace['buy'])
        other=buy.replace('character_id=77','character_id=78').replace('id=77 AND','id=78 AND').replace('(77,33,','(78,33,').replace('999500,77,','999500,78,')
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(lambda body:q(body,False),[buy,other]))
        verify(sorted(r.returncode for r in results)==[0,1],'two simultaneous buyers have exactly one winner')
        verify(q('SELECT COUNT(*) FROM inventory; SELECT COUNT(*) FROM nightcap_market_trades; SELECT remaining FROM nightcap_market_offers; SELECT SUM(platinum) FROM character_currency;').stdout.strip()=='1\n1\n0\n190','one item, one payment, one audit, sold out')
        verify(q(buy,False).returncode!=0,'repeated purchase rejected')
        q('DELETE FROM inventory; DELETE FROM nightcap_market_trades; UPDATE character_currency SET platinum=100;'
          "UPDATE nightcap_market_offers SET kind='buy',remaining=1;"
          'INSERT INTO inventory(character_id,slot_id,item_id,charges,color,guid) VALUES(77,33,1001,0,0,901);')
        sell=atomic_trace(trace['sell'])
        q('UPDATE inventory SET augment_one=123;')
        verify(q(sell,False).returncode!=0,'modified hand-in rejected without payout')
        q('UPDATE inventory SET augment_one=0;')
        q(sell)
        verify(q('SELECT COUNT(*) FROM inventory; SELECT platinum FROM character_currency WHERE id=77; SELECT remaining FROM nightcap_market_offers;').stdout.strip()=='0\n110\n0','WTB consumes one item and pays atomically')
        q('UPDATE nightcap_market_state SET epoch=2; UPDATE nightcap_market_offers SET remaining=1;')
        verify(q(buy,False).returncode!=0,'stale restart quote rejected')
        columns=[line.split('\t') for line in q('SHOW COLUMNS FROM zone_state_spawns;').stdout.splitlines()]
        required={c[0]: ('0' if re.match(r'(tinyint|smallint|mediumint|int|bigint|float|double|decimal)',c[1]) else "''")
                  for c in columns if c[2]=='NO' and c[4]=='NULL' and 'auto_increment' not in c[5]}
        for instance,corpse,npc in [(0,0,999500),(0,1,999500),(1,0,999500),(0,0,12345)]:
            fixture={**required,'zone_id':'22','instance_id':str(instance),'is_corpse':str(corpse),'is_zone':'0','npc_id':str(npc)}
            q('INSERT INTO zone_state_spawns('+','.join('`'+c+'`' for c in fixture)+') VALUES('+','.join(fixture.values())+');')
        preserved=q('SELECT * FROM character_currency ORDER BY id; SELECT * FROM inventory; '
                    'SELECT * FROM nightcap_market_trades; SELECT * FROM merchantlist ORDER BY merchantid,slot;').stdout
        q((generated/'rollback.sql').read_text())
        verify(q('SELECT enabled FROM nightcap_market_state; SELECT COUNT(*) FROM nightcap_market_actors; '
                 'SELECT COUNT(*) FROM nightcap_market_offers; SELECT COUNT(*) FROM spawn2; '
                 'SELECT COUNT(*) FROM npc_types WHERE id BETWEEN 999500 AND 999509;').stdout.strip()=='0\n0\n0\n0\n0',
               'rollback disables market and removes only new actors/spawns')
        verify(preserved==q('SELECT * FROM character_currency ORDER BY id; SELECT * FROM inventory; '
                            'SELECT * FROM nightcap_market_trades; SELECT * FROM merchantlist ORDER BY merchantid,slot;').stdout,
               'rollback preserves player money/items, audit and original merchant stock')
        verify(q('SELECT COUNT(*) FROM zone_state_spawns;').stdout.strip()=='3',
               'rollback retains corpses, other instances and unrelated saved spawns')
    finally:
        sql('DROP DATABASE IF EXISTS '+schema+';')
    evidence.mkdir(parents=True,exist_ok=True)
    report={'status':'passed','scope':'disposable schema; no live PEQ writes','schema_removed':schema,'checks':checks}
    (evidence/'market-database.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('evidence',type=Path);run(p.parse_args().evidence)
