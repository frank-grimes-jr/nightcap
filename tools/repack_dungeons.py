"""Refresh verified SQL/docs in the paired package without rerolling its cache.

Checks every previous member hash before replacing the task-owned output archive.
Native binaries/cache remain byte-identical. No server or database operations.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import tarfile

ROOT=Path(__file__).resolve().parents[1]
PREFIX='nightcap-dungeons-20261016/'

class DigestReader:
    def __init__(self,stream):self.stream=stream;self.digest=hashlib.sha256()
    def read(self,count):
        chunk=self.stream.read(count);self.digest.update(chunk);return chunk

def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('archive',type=Path);args=parser.parse_args()
    archive=args.archive.resolve();original=sha(archive)
    assert original==archive.with_name(archive.name+'.sha256').read_text().split()[0]
    with tarfile.open(archive,'r:gz') as old:
        manifest=json.load(old.extractfile(PREFIX+'manifest.json'))
    replacements={'sql/'+p.name:p.read_bytes() for p in (ROOT/'server-mods/sql').glob('20261016_dungeon*.sql')}
    for name in ('README.md','QA.md','SPEC.md','catalog.json','activation-verification.json','concurrency-verification.json','verification.json','review.md'):
        replacements['docs/'+name]=(ROOT/'docs/dungeons'/name).read_bytes()
    replacements['quests/global/Instance_Keeper.pl']=(ROOT/'server-mods/quests/global/Instance_Keeper.pl').read_bytes()
    temporary=ROOT.parent/'dungeon-package-final.tar.gz'
    seen=set();after={}
    with tarfile.open(archive,'r|gz') as old,tarfile.open(temporary,'w:gz',compresslevel=5) as new:
        for member in old:
            assert member.name=='nightcap-dungeons-20261016' or member.name.startswith(PREFIX)
            relative=member.name[len(PREFIX):]
            assert '..' not in PurePosixPath(member.name).parts
            if member.isdir():new.addfile(member);continue
            assert member.isfile(),'Unexpected package member'
            if relative=='manifest.json':continue
            assert relative in manifest['files'] and relative not in seen
            reader=DigestReader(old.extractfile(member))
            if relative in replacements:
                while reader.read(1024*1024):pass
            else:
                new.addfile(member,reader);after[relative]=manifest['files'][relative]
            assert reader.digest.hexdigest()==manifest['files'][relative],relative
            seen.add(relative)
        assert seen==set(manifest['files'])
        for relative,data in replacements.items():
            member=tarfile.TarInfo(PREFIX+relative);member.size=len(data);member.mode=0o644
            new.addfile(member,io.BytesIO(data));after[relative]=hashlib.sha256(data).hexdigest()
        manifest['files']=dict(sorted(after.items()))
        data=(json.dumps(manifest,indent=2)+'\n').encode()
        member=tarfile.TarInfo(PREFIX+'manifest.json');member.size=len(data);member.mode=0o644
        new.addfile(member,io.BytesIO(data))
    assert sha(archive)==original,'Output changed during packaging'
    temporary.replace(archive)
    digest=sha(archive)
    archive.with_name(archive.name+'.sha256').write_text(digest+'  '+archive.name+'\n')
    (ROOT/'docs/dungeons/package-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    result=dict(status='passed',archive_sha256=digest,members=len(after),
                all_prior_members_verified=True,native_and_cache_preserved=True)
    (ROOT/'docs/dungeons/package-verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))

if __name__=='__main__':main()
