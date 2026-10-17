"""Update an installed wiki with an atomic relative symlink and verified rollback.

Uses the existing publisher lock. Never edits Nginx, Cloudflare or game services.
"""
from pathlib import Path
import argparse
import fcntl
import json
import os
import re
import deploy


def release_name(value):
    if not re.fullmatch(r'\d{8}-[a-z0-9-]+', value):
        raise ValueError('Invalid release name')
    return value


def main(args):
    release_name(args.release)
    release_name(args.expected_release)
    base = deploy.BASE
    config = base/'nginx.conf'
    before_config = config.read_bytes()
    if deploy.sha(before_config) != args.expected_config_sha:
        raise ValueError('Web config changed; inspect before updating')
    root = base/'data/public/wiki'
    pointer = root/'current'
    previous = Path('releases')/args.expected_release
    target = Path('releases')/args.release

    def guard(expected, require_config=True):
        if require_config and config.read_bytes() != before_config:
            raise RuntimeError('Web config changed during update')
        if not pointer.is_symlink() or pointer.readlink() != expected:
            raise RuntimeError('Wiki pointer changed; refusing to overwrite it')

    guard(previous)
    if not (root/previous).is_dir() or (root/'releases').is_symlink():
        raise ValueError('Invalid release directory')
    old_manifest = json.loads((base/'website-history'/args.expected_release/'manifest.json').read_text())
    deploy.verify(old_manifest)
    old_services, old_protected = deploy.services(), deploy.protected()
    if len(old_services) != 5 or any(status != 200 for status, digest in old_protected.values()):
        raise RuntimeError('Production baseline is not healthy')
    manifest = json.loads(args.manifest.read_text())
    receipt = base/'website-history'/args.release
    receipt.mkdir(exist_ok=False)
    (receipt/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    (receipt/'baseline.json').write_text(json.dumps({'previous':str(previous), 'config_sha256':deploy.sha(before_config), 'services':old_services, 'protected':old_protected}, indent=2)+'\n')
    deploy.unpack(args.archive, manifest, root/target)
    temporary = root/('.current-'+args.release)

    def switch(expected, destination, require_config=True):
        guard(expected, require_config)
        # symlink_to fails if the temporary path exists, including a dangling link.
        temporary.symlink_to(destination)
        try:
            guard(expected, require_config)
            os.replace(temporary, pointer)
        finally:
            if temporary.is_symlink() and temporary.readlink() == destination:
                temporary.unlink()

    def preserved():
        if deploy.services() != old_services or deploy.protected() != old_protected:
            raise RuntimeError('Private downloads or service identities changed')
        if config.read_bytes() != before_config:
            raise RuntimeError('Origin configuration changed')

    try:
        switch(previous, target)
        deploy.verify(manifest)
        preserved()
        switch(target, previous)
        deploy.verify(old_manifest)
        preserved()
        switch(previous, target)
        deploy.verify(manifest)
        preserved()
        report = {'result':'PASS', 'release':args.release, 'previous_release':args.expected_release,
                  'files':len(manifest), 'config_sha256':deploy.sha(before_config),
                  'rollback_rehearsed':True, 'private_downloads_preserved':True,
                  'service_ids_start_times_preserved':True, 'nginx_reload_required':False}
        (receipt/'verification.json').write_text(json.dumps(report, indent=2)+'\n')
    except BaseException as failure:
        try:
            # Inspect the actual pointer: interruption can happen just after replace().
            # Restore only our pointer even if another operator changed the config.
            if pointer.is_symlink() and pointer.readlink() == target:
                switch(target, previous, require_config=False)
            guard(previous, require_config=False)
            deploy.verify(old_manifest)
            preserved()
        except BaseException as recovery:
            raise RuntimeError('Update failed; rollback needs attention: '+str(recovery)) from failure
        raise
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('release')
    parser.add_argument('expected_release')
    parser.add_argument('expected_config_sha')
    args = parser.parse_args()
    with (deploy.BASE/'website-history'/'.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        main(args)
