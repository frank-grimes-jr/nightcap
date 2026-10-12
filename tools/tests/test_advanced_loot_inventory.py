"""Execute actual candidate inventory-transfer code with failure-injection fakes."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile


def run(root: Path, output: Path):
    root = root.resolve()
    source = root / 'server-mods/code/zone/advanced_loot_inventory.cpp'
    # Only dependency includes are replaced; every function body is production code.
    body = '\n'.join(line for line in source.read_text().splitlines() if not line.startswith('#include '))
    fixture = Path(__file__).with_name('advanced_loot_inventory_fixture.cpp').read_text()
    fixture = fixture.replace('ADVANCED_LOOT_POLICY_PATH', (root / 'server-mods/code/zone/advanced_loot_inventory.h').as_posix())
    with tempfile.TemporaryDirectory(prefix='nightcap-advloot-inventory-') as temporary:
        folder = Path(temporary)
        (folder / 'test.cpp').write_text(fixture.replace('// ACTUAL_TRANSLATION_UNIT', body))
        (folder / 'build.cmd').write_text('@echo off\ncall "C:/BuildTools/VC/Auxiliary/Build/vcvars32.bat" >nul || exit /b 1\n'
                                        f'cl /nologo /EHsc /W4 /std:c++17 /I"{(root / "server-mods/code").as_posix()}" test.cpp /Fe:test.exe >build.log 2>&1\nexit /b %errorlevel%\n')
        build = subprocess.run(['cmd', '/d', '/c', str(folder / 'build.cmd')], cwd=folder)
        if build.returncode:
            raise RuntimeError((folder / 'build.log').read_text())
        result = subprocess.run([str(folder / 'test.exe')], capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError(result.stdout + result.stderr)
        evidence = {'status': 'passed', 'scope': 'production inventory translation unit with dependency fakes; no native gameplay execution',
                    'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                    'queries': [line[4:] for line in result.stdout.splitlines() if line.startswith('SQL:')],
                    'upgrade_queries': [line[12:] for line in result.stdout.splitlines() if line.startswith('UPGRADE_SQL:')],
                    'forge_queries': [line[10:] for line in result.stdout.splitlines() if line.startswith('FORGE_SQL:')],
                    'result': result.stdout.splitlines()[-1]}
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(evidence, indent=2) + '\n')
        print(evidence['result'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.root, args.output)
