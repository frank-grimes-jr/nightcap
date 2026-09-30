"""Check new-table privileges using the actual game account; roll every write back."""
import json
import secrets
import subprocess
import uuid

TABLES=('character_advloot_settings','character_advloot_filters','character_advloot_claims')

def verify_app_database(root, sql, evidence):
    config=json.loads((root/'private/eqemu_config.json').read_text())['server']['database']
    assert config['db']=='peq' and config['host']=='db'
    character=4294967001
    drop=str(uuid.uuid4())
    assert sql(f'SELECT COUNT(*) FROM character_data WHERE id={character};').strip()=='0'
    assert all(sql(f'SELECT COUNT(*) FROM {name} WHERE character_id={character};').strip()=='0' for name in TABLES)
    def option(value):
        return '"'+str(value).replace('\\','\\\\').replace('"','\\"').replace('\n','\\n').replace('\r','\\r')+'"'
    private='[client]\n'+''.join(name+'='+option(value)+'\n' for name,value in (
        ('host',config['host']),('port',config['port']),('user',config['username']),('password',config['password'])))
    path='/tmp/nightcap-advloot-app-'+secrets.token_hex(12)+'.cnf'
    base=['docker','compose','exec','-T','db']
    query=f'''START TRANSACTION;
INSERT INTO character_advloot_settings(character_id,settings) VALUES({character},7);
INSERT INTO character_advloot_filters(character_id,item_id,filter) VALUES({character},13073,2);
INSERT INTO character_advloot_claims(drop_id,character_id,item_id,charges,inventory_after) VALUES('{drop}',{character},13073,1,'permission-probe');
UPDATE character_advloot_settings SET settings=6 WHERE character_id={character};
UPDATE character_advloot_filters SET filter=4 WHERE character_id={character};
SELECT settings FROM character_advloot_settings WHERE character_id={character};
SELECT filter FROM character_advloot_filters WHERE character_id={character};
SELECT item_id FROM character_advloot_claims WHERE drop_id='{drop}';
DELETE FROM character_advloot_filters WHERE character_id={character};
SELECT COUNT(*) FROM character_advloot_filters WHERE character_id={character};
ROLLBACK;
'''
    try:
        # The credential is input data, never a command argument or tool output.
        created=subprocess.run(base+['sh','-c','umask 077; cat > "$1"','probe',path],cwd=root,input=private,text=True,capture_output=True,timeout=30)
        assert created.returncode==0,'Unable to stage private app-account probe'
        result=subprocess.run(base+['mariadb','--defaults-extra-file='+path,'--batch','--raw','--skip-column-names','peq'],cwd=root,input=query,text=True,capture_output=True,timeout=45)
        if result.returncode or result.stdout.strip().splitlines()!=['6','4','13073','0']:
            (evidence/'application-db-probe-private.log').write_text(result.stderr)
            raise RuntimeError('Game account lacks required loot-table capabilities; private host diagnostic retained')
    finally:
        removed=subprocess.run(base+['rm','-f',path],cwd=root,capture_output=True,timeout=30)
        assert removed.returncode==0,'Private probe credential cleanup failed'
    assert all(sql(f'SELECT COUNT(*) FROM {name} WHERE character_id={character};').strip()=='0' for name in TABLES),'Privilege probe failed to roll back'
    return {'identity':'actual game database account','settings':'select/insert/update','filters':'select/insert/update/delete','claims':'select/insert','transaction_rolled_back':True}
