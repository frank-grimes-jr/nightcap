"""Package reviewed local test artifacts; never activate, sign, or publish gameplay."""
import hashlib,json,shutil,subprocess,sys,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];REL=Path(__file__).resolve().parent
OUT=Path('E:/EQ_Local_Dev/artifacts/thj-behaviors-20261019/test-bundle-v1')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def prepare():
    build=json.loads((REL/'native-build-manifest.json').read_text())
    for name,digest in build['requested_sources'].items():assert sha(ROOT/'server-mods/code'/name)==digest,name
    OUT.mkdir(exist_ok=True);(OUT/'server/bin').mkdir(parents=True,exist_ok=True)
    for name in ('world','zone','shared_memory'):
        p=OUT/'server/bin'/name
        subprocess.run(['docker','cp','akk-stack-eqemu-server-1:/tmp/nightcap-thj-behaviors-v1/build/bin/'+name,str(p)],check=True)
        assert sha(p)==build[name+'_sha256'],name
    with tarfile.open(OUT/'server-linux.tar.gz','w:gz',compresslevel=6) as archive:
        for name in ('world','zone','shared_memory'):
            p=OUT/'server/bin'/name;info=archive.gettarinfo(p,arcname='bin/'+name);info.mode=0o755
            with p.open('rb') as stream:archive.addfile(info,stream)
    with tarfile.open(OUT/'server-linux.tar.gz','r:gz') as archive:
        for member in archive.getmembers():
            assert member.mode==0o755
            with archive.extractfile(member) as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==build[Path(member.name).name+'_sha256']
    print('Paired server archive verified',flush=True)
def main():
    for name,key,value in [('database-rehearsal.json','status','passed'),('bootstrap-guards.json','status','passed'),('automated-tests.json','passed',True),('supplemental-tests.json','passed',True),('migration-tests.json','passed',True)]:assert json.loads((REL/name).read_text())[key]==value,name
    build=json.loads((REL/'native-build-manifest.json').read_text())
    for name,digest in build['requested_sources'].items():assert sha(ROOT/'server-mods/code'/name)==digest,name
    for name in ('world','zone','shared_memory'):assert sha(OUT/'server/bin'/name)==build[name+'_sha256']
    files={}
    for name in ('content-forward.sql','gear-forward.sql.gz','rule-forward.sql'):files['content/'+name]=REL/name
    for name in ('content-rollback.sql','gear-rollback.sql.gz','rule-disable.sql','rule-enable.sql'):files['recovery/'+name]=REL/name
    for name in ('README.md','CHANGELIST.md','QA.md'):files['guides/'+name]=REL/name
    for name in ('native-build-manifest.json','client-stage.json','database-rehearsal.json','bootstrap-guards.json','automated-tests.json','supplemental-tests.json','native-verification.json','aa-native-verification.json','migration-tests.json','cache-verification.json','wiki-publication.json','wiki-public-verification.json'):files['evidence/'+name]=REL/name
    client=json.loads((REL/'client-stage.json').read_text())
    for name,record in client['files'].items():
        source=Path('E:/EQ_Local_Dev/artifacts/thj-behaviors-20261019/client-candidate-v1')/name
        assert sha(source)==record['sha256'],name;files['client-delta/'+name]=source
    for name,source in files.items():
        target=OUT/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
    (OUT/'README.txt').write_text('THJ custom AA / focus / stock gear TEST CANDIDATE. Not deployed or owner accepted.\nRead guides/README.md and QA.md. Apply only to a stopped isolated clone of the matching base.\nContent SQL must stop on the first error. Decompress gear SQL before piping to MariaDB; do not use --force.\nRegenerate complete item/spell caches on the target with the paired loader and existing runtime credentials.\nNo diagnostic or incomplete caches, account configuration, credentials or player snapshots are included.\nThe unsigned two-file client delta requires signed2026101901 with proxy0.11.0 and its catalog.\nClassic50 and starter progression remain. Server-linux.tar.gz preserves executable modes.\nProduction activation, launcher signing and owner gameplay acceptance are separate steps.\n')
    manifest=dict(status='staged_not_installed_or_signed',path=OUT.as_posix(),source_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),files={p.relative_to(OUT).as_posix():dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='manifest.json'})
    for name,row in manifest['files'].items():assert sha(OUT/name)==row['sha256']
    text=json.dumps(manifest,indent=2)+'\n';(OUT/'manifest.json').write_text(text);(REL/'test-bundle.json').write_text(text)
    print(json.dumps(dict(status=manifest['status'],files=len(manifest['files']),path=str(OUT))))
if __name__=='__main__':prepare() if '--prepare-server' in sys.argv else main()
