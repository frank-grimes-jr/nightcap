"""Exercise fresh-bootstrap guards against temporary item rows only."""
import json
from pathlib import Path
import rehearse
REL=Path(__file__).resolve().parent
ROOT=REL.parents[2]
def main():
    assert json.loads((REL/'database-rehearsal.json').read_text())['status']=='passed'
    audit=json.loads((REL/'gear-audit.json').read_text());a,b,c=audit['included_families'][:3]
    ids=[ident+offset for ident in (a,b,c) for offset in (0,200000,400000,600000)]
    setup='CREATE TEMPORARY TABLE bootstrap_fixture LIKE items;INSERT INTO bootstrap_fixture SELECT * FROM items WHERE id IN ('+','.join(map(str,ids))+');CREATE TEMPORARY TABLE items LIKE bootstrap_fixture;INSERT INTO items SELECT * FROM bootstrap_fixture;'
    setup+=f'UPDATE items SET hp=hp+1 WHERE id={a};UPDATE items SET hp=hp+123 WHERE id IN ({a+600000},{b+600000},{c+600000});DELETE FROM items WHERE id={b+400000};'
    setup+='SET @drift_a=(SELECT hp FROM items WHERE id='+str(a+600000)+');SET @drift_b=(SELECT hp FROM items WHERE id='+str(b+600000)+');'
    setup+=(ROOT/'eq-solo-gm/scripts/thj-stock-bootstrap.sql').read_text()
    setup+=f"SELECT 'CUSTOM_NORMAL_SKIPPED',hp=@drift_a FROM items WHERE id={a+600000};SELECT 'MISSING_FAMILY_SKIPPED',hp=@drift_b FROM items WHERE id={b+600000};SELECT 'ELIGIBLE_UPDATED',i.hp=f.hp FROM items i JOIN bootstrap_fixture f ON f.id=i.id WHERE i.id={c+600000};"
    result=rehearse.sql(setup).stdout.strip();assert result=='CUSTOM_NORMAL_SKIPPED\t1\nMISSING_FAMILY_SKIPPED\t1\nELIGIBLE_UPDATED\t1',result
    (REL/'bootstrap-guards.json').write_text(json.dumps(dict(status='passed',checks=3,database=rehearse.DB,temporary_only=True,output=result.splitlines()),indent=2)+'\n');print(result)
if __name__=='__main__':main()
