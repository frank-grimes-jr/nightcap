"""Run production currency/saved-state function bodies with explicit dependency fakes."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile


def run(root, base, output):
    results = {}
    for name in ('currency', 'saved_state'):
        source = root / f'server-mods/code/zone/advanced_loot_{name}.cpp'
        body = '\n'.join(line for line in source.read_text().splitlines() if not line.startswith('#include '))
        fixture = Path(__file__).with_name(f'advanced_loot_{name}_fixture.cpp').read_text()
        with tempfile.TemporaryDirectory(prefix=f'nightcap-advloot-{name}-') as temporary:
            folder = Path(temporary)
            (folder / 'test.cpp').write_text(fixture.replace('// ACTUAL_TRANSLATION_UNIT', body))
            (folder / 'build.cmd').write_text(
                '@echo off\ncall "C:/BuildTools/VC/Auxiliary/Build/vcvars32.bat" >nul || exit /b 1\n'
                f'cl /nologo /EHsc /W4 /DWIN32 /DNOMINMAX /std:c++20 /I"{(root / "server-mods/code").as_posix()}" '
                f'/I"{base.as_posix()}" test.cpp bcrypt.lib /Fe:test.exe >build.log 2>&1\nexit /b %errorlevel%\n')
            built = subprocess.run(['cmd', '/d', '/c', str(folder / 'build.cmd')], cwd=folder)
            if built.returncode:
                raise RuntimeError((folder / 'build.log').read_text())
            tested = subprocess.run([str(folder / 'test.exe')], capture_output=True, text=True)
            if tested.returncode:
                raise RuntimeError(tested.stdout + tested.stderr)
            results[name] = {'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                             'fixture_sha256': hashlib.sha256(Path(__file__).with_name(f'advanced_loot_{name}_fixture.cpp').read_bytes()).hexdigest(),
                             'result': tested.stdout.strip()}
            print(tested.stdout.strip())
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({'status': 'passed', 'scope': 'production currency and saved-state bodies; dependency fakes, no native gameplay',
                                  'results': results}, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--base', type=Path, required=True, help='read-only EQEmu base source providing json.hpp/types.h')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.root.resolve(), args.base.resolve(), args.output.resolve())
