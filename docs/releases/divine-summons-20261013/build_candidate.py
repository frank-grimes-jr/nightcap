"""Build only the item loader from fingerprinted retained production source."""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import shutil
import subprocess

def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--base', type=Path, default=Path('/tmp/nightcap-zone-hunt-hardened-build-20261009'))
    args = parser.parse_args()
    base = args.base
    prior = json.loads((base/'manifest.json').read_text())
    assert prior['binaries']['shared_memory'] == '91664a87eac78306e8a76ab4cb923ba1f03c2d0da180278db6b6cf9b6607c0ef'
    assert sha(base/'build/bin/shared_memory') == prior['binaries']['shared_memory']
    assert all(sha(base/'source'/p) == h for p,h in prior['source_files'].items()), 'Retained source drift'
    inputs = json.loads((args.input/'input.json').read_text())
    assert all(sha(args.input/p) == h for p,h in inputs['files'].items()), 'Input drift'
    args.output.mkdir(exist_ok=False)
    source = args.output/'source'
    shutil.copytree(base/'source', source)
    loader = source/'common/shareddb.cpp'
    before = loader.read_text()
    after = before.replace('#include "item_trade_policy.h"', '#include "item_trade_policy.h"\n#include "divine_summoned_weapon_policy.h"')
    call = '\t\tEQ::ItemTradePolicy::Apply(item, RuleB(Items, FreeTrade), e.nodrop == 0);'
    assert before.count(call) == 1 and before.count('#include "item_trade_policy.h"') == 1
    after = after.replace(call, call+'\n\t\tNightcapDivineSummons::ApplyMerchantPolicy(item);')
    assert after == (args.input/'common/shareddb.cpp').read_text(), 'Git/retained loader differs beyond reviewed changes'
    loader.write_text(after)
    shutil.copyfile(args.input/'common/divine_summoned_weapon_policy.h', source/'common/divine_summoned_weapon_policy.h')
    cwd = base/'build/shared_memory'
    link = shlex.split((cwd/'CMakeFiles/shared_memory.dir/link.txt').read_text())
    retained = {str((cwd/p).resolve()):sha((cwd/p).resolve()) for p in link[1:] if (cwd/p).is_file()}
    archive = args.output/'libcommon.a'
    shutil.copyfile(base/'build/bin/libcommon.a', archive)
    flags = []
    for line in (base/'build/common/CMakeFiles/common.dir/flags.make').read_text().splitlines():
        if line.startswith(('CXX_DEFINES =','CXX_INCLUDES =','CXX_FLAGS =')):
            flags += shlex.split(line.split('=',1)[1].replace(str(base/'source'),str(source)))
    def run(name, command):
        print(name, flush=True)
        with (args.output/(name+'.log')).open('w') as log:
            result = subprocess.run(command,cwd=cwd,stdout=log,stderr=subprocess.STDOUT)
        if result.returncode:
            raise RuntimeError((args.output/(name+'.log')).read_text()[-6000:])
    obj = args.output/'shareddb.cpp.o'
    compile_command = ['/usr/bin/clang++',*flags,'-c',str(loader),'-o',str(obj)]
    run('compile-shareddb', compile_command)
    members = subprocess.check_output(['ar','t',str(archive)],text=True).splitlines()
    assert members.count('shareddb.cpp.o') == 1
    run('replace-object',['ar','r',str(archive),str(obj)])
    assert subprocess.check_output(['ar','t',str(archive)],text=True).splitlines() == members
    for member in members:
        expected = obj.read_bytes() if member == 'shareddb.cpp.o' else subprocess.check_output(['ar','p',str(base/'build/bin/libcommon.a'),member])
        assert subprocess.check_output(['ar','p',str(archive),member]) == expected, member
    link[link.index('../bin/libcommon.a')] = str(archive)
    link[link.index('-o')+1] = str(args.output/'shared_memory')
    run('link-shared-memory',link)
    run('ldd',['ldd',str(args.output/'shared_memory')])
    assert 'not found' not in (args.output/'ldd.log').read_text()
    assert all(sha(Path(p)) == h for p,h in retained.items()), 'Retained link input drift'
    assert all(sha(base/'source'/p) == h for p,h in prior['source_files'].items())
    fields = ['ID','Price','FixedSellPrice','Damage','Delay','SpellDmg','HealAmt']
    layout = '#include "common/item_data.h"\n#include <cstddef>\n#include <cstdio>\nint main(){printf("%zu",sizeof(EQ::ItemData));'
    layout += ''.join('printf(" %zu",offsetof(EQ::ItemData,'+f+'));' for f in fields)+'puts("");}\n'
    (args.output/'layout.cpp').write_text(layout)
    run('layout',['clang++','-std=c++20','-I'+str(source),str(args.output/'layout.cpp'),'-o',str(args.output/'layout')])
    sizes = list(map(int,subprocess.check_output([str(args.output/'layout')],text=True).split()))
    result = dict(status='built_not_installed',source_commit=inputs['source_commit'],
                  base_manifest_sha256=sha(base/'manifest.json'),base_loader_sha256=prior['binaries']['shared_memory'],
                  loader_sha256=sha(args.output/'shared_memory'),source_files={**prior['source_files'],
                  'common/shareddb.cpp':sha(loader),'common/divine_summoned_weapon_policy.h':sha(source/'common/divine_summoned_weapon_policy.h')},
                  compile_command=compile_command,link_command=link,retained_link_inputs=retained,
                  archive_members_preserved=len(members)-1,item_size=sizes[0],offsets=dict(zip(fields,sizes[1:])))
    (args.output/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('status','loader_sha256','archive_members_preserved','item_size','offsets')}),flush=True)

if __name__ == '__main__':
    main()
