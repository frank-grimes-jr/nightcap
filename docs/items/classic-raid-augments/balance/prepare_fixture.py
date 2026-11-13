"""Load public offline content only into the dedicated ephemeral MariaDB container."""
import argparse
import gzip
import json
from pathlib import Path
import re
import secrets
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
DB = 'nightcap_raid_aug_balance_20261112'
USER = 'raid_aug_balance_261112'
MYSQL = 'nightcap-raid-aug-balance-20261112'
SERVER = 'akk-stack-eqemu-server-1'
R = '/tmp/nightcap-balance-raid-augs-20261112'
sys.path.insert(0,str(ROOT/'tools'/'balance'))
from prepare_native import content_tables


def sql(body):
    cmd = ['docker','exec','-i',MYSQL,'mariadb','--protocol=socket','-uroot','--batch','--raw','-N',DB]
    p = subprocess.run(cmd,input=body.encode() if isinstance(body,str) else body,capture_output=True)
    if p.returncode:
        # Never print row contents, which can contain control characters.
        raise RuntimeError(p.stderr.decode(errors='replace')[-450:])
    return p.stdout.decode()


def prepare(backup, source):
    if sql('SHOW TABLES').strip():
        raise ValueError('Fresh task-owned DB required')
    selected = set(content_tables((source/'common/database_schema.h').read_text()))
    # No schema/records from account- or character-specific tables; diagnostic
    # needs their empty definitions for its generated clients.
    names = []
    inserts = 0
    create = None
    cmd=['docker','exec','-i',MYSQL,'mariadb','--protocol=socket','-uroot',DB]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    proc.stdin.write(b"SET SESSION foreign_key_checks=0; SET SESSION sql_mode='NO_AUTO_VALUE_ON_ZERO';\n")
    with gzip.open(backup,'rb') as f:
        for line in f:
            if create is not None:
                create.append(line)
                if line.startswith(b') ENGINE='):
                    proc.stdin.write(b''.join(create))
                    create=None
            elif (m:=re.match(rb'CREATE TABLE `(\w+)`',line)):
                names.append(m[1].decode())
                create=[line]
            elif (m:=re.match(rb'INSERT INTO `(\w+)`',line)) and m[1].decode() in selected:
                proc.stdin.write(line)
                inserts+=1
    proc.stdin.close()
    error=proc.stderr.read()
    if proc.wait()!=0:raise RuntimeError(error.decode(errors='replace')[-450:])
    assert len(names)>200 and inserts>200
    print('Restored allowed content and empty synthetic schema',len(names),inserts,flush=True)


def overlay():
    content = json.loads(gzip.decompress((ROOT/'docs/quests/camil-chapterhouse/balance-public-content.json.gz').read_bytes()))
    for table, data in content['tables'].items():
        if table=='items':
            continue
        names = ','.join('`'+k+'`' for k in data['columns'])
        # Captured rows carry integers, decimal strings and UTF-8 text. Use
        # ordinary SQL string constants (hex interpreted numerically for ints).
        def quoted(v):
            if v is None:return 'NULL'
            return "'"+str(v).replace("'","''")+"'"
        for start in range(0,len(data['rows']),500):
            body='SET SESSION sql_mode=\'NO_BACKSLASH_ESCAPES\';\n'
            if start==0:body+='DELETE FROM '+table+';\n'
            body+='INSERT INTO '+table+' ('+names+') VALUES '+','.join('('+','.join(quoted(x) for x in row)+')' for row in data['rows'][start:start+500])
            sql(body)
    hunts=json.loads((ROOT/'docs/audits/augments-20261106/item-preimages.json').read_text())
    for row in hunts:
        if row['tier']!=3:continue
        item=row['after']
        cols=list(item)
        data=','.join('NULL' if item[k] is None or item[k]=='NULL' else "'"+str(item[k]).replace("'","''")+"'" for k in cols)
        sql("SET SESSION sql_mode='NO_BACKSLASH_ESCAPES'; REPLACE INTO items ("+','.join('`'+k+'`' for k in cols)+') VALUES ('+data+')')
    sql((HERE.parent/'content.sql').read_text())
    for row in json.loads((ROOT/'docs/releases/zone-loot-20261009/generated/socket-preimages.json').read_text()):
        if row['id'] in (601552,604882,602814):
            socket=row['socket']
            sql(f"UPDATE items SET augslot{socket}type=22,augslot{socket}visible=1 WHERE id={row['id']}")
    sql("DELETE FROM npc_spells_entries WHERE spellid IN (982,2859)")
    sql("INSERT INTO character_multiclass(character_id,class2,class3) VALUES (97101,2,7),(97102,2,12),(97103,3,7),(97104,11,10),(97201,2,7),(97202,2,12),(97203,3,7),(97204,11,10)")
    password=secrets.token_hex(30)
    sql(f"CREATE USER '{USER}'@'%' IDENTIFIED BY '{password}'; GRANT ALL ON {DB}.* TO '{USER}'@'%'")
    config={'server':{'world':{'shortname':'raid_aug_bal','longname':'Isolated local encounter diagnostic','tcp':{'ip':'127.0.0.1','port':'1'}},'auto_database_updates':'false','database':{'host':MYSQL,'port':'3306','db':DB,'username':USER,'password':password},'directories':{'quests':'quests','plugins':'plugins','lua_modules':'lua_modules','logs':'logs','maps':'maps','shared_memory':'shared/','patches':'/home/eqemu/server','opcodes':'/home/eqemu/server'}}}
    setup="from pathlib import Path;import sys; r=Path('"+R+"'); [(r/d).mkdir(exist_ok=True) for d in ('plugins','quests','lua_modules','logs','shared')]; (r/'maps').symlink_to('/tmp/nightcap-balance-thj-parity-20261018/maps',target_is_directory=True); (r/'eqemu_config.json').write_text(sys.stdin.read()); (r/'eqemu_config.json').chmod(0o600)"
    subprocess.run(['docker','exec','-i',SERVER,'python3','-c',setup],input=json.dumps(config),text=True,check=True)
    print('NPC fixtures:',sql('SELECT id,name,level,hp,mindmg,maxdmg FROM npc_types WHERE id IN (32040,72003,76007,71065)'))
    assert sql('SELECT COUNT(*) FROM account; SELECT COUNT(*) FROM character_data;').strip().splitlines()==['0','0']


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('action',choices=('base','overlay'))
    p.add_argument('--backup',type=Path)
    p.add_argument('--source',type=Path)
    a=p.parse_args()
    if a.action=='base':prepare(a.backup,a.source)
    else:overlay()
