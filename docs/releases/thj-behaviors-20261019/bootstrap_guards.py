"""Exercise fresh-bootstrap guards against an isolated 12-row fixture table only."""
import json
from pathlib import Path
import rehearse
REL=Path(__file__).resolve().parent
ROOT=REL.parents[2]
def main():
    assert json.loads((REL/'database-rehearsal.json').read_text())['status']=='passed'
    audit=json.loads((REL/'gear-audit.json').read_text());a,b,c=audit['included_families'][:3]
    ids=[ident+offset for ident in (a,b,c) for offset in (0,200000,400000,600000)]
    table='nightcap_thj_bootstrap_guard_items'
    setup='CREATE TABLE '+table+' LIKE items;INSERT INTO '+table+' SELECT * FROM items WHERE id IN ('+','.join(map(str,ids))+');'
    setup+=f'UPDATE {table} SET hp=hp+1 WHERE id={a};UPDATE {table} SET hp=hp+123 WHERE id IN ({a+600000},{b+600000},{c+600000});DELETE FROM {table} WHERE id={b+400000};'
    setup+=f'SET @drift_a=(SELECT hp FROM {table} WHERE id={a+600000});SET @drift_b=(SELECT hp FROM {table} WHERE id={b+600000});'
    bootstrap=(ROOT/'eq-solo-gm/scripts/thj-stock-bootstrap.sql').read_text()
    bootstrap=bootstrap.replace('UPDATE items t JOIN','UPDATE '+table+' t JOIN').replace('JOIN items ','JOIN '+table+' ')
    setup+=bootstrap
    setup+=f"SELECT 'CUSTOM_NORMAL_SKIPPED',hp=@drift_a FROM {table} WHERE id={a+600000};SELECT 'MISSING_FAMILY_SKIPPED',hp=@drift_b FROM {table} WHERE id={b+600000};SELECT 'ELIGIBLE_UPDATED',i.hp=f.hp FROM {table} i JOIN items f ON f.id=i.id WHERE i.id={c+600000};DROP TABLE {table};"
    result=rehearse.sql(setup).stdout.strip();assert result=='CUSTOM_NORMAL_SKIPPED\t1\nMISSING_FAMILY_SKIPPED\t1\nELIGIBLE_UPDATED\t1',result
    (REL/'bootstrap-guards.json').write_text(json.dumps(dict(status='passed',checks=3,database=rehearse.DB,isolated_fixture_table=table,live_modified=False,output=result.splitlines()),indent=2)+'\n');print(result)
if __name__=='__main__':main()
