"""One-shot DoT zone deployment using the pinned current release operator.

Only the zone binary changes. No SQL content writes, client update, or snapshot
restore. Receipts and the prior operator's admission/backup/state gates remain.
"""
import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path

ROOT = Path('/opt/nightcap/deploy/production')
STAGE = Path('/opt/nightcap/releases/dot-no-initial-damage-20261112-v1')
AUTHORIZATION = 'Deploy it to the live server so I can test it in game.'
PRIOR = Path('/opt/nightcap/releases/quick-buff-20261112-v2/rollout.py')
PRIOR_SHA256 = '2c54fb5b25dc52186aca32ee8090a3efb78b44638b70408aa0801c7309c0e964'


def sha(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def initialize():
    manifest = json.loads((STAGE / 'manifest.json').read_text())
    assert manifest['owner_authorization'] == AUTHORIZATION
    assert manifest['prior_operator_sha256'] == sha(PRIOR) == PRIOR_SHA256
    for name, expected in manifest['files'].items():
        path = STAGE / name
        assert not path.is_symlink() and path.resolve().is_relative_to(STAGE)
        assert sha(path) == expected, name
    spec = importlib.util.spec_from_file_location('dot_release_base', PRIOR)
    prior = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prior)
    prior.initialize()
    assert prior.r.image_hashes(manifest['base_image_id']) == manifest['base_hashes']
    proof = json.loads((STAGE / 'native-build.json').read_text())
    checks = json.loads((STAGE / 'verification.json').read_text())
    assert proof['status'] == 'PASS' and proof['baseline_reproduced']
    assert proof['source_delta'] == ['zone/spell_effects.cpp']
    assert proof['binary_sha256']['baseline'] == manifest['base_hashes']['bin/zone']
    assert proof['binary_sha256']['candidate'] == manifest['binaries']['zone'] == manifest['files']['bin/zone']
    assert proof['candidate_source_sha256'] == manifest['files']['source/spell_effects.cpp']
    assert checks['green'] == {'dot_initial_damage': 2, 'gameplay_policies': 2,
                               'thj_spell_scaling': 2, 'thj_behavior_native': 1,
                               'client_spell_cast_times': 4}
    assert manifest['client_channel_sha256'] == prior.m['client_channel_sha256']
    # Bind the reviewed functions to this immutable stage/manifest, retaining
    # their exact drain, stopped backup, boot/market, hold and preservation gates.
    prior.STAGE = STAGE
    prior.EVIDENCE = STAGE / 'evidence'
    prior.TAG = 'nightcap-game:dot-no-initial-damage-20261112-v1'
    prior.m = manifest
    return prior


def main():
    assert __debug__
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('preflight', 'activate', 'open'))
    action = parser.parse_args().action
    prior = initialize()
    with (ROOT / '.deployment.lock').open('a') as lock, open('/var/lock/nightcap-gm.lock', 'a') as gm:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        fcntl.flock(gm, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert not (ROOT / 'private/gm-maintenance.json').exists()
        assert prior.a.sql("SELECT IS_FREE_LOCK('nightcap_gm_writes');").strip() == '1'
        {'preflight': prior.preflight, 'activate': prior.activate, 'open': prior.open_access}[action]()
    print('DoT release action verified: ' + action, flush=True)


if __name__ == '__main__':
    main()
