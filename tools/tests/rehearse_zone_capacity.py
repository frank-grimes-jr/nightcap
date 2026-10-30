"""Exercise actual forward/inverse SQL in an isolated local MariaDB schema."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from content_patch import capture
from pok_hub_migration import insert
from zone_capacity import generate, plan, selected


def rehearse(source, container):
    if not __debug__:
        raise RuntimeError('Rehearsal requires enabled assertions; do not use python -O')
    if not container.startswith('akk-stack-'):
        raise ValueError('Only an explicitly local akk-stack container is accepted')
    schema = 'nightcap_capacity_test_' + uuid.uuid4().hex[:12]
    if not re.fullmatch('nightcap_capacity_test_[a-f0-9]{12}',schema):
        raise ValueError('Unsafe disposable schema')
    def raw(sql, fail=False):
        result = subprocess.run(['docker','exec','-i',container,'sh','-lc',
            'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mariadb -uroot -N -B --raw'],
            input=sql,text=True,capture_output=True,timeout=120)
        if fail:
            if result.returncode == 0 or 'Court ' not in result.stderr:
                raise AssertionError('Expected guarded SQL rejection: '+result.stderr)
        elif result.returncode:
            raise RuntimeError(result.stderr)
        return result.stdout
    def sql(text,fail=False):return raw('USE `'+schema+'`;\n'+text,fail)
    def snapshot():
        data = capture(sql,{'zone':'1=1'})
        data['rows']['zone'].sort(key=lambda x:int(x['id']))
        return data['rows']['zone']
    supplied=json.loads(source.read_text(encoding='utf-8'))
    checks=[]
    raw('CREATE DATABASE `'+schema+'`;')
    try:
        sql(supplied['schemas']['zone']['create']+';\n'+
            '\n'.join(insert('zone',row) for row in supplied['rows']['zone']))
        baseline=snapshot()
        if baseline != sorted(supplied['rows']['zone'],key=lambda x:int(x['id'])):
            raise AssertionError('Captured production row reconstruction drift')
        before={'rows':{'zone':baseline}}
        forward,inverse=generate(before)
        expected=plan(before)['rows']['zone']
        sql('CREATE TABLE original LIKE zone; INSERT INTO original SELECT * FROM zone;'
            'CREATE TABLE progress_guard(id INT PRIMARY KEY,value TEXT) ENGINE=InnoDB;'
            "INSERT INTO progress_guard VALUES(1,'earned-progress-and-corpses');")
        def reset():sql('TRUNCATE TABLE zone; INSERT INTO zone SELECT * FROM original;')
        sql(forward)
        assert snapshot()==expected
        assert sql('SELECT value FROM progress_guard;').strip()=='earned-progress-and-corpses'
        checks.append('five scoped timer updates; all other fields and 613 rows preserved')
        sql(forward,True); assert snapshot()==expected
        checks.append('replay fails without writes')
        sql(inverse); assert snapshot()==baseline
        checks.append('inverse restores the complete exact zone table')
        target=selected(before)[0]['id']
        for mutation in [f'UPDATE zone SET shutdowndelay=123 WHERE id={target}',
                         f"UPDATE zone SET short_name=UPPER(short_name) WHERE id={target}",
                         f'UPDATE zone SET safe_x=safe_x+1 WHERE id={target}',
                         f'UPDATE zone SET version=1 WHERE id={target}',
                         f'DELETE FROM zone WHERE id={target}']:
            sql(mutation+';'); drift=snapshot(); sql(forward,True); assert snapshot()==drift; reset()
        checks.append('timer, case, coordinate, version and deletion drift reject atomically')
        sql("UPDATE zone SET shutdowndelay=123 WHERE short_name='fearplane';")
        unrelated=snapshot(); sql(forward); sql(inverse); assert snapshot()==unrelated; reset()
        checks.append('unrelated concurrent zone changes survive both directions')
        sql(forward); sql(f'UPDATE zone SET safe_x=safe_x+1 WHERE id={target};')
        drift=snapshot(); sql(inverse,True); assert snapshot()==drift; reset()
        checks.append('rollback refuses changed afterimages')
        sql('CREATE TRIGGER capacity_guard BEFORE UPDATE ON zone FOR EACH ROW SET NEW.shutdowndelay=NEW.shutdowndelay;')
        sql(forward,True); assert snapshot()==baseline; sql('DROP TRIGGER capacity_guard;')
        checks.append('unexpected trigger rejects before writes')
        sql('ALTER TABLE zone ENGINE=MyISAM;'); sql(forward,True); assert snapshot()==baseline
        checks.append('nontransactional engine rejects before writes')
    finally:
        raw('DROP DATABASE `'+schema+'`;')
    return {'passed':True,'environment':'isolated local MariaDB schema',
            'production_writes':False,'local_peq_writes':False,'zone_rows':len(baseline),'checks':checks}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture',type=Path,required=True)
    parser.add_argument('--container',default='akk-stack-mariadb-1')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    result=rehearse(args.capture,args.container)
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))
