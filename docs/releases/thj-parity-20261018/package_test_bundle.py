"""Stage verified test artifacts locally; never install, sign or publish them."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tarfile

ROOT=Path(__file__).resolve().parents[3]
REL=Path(__file__).resolve().parent
OUT=ROOT.parent/'thj-parity-test-bundle'
PET=ROOT/'docs/releases/thj-pet-scaling-20261018/content'
WPM=ROOT/'docs/releases/wpm-melee-20261018/content'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    build=json.loads((REL/'evidence/native-build-manifest.json').read_text())
    pairing=json.loads((REL/'evidence/native-pairing.json').read_text())
    comparison=json.loads((REL/'evidence/native-comparison.json').read_text())
    assert pairing['status']==comparison['status']=='passed'
    assert comparison['execution_cases']==47
    for name,digest in build['requested_sources'].items():
        assert hashlib.sha256((ROOT/'server-mods/code'/name).read_bytes().replace(b'\r\n',b'\n')).hexdigest()==digest,name
    OUT.mkdir(exist_ok=False)
    (OUT/'server/bin').mkdir(parents=True)
    for name in ('world','zone','shared_memory'):
        target=OUT/'server/bin'/name
        subprocess.run(['docker','cp',f'akk-stack-eqemu-server-1:/tmp/nightcap-thj-parity-v1/build/bin/{name}',str(target)],check=True)
        assert sha(target)==build[name+'_sha256'],name
    files={
        'content/01-pet-equipment-schema.sql':ROOT/'server-mods/sql/2026-10-18-pet-equipment.sql',
        'content/02-shared-output-caps.sql':ROOT/'server-mods/sql/2026-10-18-shared-output-caps.sql',
        'content/03-rabid-forward.sql':PET/'rabid-forward.sql',
        'content/04-pet-support-forward.sql':PET/'pet-support-forward.sql',
        'content/05-wpm-aa-forward.sql':WPM/'aa-forward.sql',
        'content/06-heroic-melee-forward.sql':WPM/'heroic-rule-forward.sql',
        'content/07-pet-acquisition-forward.sql':REL/'content/pet-content-forward.sql',
        'content/08-wpm-acquisition-forward.sql':REL/'content/wpm-content-forward.sql',
        'content/09-combined-items-forward.sql':REL/'content/items-forward.sql',
        'content/10-spell-rules-forward.sql':REL/'content/rules-forward.sql',
        'recovery/items-numeric.sql':REL/'content/items-rollback.sql',
        'recovery/spell-rules-disable.sql':REL/'content/rules-disable.sql',
        'recovery/spell-rules-enable.sql':REL/'content/rules-enable.sql',
        'recovery/pet-acquisition.sql':PET/'pet-content-acquisition-rollback.sql',
        'recovery/wpm-acquisition.sql':WPM/'items-acquisition-rollback.sql',
        'recovery/heroic-melee-disable.sql':WPM/'heroic-rule-disable.sql',
        'recovery/heroic-melee-enable.sql':WPM/'heroic-rule-enable.sql',
    }
    for name in ('README.md','QA.md','ACTIVATION.md','COMPARISON.md'):
        files['guides/'+name]=REL/name
    for name in ('native-build-manifest.json','native-pairing.json','native-comparison.json','cache-manifest.json','client-stage.json'):
        files['evidence/'+name]=REL/'evidence'/name
    client=json.loads((REL/'evidence/client-stage.json').read_text())
    for name,record in client['files'].items():
        source=Path(client['output'])/name
        assert sha(source)==record['sha256'],name
        files['client-delta/'+name]=source
    for name,source in files.items():
        target=OUT/name
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,target)
    with tarfile.open(OUT/'server-linux.tar.gz','w:gz') as archive:
        for name in ('world','zone','shared_memory'):
            source=OUT/'server/bin'/name
            info=archive.gettarinfo(source,arcname='bin/'+name)
            info.mode=0o755
            with source.open('rb') as stream:
                archive.addfile(info,stream)
    (OUT/'README.txt').write_text(
        'Combined Nightcap THJ scaling TEST CANDIDATE. Not installed or signed.\n'
        'Read guides/ACTIVATION.md and QA.md before using these artifacts.\n'
        'server-linux.tar.gz contains matching world, zone and shared_memory, never the diagnostic executable.\n'
        'content/ is ordered reference material, not an unattended installer. Recheck target preimages; schema DDL is separate.\n'
        'Generate fresh item/spell caches on the test target. Captured diagnostic caches are not shipped.\n'
        'client-delta/ is unsigned and requires the current complete managed client base.\n'
        'Classic50 remains the current profile; PoP activation is outside this default bundle.\n'
        'No account configuration, database credentials or player snapshots are included.\n')
    manifest={'status':'staged_not_installed_or_signed','path':OUT.as_posix(),
        'source_revision':subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip(),
        'files':{p.relative_to(OUT).as_posix():{'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(OUT.rglob('*')) if p.is_file()}}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (REL/'evidence/test-bundle.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'status':manifest['status'],'files':len(manifest['files']),'path':str(OUT)}))


if __name__=='__main__':
    main()
