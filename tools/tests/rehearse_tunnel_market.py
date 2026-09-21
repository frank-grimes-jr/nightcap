"""Execute multi-offer schema/rotation on a disposable database, preserving audit."""
import argparse
import json
from pathlib import Path
import secrets
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from generate_living_economy import insert

ROOT=Path(__file__).resolve().parents[2]


def run(container,evidence):
    schema='nightcap_market_multi_test_'+secrets.token_hex(5)
    checks=[];created=False
    def sql(text,check=True,use=True):
        r=subprocess.run(['docker','exec','-i',container,'sh','-c',
            'MYSQL_PWD="${MARIADB_ROOT_PASSWORD:-$MYSQL_ROOT_PASSWORD}" exec mariadb -uroot --batch --raw --skip-column-names'],
            input=(f'USE {schema};\n' if use else '')+text,text=True,capture_output=True,timeout=120)
        if check and r.returncode:raise RuntimeError(r.stderr[-2500:])
        return r
    def verify(ok,label):
        if not ok:raise AssertionError(label)
        checks.append(label)
    try:
        sql(f'CREATE DATABASE {schema};',use=False);created=True
        sql((ROOT/'server-mods/sql/2026-09-20-living-economy.sql').read_text())
        sql('CREATE TABLE items(id INT PRIMARY KEY,nodrop INT,norent INT,stackable INT,maxcharges INT,itemclass INT,questitemflag INT,attuneable INT) ENGINE=InnoDB;'
            'CREATE TABLE npc_types(id INT PRIMARY KEY,merchant_id INT) ENGINE=InnoDB;'
            'CREATE TABLE merchantlist(merchantid INT,item INT) ENGINE=InnoDB;')
        catalog=json.loads((ROOT/'docs/economy/generated/catalog.json').read_bytes())['items']
        for item in catalog:
            sql(insert('items',dict(id=item['id'],nodrop=1,norent=1,stackable=0,maxcharges=0,itemclass=0,questitemflag=0,attuneable=0)))
            sql(insert('nightcap_market_catalog',dict(item_id=item['id'],pool=item['pool'],min_expansion=0,max_expansion=-1,
                **{k:item[k] for k in ('find_cp','sell_cp','buy_cp')},source_url=item['source_url'],captured_at='2026-09-20')))
        actors=[dict(npc_id=i,zone_id=22,kind='sell' if i<999506 else 'buy') for i in range(999500,999510)]
        actors += [dict(npc_id=i,zone_id=1,kind='find') for i in range(101,111)]
        sql('\n'.join(insert('nightcap_market_actors',a) for a in actors))
        sql('UPDATE nightcap_market_state SET enabled=1; CALL nightcap_market_rotate(0,4,2.5);'
            "INSERT INTO nightcap_market_trades(epoch,npc_id,character_id,kind,item_id,price_cp) SELECT epoch,npc_id,77,kind,item_id,price_cp FROM nightcap_market_offers WHERE kind='sell' LIMIT 1;")
        audit=sql('SELECT * FROM nightcap_market_trades;').stdout
        upgrade=(ROOT/'server-mods/sql/2026-09-21-multi-offer-market.sql').read_text()
        sql(upgrade);sql(upgrade)
        verify(sql('SELECT * FROM nightcap_market_trades;').stdout==audit,'upgrade and safe replay retain historic audit exactly')
        sql('\n'.join(insert('nightcap_market_actors',dict(npc_id=i,zone_id=22,kind='sell' if i<999684 else 'buy')) for i in range(999680,999686)))
        for iteration in range(30):
            sql('CALL nightcap_market_rotate(0,4,2.5);')
            counts=sql('SELECT kind,COUNT(*) FROM nightcap_market_offers GROUP BY kind ORDER BY kind;').stdout.strip()
            verify(counts=='find\t10\nsell\t20\nbuy\t12','rotation '+str(iteration)+' fills 10 finds, 20 sales and 12 buys')
            verify(sql("SELECT COUNT(*) FROM (SELECT npc_id,COUNT(*) n FROM nightcap_market_offers WHERE kind<>'find' GROUP BY npc_id HAVING n<>2) x;").stdout.strip()=='0','rotation '+str(iteration)+' gives every tunnel actor two distinct items')
            verify(sql("SELECT COUNT(*) FROM (SELECT item_id,kind,COUNT(*) n FROM nightcap_market_offers GROUP BY item_id,kind HAVING n>IF(kind='sell',3,2)) x;").stdout.strip()=='0','rotation '+str(iteration)+' respects per-item supply cap')
        first=sql("SELECT epoch,npc_id,item_id,price_cp FROM nightcap_market_offers WHERE kind='sell' ORDER BY npc_id,item_id LIMIT 1;").stdout.strip().split('\t')
        epoch,npc,item,price=map(int,first)
        sql('START TRANSACTION;'+f'UPDATE nightcap_market_offers SET remaining=0 WHERE npc_id={npc} AND item_id={item} AND epoch={epoch} AND remaining=1;'+
            f"INSERT INTO nightcap_market_trades(epoch,npc_id,character_id,kind,item_id,price_cp) VALUES({epoch},{npc},77,'sell',{item},{price});COMMIT;")
        verify(sql(f'SELECT SUM(remaining),COUNT(*) FROM nightcap_market_offers WHERE npc_id={npc};').stdout.strip()=='1\t2','consuming one offer leaves the sibling item for sale')
        sql(f"INSERT INTO nightcap_market_trades(epoch,npc_id,character_id,kind,item_id,price_cp) SELECT epoch,npc_id,77,kind,item_id,price_cp FROM nightcap_market_offers WHERE npc_id={npc} AND remaining=1;")
        verify(sql(f'SELECT COUNT(*) FROM nightcap_market_trades WHERE epoch={epoch} AND npc_id={npc};').stdout.strip()=='2','both purchases have separate durable audit rows')
        verify(sql(f"INSERT INTO nightcap_market_trades(epoch,npc_id,character_id,kind,item_id,price_cp) VALUES({epoch},{npc},77,'sell',{item},{price});",False).returncode!=0,'same item cannot be audited twice in one epoch')
        verify(sql('CALL nightcap_market_rotate(0,5,2.5);',False).returncode!=0,'income-policy drift rejects rotation')
        # Old procedure/native adapter can resume on composite keys; no historic
        # audit downgrade or deletion is required for rollback.
        baseline=(ROOT/'server-mods/sql/2026-09-20-living-economy.sql').read_text()
        proc=baseline[baseline.index('DELIMITER //'):].replace('CREATE PROCEDURE','DROP PROCEDURE nightcap_market_rotate //\nCREATE PROCEDURE',1)
        sql('DELETE FROM nightcap_market_actors WHERE npc_id BETWEEN 999680 AND 999685;\n'+proc+'\nCALL nightcap_market_rotate(0,4,2.5);')
        verify(sql('SELECT MAX(n) FROM (SELECT npc_id,COUNT(*) n FROM nightcap_market_offers GROUP BY npc_id) x;').stdout.strip()=='1','baseline rotation works with retained composite schema')
        verify(sql('SELECT COUNT(*) FROM nightcap_market_trades;').stdout.strip()=='3','rollback preserves all old and new trade audit')
        return checks
    finally:
        if created:sql(f'DROP DATABASE {schema};',use=False)
        evidence.mkdir(parents=True,exist_ok=True)
        (evidence/'market-database-checks.json').write_text(json.dumps(dict(checks=checks,disposable_schema_removed=True),indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--container',default='akk-stack-mariadb-1')
    p.add_argument('--evidence',type=Path,required=True);a=p.parse_args()
    checks=run(a.container,a.evidence);print(json.dumps(dict(passed=len(checks))))
