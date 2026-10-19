"""Rehearse the exact candidate in a new isolated DB, never peq or production."""
import gzip,hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];REL=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools'))
from thj_item_migration import row_hash
import thj_behavior_content as content,thj_stock_scaling as gear
DB='nightcap_thj_behaviors_20261019'
STAGE=Path('E:/EQ_Local_Dev/artifacts/thj-behaviors-20261019/db-rehearsal')

def command(db=''):
    assert db in ('',DB)
    return ['docker','exec','-i','akk-stack-mariadb-1','bash','-lc','exec mariadb --local-infile=1 --max-allowed-packet=1G -uroot -p"$MYSQL_ROOT_PASSWORD" --batch --skip-column-names '+db]
def sql(text,check=True):
    return subprocess.run(command(DB),input=text,encoding='utf-8',stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=check)
def load(table,rows,columns):
    def cell(v):
        if v is None:return r'\N'
        return str(v).replace('\\','\\\\').replace('\0',r'\0').replace('\t',r'\t').replace('\n',r'\n').replace('\r',r'\r')
    path=STAGE/(table+'.tsv')
    with path.open('w',encoding='utf-8',newline='') as f:
        for row in rows:f.write('\t'.join(cell(row[c]) for c in columns)+'\n')
    dest='/tmp/nightcap-thj-behaviors-'+table+'.tsv'
    subprocess.run(['docker','cp',str(path),'akk-stack-mariadb-1:'+dest],check=True,stdout=subprocess.DEVNULL)
    sql("LOAD DATA LOCAL INFILE '"+dest+"' INTO TABLE `"+table+"` CHARACTER SET utf8mb4 ("+','.join('`'+c+'`' for c in columns)+');')
    print('loaded',table,len(rows),flush=True)
def apply(name,check=True):
    p=REL/name;data=gzip.decompress(p.read_bytes()).decode() if name.endswith('.gz') else p.read_text()
    result=sql(data,check=False)
    if check and result.returncode:raise RuntimeError(name+': '+result.stderr[-3000:])
    print(name,result.returncode,flush=True);return result

def hashes(table,columns):
    expr="SHA2(CONCAT_WS('|',"+','.join("IFNULL(HEX(CAST(`"+c+"` AS CHAR CHARACTER SET utf8mb4)),'NULL')" for c in columns)+'),256)'
    output=sql('SELECT id,'+expr+' FROM '+table+' ORDER BY id;').stdout
    return {int(line.split('\t')[0]):line.split('\t')[1] for line in output.splitlines()}

def main(resume=False):
    if not resume:STAGE.mkdir(exist_ok=False)
    if not resume:
        create=f'CREATE DATABASE {DB};'+''.join(f'CREATE TABLE {DB}.{t} LIKE peq.{t};' for t in ('items','spells_new','aa_ability','aa_ranks','aa_rank_effects','aa_rank_prereqs','rule_values'))
        subprocess.run(command(),input=create,encoding='utf-8',check=True)
        base=content.snapshot()
        for table,rows in base['tables'].items():load(table,rows,base['schemas'][table])
    captured=Path('E:/EQ_Local_Dev/artifacts/thj-behaviors-20261019/production-items.json.gz')
    data=json.loads(gzip.decompress(captured.read_bytes()));columns=data['columns'];current={int(r['id']):r for r in data['rows']}
    if not resume:load('items',data['rows'],columns)
    pairs,audit=gear.plan(current)
    before={i:row_hash(r,columns) for i,r in current.items()};after=dict(before)
    for old,new in pairs:after[old['id']]=row_hash(new,columns)
    assert hashes('items',columns)==before,'Loaded public item preimages differ'
    del current,data
    # A failed prior procedure can remain after its transaction rolled back.
    sql('DROP PROCEDURE IF EXISTS nightcap_thj_behaviors_20261019;')
    for name in ('content-forward.sql','content-forward.sql','rule-forward.sql','rule-forward.sql','rule-disable.sql','rule-disable.sql','rule-enable.sql') :apply(name)
    for name in ('gear-forward.sql.gz','gear-forward.sql.gz'):apply(name)
    assert hashes('items',columns)==after,'Full item afterimage mismatch'
    apply('gear-rollback.sql.gz');assert hashes('items',columns)==before,'Rollback differs'
    apply('gear-rollback.sql.gz');apply('content-rollback.sql');apply('content-rollback.sql')
    # Late-row drift must prevent even the first proposed update.
    last=pairs[-1][0]['id'];sql(f'UPDATE items SET price=price+1 WHERE id={last};')
    failed=apply('gear-forward.sql.gz',False);assert failed.returncode and 'preimage drift' in failed.stderr
    observed=hashes('items',columns);assert all(observed[i]==h for i,h in before.items() if i!=last),'Failed preflight partially wrote items'
    sql(f'UPDATE items SET price=price-1 WHERE id={last};')
    apply('content-forward.sql');apply('gear-forward.sql.gz')
    assert hashes('items',columns)==after
    # The same new bootstrap policy must agree with the live planner on all rows.
    sql((ROOT/'eq-solo-gm/scripts/thj-stock-bootstrap.sql').read_text())
    assert hashes('items',columns)==after,'Bootstrap and migration disagree'
    report=dict(status='passed',database=DB,content_groups=len(content.groups()),item_rows_verified=len(before),changed_items=len(pairs),full_row_columns=len(columns),retry=True,rollback=True,late_preimage_fault_atomic=True,bootstrap_equivalent=True,live_modified=False)
    (REL/'database-rehearsal.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
if __name__=='__main__':main('--resume-verified-import' in sys.argv)
