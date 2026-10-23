"""Refresh public loot snapshots atomically; no gameplay or schema writes.

The HTML release and data are independent. Readers use the immutable snapshot
named in index.json, so a refresh cannot mix item details from another capture.
"""
from contextlib import contextmanager
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
from loot_capture import capture
from loot_model import project

PUBLIC_ROOT=Path('/opt/nightcap/deploy/production/data/public/wiki-data')


def encoded(value):
    return (json.dumps(value,ensure_ascii=False,separators=(',',':'),allow_nan=False)+'\n').encode()


def publish(root, index, details, *, retain=8):
    root=Path(root)
    if root.is_symlink(): raise ValueError('Data root must not be a symlink')
    root.mkdir(parents=True,exist_ok=True)
    root=root.resolve()
    if not index['items'] or set(details)!={str(i['id']) for i in index['items']}:
        raise ValueError('Incomplete projection; refusing to replace previous data')
    if not 1<=len(details)<=100000: raise ValueError('Unexpected projection size')
    payloads={f'item-{key}.json':encoded(value) for key,value in details.items() if re.fullmatch(r'[1-9]\d{0,6}',key)}
    if len(payloads)!=len(details): raise ValueError('Unsafe item identity')
    digest=hashlib.sha256(encoded(index))
    for name,body in sorted(payloads.items()): digest.update(name.encode()+b'\0'+body)
    revision=digest.hexdigest()[:16]
    payloads['index.json']=encoded(index|{'snapshot':revision,'base_url':f'/loot-data/{revision}/'})
    target=root/revision
    current=root/'current'
    if current.exists() or current.is_symlink():
        if not current.is_symlink() or not re.fullmatch('[a-f0-9]{16}',str(current.readlink())):
            raise ValueError('Unsafe current pointer')
        if current.resolve().parent!=root: raise ValueError('Pointer escaped data root')
    if not target.exists():
        stage=Path(tempfile.mkdtemp(prefix='.stage-',dir=root))
        try:
            for name,body in payloads.items():
                with (stage/name).open('xb') as handle:
                    handle.write(body)
                    handle.flush()
                    os.fsync(handle.fileno())
            manifest={name:hashlib.sha256(body).hexdigest() for name,body in payloads.items()}
            (stage/'.manifest.json').write_bytes(encoded(manifest))
            # mkdtemp is 0700 regardless of service umask. Public nginx workers
            # need traversal after this directory becomes the served snapshot.
            stage.chmod(0o755)
            stage.rename(target)
        finally:
            if stage.exists():
                if stage.is_symlink() or stage.resolve().parent!=root: raise ValueError('Unsafe staging cleanup')
                shutil.rmtree(stage)
    else:
        if target.is_symlink() or target.resolve().parent!=root: raise ValueError('Unsafe snapshot target')
        for name,body in payloads.items():
            if (target/name).read_bytes()!=body: raise ValueError('Immutable snapshot differs')
    temporary=root/'.current-next'
    if temporary.exists() or temporary.is_symlink():
        # The process lock is held by the caller. A killed process can leave this
        # owned pointer between link creation and replace; validate before cleanup.
        if not temporary.is_symlink() or not re.fullmatch('[a-f0-9]{16}',str(temporary.readlink())) or temporary.resolve().parent!=root:
            raise ValueError('Unsafe previous pointer staging')
        temporary.unlink()
    temporary.symlink_to(revision,target_is_directory=True)
    try: os.replace(temporary,current)
    finally:
        if temporary.is_symlink(): temporary.unlink()
    snapshots=sorted((p for p in root.iterdir() if re.fullmatch('[a-f0-9]{16}',p.name) and not p.is_symlink() and p.is_dir()),key=lambda p:p.stat().st_mtime,reverse=True)
    # Retain old snapshots for open tabs. Only exact owned directories under this
    # validated root can be removed, and never the current snapshot.
    for old in snapshots[max(2,retain):]:
        if old.name==revision: continue
        if old.resolve().parent!=root: raise ValueError('Unsafe retention target')
        shutil.rmtree(old)
    return {'snapshot':revision,'items':len(details),'public_files':len(payloads),
            'bytes':sum(map(len,payloads.values())),'captured_at':index['captured_at']}


@contextmanager
def locked(path):
    import fcntl
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('a') as handle:
        fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        yield


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=PUBLIC_ROOT)
    parser.add_argument('--capture',type=Path,help='Use a private captured fixture for local verification')
    parser.add_argument('--output',type=Path,help='Write ordinary local preview files; no symlinks or retention')
    args=parser.parse_args()
    def run():
        raw=json.loads(gzip.decompress(args.capture.read_bytes())) if args.capture else capture()
        index,details=project(raw)
        if args.output:
            # Local preview mirrors public URLs without Windows symlink privileges.
            root=args.output/'loot-data';root.mkdir(parents=True,exist_ok=True)
            revision=hashlib.sha256(encoded(index)).hexdigest()[:16]
            directory=root/revision;directory.mkdir(exist_ok=True)
            index=index|{'snapshot':revision,'base_url':f'/loot-data/{revision}/'}
            for key,item in details.items():(directory/f'item-{key}.json').write_bytes(encoded(item))
            (directory/'index.json').write_bytes(encoded(index))
            (root/'current').mkdir(exist_ok=True);(root/'current/index.json').write_bytes(encoded(index))
            print(json.dumps({'items':len(details),'captured_at':index['captured_at'],'index_bytes':len(encoded(index))}))
        else: print(json.dumps(publish(args.root,index,details)))
    if args.output: run()
    else:
        with locked(args.root.parent/'.wiki-loot-refresh.lock'): run()


if __name__=='__main__': main()
