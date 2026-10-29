"""Resume the authenticated October29 final-reserve preflight failure only.

Retains the failed log and original receipt. No image build, service transition,
content installation or publication occurs. A failed resume is never replayed.
"""
import hashlib
import importlib.util
import json
import os
import shutil
from pathlib import Path

STAGE = Path('/opt/nightcap/releases/hate-layout-20261029-v1')
OPERATOR_SHA = '3f79d3833e431dc33c3e6f6323f950e3da328ec8924e26b7f7c2823641d05850'
MANIFEST_SHA = '468f85c5b7b5d9b108b1b55c108b7a068b04d11d7021f72290df0f58973987e8'
STARTED_SHA = 'c816d3dcc8f05de7fee05739bec9c89ecae4569502d2422c81f6decefc79ff7d'
FAILED_LOG_SHA = '88cb06bf2d5d31e85a3a11210ac6399bc23ec65b5f6d70bc23991f402cfd0169'
IMAGE = 'sha256:0dec2bfc8b2e83a30301c2fc203c5688d44a2b39cf354b5e0e0b2ba8ed38f9dd'
BASE_TAG = 'nightcap-game:hate-layout-20261029-v1-base'
CANDIDATE_TAG = 'nightcap-game:hate-layout-20261029-v1'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def authenticate(path, digest):
    assert path.resolve() == path and path.is_file() and not path.is_symlink(), str(path)
    assert sha(path) == digest, str(path)


def existing_image(op, manifest):
    r = op.r
    inspect = lambda name: r.out('docker', 'image', 'inspect', '--format', '{{.Id}}', name).strip()
    assert inspect(BASE_TAG) == manifest['base_image_id'], 'Base tag drift'
    assert inspect(CANDIDATE_TAG) == IMAGE, 'Candidate tag drift'
    assert inspect(IMAGE) == IMAGE
    layers = lambda name: json.loads(r.out('docker', 'image', 'inspect', name))[0]['RootFS']['Layers']
    assert layers(IMAGE)[:-1] == layers(manifest['base_image_id']), 'Candidate layer drift'
    assert r.image_hashes(manifest['base_image_id']) == manifest['base_hashes']
    assert r.image_hashes(IMAGE) == {**manifest['base_hashes'], **manifest['candidate_hashes']}
    for candidate in (IMAGE, manifest['base_image_id']):
        assert 'not found' not in r.out('docker', 'run', '--rm', '--network', 'none', '--entrypoint', 'ldd', candidate, '/opt/nightcap/bin/zone')
        r.call('docker', 'run', '--rm', '--network', 'none', '--entrypoint', 'python3', candidate, '-c',
               'import sys;sys.path.insert(0,"/opt/nightcap");import start;start.validate_native()')
        r.call('docker', 'run', '--rm', '--network', 'none', '--entrypoint', '/opt/nightcap/bin/loginserver', candidate, '--nightcap-crypto-self-test')
    assert inspect(CANDIDATE_TAG) == IMAGE and inspect(BASE_TAG) == manifest['base_image_id']


def resume(op):
    evidence = op.EVIDENCE
    started = evidence / 'preflight-started.json'
    failed_log = op.STAGE / 'preflight.log'
    authenticate(op.STAGE / 'rollout.py', OPERATOR_SHA)
    authenticate(op.STAGE / 'manifest.json', MANIFEST_SHA)
    authenticate(started, STARTED_SHA)
    authenticate(failed_log, FAILED_LOG_SHA)
    assert {path.name for path in evidence.iterdir()} == {'preflight-started.json'}, 'Unexpected attempt state; do not replay'
    log = failed_log.read_text()
    assert log.rstrip().endswith('AssertionError')
    assert 'assert shutil.disk_usage(ROOT).free>=RESERVE' in log, 'Failure was not the final disk guard'
    manifest = op.manifest()
    original = op.read(started)
    assert original['manifest_sha256'] == MANIFEST_SHA
    assert 'image' not in original
    services = original['services']
    assert all(service['running'] and not service['oom_killed'] for service in services.values())
    assert services['game']['health'] == services['db']['health'] == 'healthy'
    assert services['game']['image_id'] == manifest['base_image_id']
    assert all(op.r.compact(name) == value for name, value in services.items())
    op.unchanged(original)
    assert shutil.disk_usage(op.ROOT).free >= op.RESERVE
    op.save(evidence / 'preflight-resume-started.json', {
        'cause': 'completed image build; final disk reserve failed',
        'manifest_sha256': MANIFEST_SHA, 'operator_sha256': OPERATOR_SHA,
        'failed_log_sha256': FAILED_LOG_SHA, 'original_started_sha256': STARTED_SHA,
        'image': IMAGE, 'resume_sha256': sha(Path(__file__).resolve()), 'rebuild': False})
    # The prior image build consumed its scratch budget. Repeat the final reserve
    # requirement, not the pre-build allocation estimate for a build we do not run.
    op.r.running(manifest['base_image_id'], op.binaries(True), services['game']['restarts'])
    op.base.health()
    op.startup.startup_guards()
    op.r.closed_ports()
    checks = op.contract(False)
    assert checks == original['checks'], 'Original contract result drift'
    op.check_quest_preimages()
    public_checks = op.public_preflight()
    assert op.r.runtime() == manifest['runtime_preimage']
    existing_image(op, manifest)
    op.unchanged(original)
    assert all(op.r.compact(name) == value for name, value in services.items())
    op.base.health()
    op.startup.startup_guards()
    op.r.closed_ports()
    authenticate(started, STARTED_SHA)
    authenticate(failed_log, FAILED_LOG_SHA)
    authenticate(op.STAGE / 'manifest.json', MANIFEST_SHA)
    op.manifest()
    free = shutil.disk_usage(op.ROOT).free
    assert free >= op.RESERVE, 'Final disk reserve still unavailable'
    op.save(evidence / 'preflight-resume-verified.json', {
        'image': IMAGE, 'free_bytes': free, 'required_free_bytes': op.RESERVE,
        'checks': checks, 'public_checks': public_checks, 'rebuild': False,
        'services_and_publication_unchanged': True, 'original_evidence_retained': True})
    assert shutil.disk_usage(op.ROOT).free >= op.RESERVE
    op.save(evidence / 'preflight.json', {**original, 'image': IMAGE})
    print('Existing candidate reverified; preflight passed without rebuilding. Original failed evidence retained.', flush=True)


def main():
    import fcntl
    assert __debug__
    os.umask(0o077)
    authenticate(STAGE / 'rollout.py', OPERATOR_SHA)
    authenticate(STAGE / 'manifest.json', MANIFEST_SHA)
    spec = importlib.util.spec_from_file_location('hate_rollout_resume_target', STAGE / 'rollout.py')
    op = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(op)
    assert op.STAGE == STAGE
    op.initialize()
    with (op.ROOT / '.deployment.lock').open('a') as lock, open('/var/lock/nightcap-gm.lock', 'a') as gm:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        fcntl.flock(gm, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert not (op.ROOT / 'private/gm-maintenance.json').exists()
        assert op.sql("SELECT IS_FREE_LOCK('nightcap_gm_writes');").strip() == '1'
        resume(op)


if __name__ == '__main__':
    main()
