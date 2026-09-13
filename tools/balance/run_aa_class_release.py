"""Run class-release controls in the isolated balance clone, restoring fixtures."""
import argparse
import json
from aa_class_release_controls import cases,assess
from aa_policy_preflight import read_json
from run_aa_owned_core import counts
import run_aa_projection as io

TRIGGER='nightcap_class_release_failure'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase',choices=('before','after'),required=True)
    parser.add_argument('--persisted-skills',action='store_true',help='Load actual fixture skills instead of synthetic combat caps')
    args=parser.parse_args()
    if io.DATABASE!='nightcap_balance_20260912' or any(counts().values()):
        raise ValueError('Only the empty isolated balance character/AA fixtures are allowed')
    if int(io.sql("SELECT COUNT(*) FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA='"+io.DATABASE+"' AND TRIGGER_NAME='"+TRIGGER+"';").strip()):
        raise ValueError('Prior failure trigger exists')
    runtime_phase='matched-before' if args.phase=='before' and args.persisted_skills else args.phase
    io.RUNTIME='/tmp/nightcap-balance-aa-release-'+runtime_phase+'-20260913'
    controls=cases(read_json(io.DOCS/'gear-source-inputs.json'))
    if args.persisted_skills:
        for case in controls: case['input']['aa_ownership_probe']['load_release_skills']=True
    catalog=io.digest(io.dump_tables())
    classes=io.sql('SELECT id,character_id,class2,class3,applied_at FROM character_multiclass ORDER BY character_id;')
    skills=io.sql('SELECT id,skill_id,value FROM character_skills ORDER BY id,skill_id;')
    build=json.loads(io.command(['docker','exec',io.SERVER,'cat',io.RUNTIME+'/native-build-manifest.json']))
    binary=io.command(['docker','exec',io.SERVER,'sha256sum',io.RUNTIME+'/balance-zone']).decode().split()[0]
    if binary!=build['binary_sha256']: raise ValueError('Diagnostic binary changed')
    results=[]
    for case in controls:
        char=case['rows'][0]['id']
        if any(counts().values()) or io.sql(f'SELECT COALESCE(class2,0),COALESCE(class3,0) FROM character_multiclass WHERE character_id={char};').strip()!='2\t12':
            raise ValueError('Class fixture differs from the reviewed original')
        if io.sql(f'SELECT id FROM character_skills WHERE id={char};').strip():
            raise ValueError('Release probe expects no persisted skills for this synthetic character')
        stamp=next(line.split('\t')[4] for line in classes.splitlines() if line.split('\t')[1]==str(char))
        spent=case['input']['aa_ownership_probe']['initial_spent_points']
        io.sql(f"INSERT INTO character_data (id,name,aa_points,aa_points_spent,e_expended_aa_spent) VALUES ({char},'AA_Lifecycle_Probe',17,{spent},5);"+
               'INSERT INTO character_alternate_abilities (id,aa_id,aa_value,charges) VALUES '+
               ','.join('('+','.join(str(r[k]) for k in ('id','aa_id','aa_value','charges'))+')' for r in case['rows'])+';')
        injected=False
        try:
            if case['fail_table']:
                if case['fail_table'] not in ('character_multiclass','character_data'): raise ValueError('Unexpected failure target')
                io.sql('DELIMITER //\nCREATE TRIGGER '+TRIGGER+' BEFORE UPDATE ON '+case['fail_table']+" FOR EACH ROW BEGIN SET @nightcap_class_release_failures=COALESCE(@nightcap_class_release_failures,0)+1; SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='injected class-release update failure'; END //\nDELIMITER ;")
                injected=True
            native=io.native(case['input'])
            results.append({'id':case['id'],**native,'assessment':assess(case,native['report'])})
        finally:
            if injected: io.sql('DROP TRIGGER '+TRIGGER+';')
            owned=io.sql('SELECT id,aa_id,aa_value,charges FROM character_alternate_abilities ORDER BY id,aa_id;').strip()
            expected={'\t'.join(str(r[k]) for k in ('id','aa_id','aa_value','charges')) for r in case['rows']}
            saved=io.sql(f'SELECT COALESCE(class2,0),COALESCE(class3,0) FROM character_multiclass WHERE character_id={char};').strip()
            wallet=io.sql('SELECT id,name,aa_points FROM character_data ORDER BY id;').strip()
            if not set(owned.splitlines()).issubset(expected) or saved not in ('2\t12','2\t0','12\t0') or wallet not in {f'{char}\tAA_Lifecycle_Probe\t{n}' for n in (17,35,47)}:
                io.write(io.DOCS/'aa-release-unexpected.json',{'case':case,'owned':owned,'classes':saved,'character':wallet,'results':results})
                raise ValueError('Unexpected release fixture preserved')
            if io.sql('SELECT id,skill_id,value FROM character_skills ORDER BY id,skill_id;')!=skills:
                raise ValueError('Unexpected skill writes preserved')
            io.sql(f'START TRANSACTION; DELETE FROM character_alternate_abilities WHERE id={char} AND aa_id IN (107,267); DELETE FROM character_data WHERE id={char}; UPDATE character_multiclass SET class2=2,class3=12,applied_at=\"{stamp}\" WHERE character_id={char}; COMMIT;')
    final={'remaining_rows':counts(),'catalog_unchanged':io.digest(io.dump_tables())==catalog,
           'class_values_restored':io.sql('SELECT id,character_id,class2,class3,applied_at FROM character_multiclass ORDER BY character_id;')==classes,
           'skills_unchanged':io.sql('SELECT id,skill_id,value FROM character_skills ORDER BY id,skill_id;')==skills,
           'catalog_sha256':catalog,
           'failure_trigger_remaining':int(io.sql("SELECT COUNT(*) FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA='"+io.DATABASE+"' AND TRIGGER_NAME='"+TRIGGER+"';").strip())}
    stem='aa-release-'+('matched-' if args.persisted_skills else '')+args.phase
    io.write(io.DOCS/(stem+'-inputs.json'),{'cases':controls})
    io.write(io.DOCS/(stem+'-build.json'),build)
    io.write(io.DOCS/(stem+'.json.gz'),{'binary_sha256':binary,'cases':results,'final':final,
             'persisted_skill_fixture':args.persisted_skills,'scope':'Native purge plus current quest SQL sequence, or native atomic slot entry when present. Synthetic rows; ClientDataLoaded is false so the old general Save exits early. Failure counters distinguish armed from executed injections. No quest interpreter, reconnect, or skill-state simulation.'})
    if final['failure_trigger_remaining'] or any(final['remaining_rows'].values()) or not all(final[k] for k in ('catalog_unchanged','class_values_restored','skills_unchanged')):
        raise ValueError('Clone restoration failed')
    if any(r['assessment']['passed']!=(args.phase=='after' or c['expected_before_pass']) for r,c in zip(results,controls)):
        raise ValueError('Release controls differ from expected phase outcomes; evidence retained')
    print(json.dumps({'phase':args.phase,'cases':[{'id':r['id'],'passed':r['assessment']['passed'],'differences':len(r['assessment']['differences'])} for r in results],'final':final},indent=2))


if __name__=='__main__': main()
