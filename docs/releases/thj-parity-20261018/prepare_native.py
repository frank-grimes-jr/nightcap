"""Clone the completed synthetic WPM database and apply combined content there."""
import json,subprocess,sys,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
REL=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools'))
import thj_combined_content as content
from wpm_migration import insert
DB='nightcap_thj_parity_20261018'
STAGE=ROOT.parent/'thj-parity-native-input'
STAGE.mkdir(exist_ok=True)

def db_command(arguments):
    return ['docker','exec','-i','akk-stack-mariadb-1','bash','-lc',
            'exec mariadb -uroot -p"$MYSQL_ROOT_PASSWORD" --batch --skip-column-names '+arguments]

def main():
    found=subprocess.check_output(db_command(''),input=f"SELECT SCHEMA_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME='{DB}';",text=True)
    if found.strip():raise RuntimeError('Synthetic target already exists; do not replace it')
    subprocess.run(db_command(''),input=f"CREATE DATABASE {DB}; GRANT ALL ON {DB}.* TO 'nightcap_balance'@'%';",text=True,check=True)
    print('Created isolated synthetic DB',flush=True)
    dump=subprocess.Popen(['docker','exec','akk-stack-mariadb-1','bash','-lc',
        'exec mariadb-dump -uroot -p"$MYSQL_ROOT_PASSWORD" --single-transaction --skip-triggers nightcap_wpm_balance_20261018'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    restore=subprocess.run(db_command(DB),stdin=dump.stdout,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    dump.stdout.close();error=dump.stderr.read().decode();code=dump.wait()
    if code or restore.returncode:raise RuntimeError('Synthetic clone failed: '+error+restore.stderr.decode())
    print('Cloned completed WPM fixture',flush=True)
    sql=[f"SELECT IF(DATABASE()='{DB}','synthetic target','WRONG TARGET');"]
    sql.extend(insert('items',row).replace('INSERT INTO','REPLACE INTO',1) for row in content.original_items().values())
    for name in ('pet-content-forward.sql','wpm-content-forward.sql','items-forward.sql','rules-forward.sql'):
        sql.append((REL/'content'/name).read_text())
    # Full combined retry after all companion acquisitions and item afterimages exist.
    for name in ('pet-content-forward.sql','wpm-content-forward.sql','items-forward.sql','rules-forward.sql'):
        sql.append((REL/'content'/name).read_text())
    subprocess.run(db_command(DB),input='\n'.join(sql),text=True,check=True)
    print('Combined content applied twice',flush=True)
    for name in ('build_native.py','native_harness.cpp','native_runtime.cpp','native_runtime.h'):
        (STAGE/name).write_bytes((ROOT/'tools/balance'/name).read_bytes().replace(b'\r\n',b'\n'))
    matrix=Path('C:/Users/verre/Documents/Codex/2026-10-18/goa/work/wpm-native-matrix/matrix.json')
    (STAGE/'matrix.json').write_bytes(matrix.read_bytes())
    runner=(ROOT/'docs/releases/wpm-melee-20261018/run_matrix.py').read_text().replace('/tmp/nightcap-balance-wpm-20261018','/tmp/nightcap-balance-thj-parity-20261018').replace('nightcap_wpm_balance_20261018',DB)
    (STAGE/'run_matrix.py').write_text(runner)
    setup=(ROOT/'docs/releases/wpm-melee-20261018/setup_native.py').read_text()
    setup=setup.replace("ROOT=Path('/tmp/nightcap-balance-wpm-20261018')","ROOT=Path('/tmp/nightcap-balance-thj-parity-20261018')")
    setup=setup.replace("BASE=Path('/tmp/nightcap-balance-20260912')","BASE=Path('/tmp/nightcap-balance-wpm-20261018')")
    setup=setup.replace('/tmp/nightcap-wpm-test-input','/tmp/thj-parity-native-input')
    setup=setup.replace("=='nightcap_balance_20260912'","=='nightcap_wpm_balance_20261018'").replace("['db']='nightcap_wpm_balance_20261018'",f"['db']='{DB}'")
    setup=setup.replace("for name in ('build_native.py','native_harness.cpp','native_runtime.cpp','native_runtime.h'):","for name in ('build_native.py','native_harness.cpp','native_runtime.cpp','native_runtime.h','matrix.json','run_matrix.py'):")
    (STAGE/'setup_native.py').write_text(setup)
    archive=ROOT.parent/'thj-parity-native-input.tar'
    with tarfile.open(archive,'w') as tar:tar.add(STAGE,arcname=STAGE.name)
    subprocess.run(['docker','cp',str(archive),'akk-stack-eqemu-server-1:/tmp/thj-parity-native-input.tar'],check=True)
    subprocess.run(['docker','exec','akk-stack-eqemu-server-1','tar','xf','/tmp/thj-parity-native-input.tar','-C','/tmp'],check=True)
    subprocess.run(['docker','exec','akk-stack-eqemu-server-1','python3','/tmp/thj-parity-native-input/setup_native.py'],check=True)

if __name__=='__main__':main()
