"""Run additional release controls only in the empty isolated balance clone."""
import json
from aa_class_release_extended import cases,assess
from aa_policy_preflight import read_json
from run_aa_owned_core import counts
import run_aa_projection as io

TRIGGER='nightcap_class_release_failure'

def main():
    if io.DATABASE!='nightcap_balance_20260912' or any(counts().values()): raise ValueError('Nonempty or unexpected clone')
    if io.sql('SELECT id FROM character_skills WHERE id=1;').strip(): raise ValueError('Unexpected character 1 skill rows')
    if int(io.sql("SELECT COUNT(*) FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=DATABASE() AND TRIGGER_NAME='"+TRIGGER+"';").strip()): raise ValueError('Prior trigger exists')
    io.RUNTIME='/tmp/nightcap-balance-aa-release-after-20260913'
    original_classes=io.sql('SELECT id,character_id,class2,class3,applied_at FROM character_multiclass ORDER BY character_id;')
    original_skills=io.sql('SELECT id,skill_id,value FROM character_skills ORDER BY id,skill_id;')
    original=next(line.split('\t') for line in original_classes.splitlines() if line.split('\t')[1]=='1')
    if original[2:4]!=['2','12']: raise ValueError('Class fixture differs from the reviewed original; no mutations allowed')
    stamp=original[4]
    catalog=io.digest(io.dump_tables())
    controls=cases(read_json(io.DOCS/'gear-source-inputs.json'))
    build=json.loads(io.command(['docker','exec',io.SERVER,'cat',io.RUNTIME+'/native-build-manifest.json']))
    binary=io.command(['docker','exec',io.SERVER,'sha256sum',io.RUNTIME+'/balance-zone']).decode().split()[0]
    if binary!=build['binary_sha256']: raise ValueError('Native binary changed')
    results=[]
    for case in controls:
        classes=case['classes']+[0]*(3-len(case['classes']))
        rows=case['rows']; skills=case['skills'];probe=case['input']['aa_ownership_probe']
        statements=["START TRANSACTION",f"INSERT INTO character_data (id,name,aa_points,aa_points_spent,e_expended_aa_spent) VALUES (1,'AA_Lifecycle_Probe',17,{probe['initial_spent_points']},5)",
                    f"UPDATE character_multiclass SET class2={classes[1]},class3={classes[2]} WHERE character_id=1"]
        if rows: statements.append('INSERT INTO character_alternate_abilities (id,aa_id,aa_value,charges) VALUES '+','.join('('+','.join(str(r[k]) for k in ('id','aa_id','aa_value','charges'))+')' for r in rows))
        if skills: statements.append('INSERT INTO character_skills (id,skill_id,value) VALUES '+','.join(f'(1,{k},{v})' for k,v in skills.items()))
        io.sql(';'.join(statements+['COMMIT'])+';')
        injected=False
        try:
            if case['fail_table']:
                if case['fail_table'] not in ('character_skills','character_data'): raise ValueError('Unexpected failure target')
                io.sql('DELIMITER //\nCREATE TRIGGER '+TRIGGER+' BEFORE UPDATE ON '+case['fail_table']+" FOR EACH ROW BEGIN SET @nightcap_class_release_failures=COALESCE(@nightcap_class_release_failures,0)+1; SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='injected release failure'; END //\nDELIMITER ;")
                injected=True
            native=io.native(case['input']);results.append({'id':case['id'],**native,'assessment':assess(case,native['report'])})
        finally:
            if injected: io.sql('DROP TRIGGER '+TRIGGER+';')
            # Never erase unrecognized fixture state. Allow only reviewed before/after rows.
            observed=io.sql('SELECT id,aa_id,aa_value,charges FROM character_alternate_abilities ORDER BY id,aa_id;').strip()
            allowed={'\t'.join(str(r[k]) for k in ('id','aa_id','aa_value','charges')) for r in rows}
            current_skills=io.sql('SELECT skill_id,value FROM character_skills WHERE id=1 ORDER BY skill_id;').strip()
            expected=case['expected'][-1]
            allowed_skills={f'{k}\t{v}' for k,v in skills.items()}|{str(r['id'])+'\t'+str(r['value']) for r in expected['saved_skills']}
            saved=io.sql('SELECT COALESCE(class2,0),COALESCE(class3,0) FROM character_multiclass WHERE character_id=1;').strip()
            wallet=io.sql('SELECT id,name,aa_points FROM character_data ORDER BY id;').strip()
            if not set(observed.splitlines()).issubset(allowed) or not set(current_skills.splitlines()).issubset(allowed_skills) or saved not in (str(classes[1])+'\t'+str(classes[2]),str(expected['saved_classes'][1])+'\t'+str(expected['saved_classes'][2])) or wallet not in ('1\tAA_Lifecycle_Probe\t17','1\tAA_Lifecycle_Probe\t'+str(expected['unspent_points'])):
                io.write(io.DOCS/'aa-release-extended-unexpected.json',{'case':case,'observed':observed,'skills':current_skills,'classes':saved,'wallet':wallet,'results':results})
                raise ValueError('Unexpected release fixture preserved')
            io.sql(f"START TRANSACTION; DELETE FROM character_alternate_abilities WHERE id=1; DELETE FROM character_skills WHERE id=1; DELETE FROM character_data WHERE id=1; UPDATE character_multiclass SET class2=2,class3=12,applied_at='{stamp}' WHERE character_id=1; COMMIT;")
    final={'remaining_rows':counts(),'catalog_unchanged':io.digest(io.dump_tables())==catalog,
           'failure_trigger_remaining':int(io.sql("SELECT COUNT(*) FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=DATABASE() AND TRIGGER_NAME='"+TRIGGER+"';").strip()),
           'classes_restored':io.sql('SELECT id,character_id,class2,class3,applied_at FROM character_multiclass ORDER BY character_id;')==original_classes,
           'skills_restored':io.sql('SELECT id,skill_id,value FROM character_skills ORDER BY id,skill_id;')==original_skills}
    io.write(io.DOCS/'aa-release-extended-inputs.json',{'cases':controls})
    io.write(io.DOCS/'aa-release-extended.json.gz',{'binary_sha256':binary,'cases':results,'final':final})
    print(json.dumps({'cases':[r['assessment'] for r in results],'final':final},indent=2))
    if final['failure_trigger_remaining'] or any(final['remaining_rows'].values()) or not all(final[k] for k in ('catalog_unchanged','classes_restored','skills_restored')) or not all(r['assessment']['passed'] for r in results): raise ValueError('Release controls or restoration failed; evidence retained')

if __name__=='__main__': main()
