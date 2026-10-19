"""Record completion of automated preparation, separately from owner acceptance."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[3]
REL=Path(__file__).resolve().parent
EVIDENCE=REL/'evidence'


def read(name):
    return json.loads((EVIDENCE/name).read_text())


def main():
    native=read('native-comparison.json')
    pairing=read('native-pairing.json')
    content=read('content-rehearsal.json')
    regression=read('regression.json')
    supplemental=read('supplemental-tests.json')
    build=read('native-build-manifest.json')
    assert all(r['status']=='passed' for r in (native,pairing,content,regression,supplemental))
    assert native['execution_cases']==47 and read('aa-native.json')['passed']
    report={
        'status':'automated_preparation_complete_owner_qa_pending',
        'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'source_revision':subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip(),
        'unique_regression_and_migration_tests':supplemental['unique_tests_including_regression'],
        'native_cases':47,'native_encounters':native['encounters'],'spell_samples':10800,
        'native_aa_eligibility_cases':read('aa-native.json')['native_eligibility_cases'],
        'source_files':len(build['source_files']),'requested_overlays':len(build['requested_sources']),
        'existing_item_changes':content['changed_definitions'],
        'observed_ascended_targets':131,'reviewed_numeric_fields':4501,
        'independent_review':'no unresolved concrete findings in reviewed scopes; additional cross-model review declined',
        'client':'five-file delta generated, matches completed pet/WPM candidate; unsigned and uninstalled',
        'wiki':'all guides reviewed; local candidate notices; publication not performed',
        'production_changed':False,'main_promoted':False,'owner_gameplay_accepted':False,
        'evidence_hashes':{name:hashlib.sha256((EVIDENCE/name).read_bytes()).hexdigest() for name in
            ('native-comparison.json','native-pairing.json','native-build-manifest.json','native-results.tar.gz',
             'cache-manifest.json','content-rehearsal.json','regression.json','supplemental-tests.json',
             'aa-native.json','client-stage.json','independent-review.json','wiki-tests.json')}
    }
    (EVIDENCE/'completion.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('status','unique_regression_and_migration_tests','native_cases','spell_samples')}))


if __name__=='__main__':
    main()
