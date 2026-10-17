"""Build only changed journal translation units against the deployed retained objects."""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import shutil
import subprocess

FILES = ('zone/dungeon_service.cpp', 'zone/dungeon_service.h', 'zone/task_manager.cpp',
         'zone/task_client_state.cpp', 'zone/task_client_state.h')
DEPLOYED_MANIFEST = 'c7b9d843ca1235b92c2495ba089faaa2b324fd1ae269db335c84d3c4ef119e34'
DEPLOYED_ZONE = '785faf9e08856bb5355ffd46e4d4aa6d93f687a8bbbc6b40c2fa3d1692d4c524'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def fingerprints(root):
    return {p.relative_to(root).as_posix(): sha(p) for p in sorted(root.rglob('*'))
            if p.is_file() and '.git' not in p.parts}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--base', type=Path, default=Path('/tmp/nightcap-dungeon-build-20261016'))
    args = parser.parse_args()
    assert sha(args.base/'manifest.json') == DEPLOYED_MANIFEST, 'Unreviewed baseline manifest'
    base = json.loads((args.base/'manifest.json').read_text())
    assert base['binaries']['zone'] == DEPLOYED_ZONE
    assert fingerprints(args.base/'source') == base['source_files'], 'Retained source drift'
    for name, digest in base['binaries'].items():
        assert sha(args.base/'build/bin'/name) == digest, name
    args.output.mkdir(exist_ok=False)
    source = args.output/'source'
    shutil.copytree(args.base/'source', source)
    for name in FILES:
        shutil.copyfile(args.input/name, source/name)
    before = fingerprints(source)
    assert sorted(n for n,h in before.items() if base['source_files'].get(n) != h) == sorted(FILES)
    # Added free/nonvirtual member declarations do not change any object layout.
    allowed = {
        'zone/task_client_state.h': ['\t// Project an externally completed all-activity task into history. This does\n'
            '\t// not dispatch quest events, complete an active task, or grant task rewards.\n'
            '\tbool RecordCompletedTaskFromLedger(Client *client, int task_id, int completed_time);\n'],
        'zone/dungeon_service.h': ['struct TaskInformation;\n',
            '// Adapt the installed v1 journal definitions for visible RoF2 objectives.\n'
            'void ConfigureJournalTask(int task_id, TaskInformation &task);\n']}
    for name, additions in allowed.items():
        restored = (source/name).read_text()
        for addition in additions:
            assert restored.count(addition) == 1
            restored = restored.replace(addition,'',1)
        assert restored == (args.base/'source'/name).read_text(), 'Unexpected header/ABI change: '+name
    cwd = args.base/'build/zone'
    flags = {}
    for line in (cwd/'CMakeFiles/zone.dir/flags.make').read_text().splitlines():
        if line.startswith(('CXX_DEFINES =', 'CXX_INCLUDES =', 'CXX_FLAGS =')):
            key,value = line.split('=',1)
            flags[key.strip()] = shlex.split(value.replace(str(args.base/'source'),str(source)))
    link = shlex.split((cwd/'CMakeFiles/zone.dir/link.txt').read_text())
    inputs = {str((cwd/p).resolve()):sha((cwd/p).resolve()) for p in link[1:]
              if p.endswith(('.o','.a','.so')) and (cwd/p).is_file()}
    commands = []

    def run(label, command):
        print(label, flush=True)
        with (args.output/(label+'.log')).open('w') as log:
            result = subprocess.run(command,cwd=cwd,stdout=log,stderr=subprocess.STDOUT)
        if result.returncode:
            print((args.output/(label+'.log')).read_text()[-8000:],flush=True)
            raise RuntimeError(label+' failed')

    for name in FILES:
        if not name.endswith('.cpp'):
            continue
        target = args.output/(Path(name).name+'.o')
        command = ['/usr/bin/clang++']+flags['CXX_DEFINES']+flags['CXX_INCLUDES']+flags['CXX_FLAGS']
        # Match CMake's forced includes, compiled from the candidate headers.
        # Reusing the old binary PCH would hide the added task declarations.
        for header in ('common/pch/app-pch.h','common/pch/std-pch.h','zone/pch/pch.h'):
            command += ['-include',str(source/header)]
        command += ['-c',str(source/name),'-o',str(target)]
        run('compile-'+Path(name).stem,command)
        commands.append(command)
        old = 'CMakeFiles/zone.dir/'+Path(name).name+'.o'
        assert link.count(old) == 1
        link[link.index(old)] = str(target)
    link[link.index('-o')+1] = str(args.output/'zone')
    run('link',link)
    # Re-link the unchanged baseline as proof the retained object set still
    # produces the exact deployed binary, not merely a stable local object set.
    baseline_link = shlex.split((cwd/'CMakeFiles/zone.dir/link.txt').read_text())
    baseline_link[baseline_link.index('-o')+1] = str(args.output/'baseline-zone')
    run('verify-baseline-link',baseline_link)
    assert sha(args.output/'baseline-zone') == base['binaries']['zone'], 'Retained objects do not reproduce deployed zone'
    run('ldd',['ldd',str(args.output/'zone')])
    assert 'not found' not in (args.output/'ldd.log').read_text()
    assert all(sha(Path(p)) == h for p,h in inputs.items()), 'Retained link-input drift'
    assert fingerprints(source) == before, 'Candidate source changed during build'
    assert fingerprints(args.base/'source') == base['source_files']
    for name,digest in base['binaries'].items():
        assert sha(args.base/'build/bin'/name) == digest
    result = {'status':'built_not_installed','source_files':before,'changed_sources':list(FILES),
              'zone_sha256':sha(args.output/'zone'),'baseline_manifest_sha256':sha(args.base/'manifest.json'),
              'base_binaries':base['binaries'],'unchanged_link_inputs':inputs,
              'retained_baseline_relinked_sha256':sha(args.output/'baseline-zone'),
              'compile_commands':commands,'link_command':link,
              'item_abi_changed':False,'sql_changed':False,'client_changed':False,'owner_visible_qa':'pending'}
    (args.output/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'zone_sha256':result['zone_sha256']}),flush=True)


if __name__ == '__main__':
    main()
