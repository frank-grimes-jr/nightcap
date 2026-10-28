"""Isolated native candidate relink; never changes retained build or running binaries."""
from pathlib import Path
import hashlib,json,shlex,shutil,subprocess,sys
HERE=Path(__file__).resolve().parent
BASE=Path('/tmp/nightcap-paladin-grip-20261026-v1')
assert HERE == Path('/tmp/nightcap-paladin-progression-20261028')
source=HERE/'source'
if not source.exists():shutil.copytree(BASE/'source',source,symlinks=True)
for p in (HERE/'overlay').rglob('*'):
 if p.is_file():shutil.copy2(p,source/p.relative_to(HERE/'overlay'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(args,cwd=None):
 with (HERE/'build.log').open('a') as log:subprocess.run(args,cwd=cwd,stdout=log,stderr=log,check=True)
objects={}
prior=json.loads((HERE/'build-manifest.json').read_text()) if '--relink' in sys.argv else None
if prior:
 assert all(sha(HERE/'overlay'/p)==s for p,s in prior['source_sha256'].items())
for part,name in [('common','item_instance'),('zone','bonuses'),('zone','inventory'),('zone','perl_client')]:
 flagsfile=BASE/f'build/{part}/CMakeFiles/{part}.dir/flags.make'
 flags=dict(l.split(' = ',1) for l in flagsfile.read_text().splitlines() if ' = ' in l)
 args=sum([shlex.split(flags[k]) for k in ['CXX_DEFINES','CXX_INCLUDES','CXX_FLAGS']],[])
 args=[a.replace(str(BASE/'source'),str(source)) for a in args]
 if part=='zone':
  for header in ['common/pch/app-pch.h','common/pch/std-pch.h','zone/pch/pch.h']:
   args+=['-include',str(source/header)]
 obj=HERE/f'{name}.cpp.o';src=source/part/f'{name}.cpp'
 if prior:
  assert sha(obj)==prior['objects'][f'{part}/{name}.cpp']['object_sha256']
  assert sha(src)==prior['objects'][f'{part}/{name}.cpp']['source_sha256']
 else:run(['/usr/bin/clang++',*args,'-c',str(src),'-o',str(obj)])
 objects[f'{part}/{name}.cpp']={'source_sha256':sha(src),'object_sha256':sha(obj)}
 print('Compiled',part,name,flush=True)
archive=HERE/'libcommon.a';shutil.copy2(BASE/'build/bin/libcommon.a',archive)
run(['ar','r',str(archive),str(HERE/'item_instance.cpp.o')])
perl_archive=HERE/'libperl_zone.a';shutil.copy2(BASE/'build/zone/libperl_zone.a',perl_archive)
perl_build=BASE/'build/zone/CMakeFiles/perl_zone.dir'
unity=next(p for p in (perl_build/'Unity').glob('*.cxx') if 'perl_client.cpp' in p.read_text())
unity_source=HERE/unity.name
unity_source.write_text(unity.read_text().replace(str(BASE/'source'),str(source)))
flags=dict(l.split(' = ',1) for l in (perl_build/'flags.make').read_text().splitlines() if ' = ' in l)
args=sum([shlex.split(flags[k]) for k in ['CXX_DEFINES','CXX_INCLUDES','CXX_FLAGS']],[])
args=[a.replace(str(BASE/'source'),str(source)) for a in args]
pch=perl_build/'cmake_pch.hxx'
if pch.exists():
 implicit=HERE/'perl_implicit.hxx';implicit.write_text(pch.read_text().replace(str(BASE/'source'),str(source)))
 args+=['-include',str(implicit)]
unity_object=HERE/(unity.name+'.o')
run(['/usr/bin/clang++',*args,'-c',str(unity_source),'-o',str(unity_object)])
run(['ar','r',str(perl_archive),str(unity_object)])
objects['perl_binding_unity']={'generated_source_sha256':sha(unity_source),'object_sha256':sha(unity_object)}
man={'date':'2026-10-28','status':'isolated relink of four changed translation units; unchanged retained objects reused','objects':objects,'binaries':{},'source_sha256':{str(p.relative_to(HERE/'overlay')):sha(p) for p in (HERE/'overlay').rglob('*') if p.is_file()}}
for target in ['zone','world','shared_memory']:
 build=BASE/f'build/{target}';link=shlex.split((build/f'CMakeFiles/{target}.dir/link.txt').read_text())
 for i,arg in enumerate(link):
  if arg.endswith('/libcommon.a'):link[i]=str(archive)
  if arg=='libperl_zone.a':link[i]=str(perl_archive)
  if target=='zone' and arg in [f'CMakeFiles/zone.dir/{n}.cpp.o' for n in ['bonuses','inventory','perl_client']]:link[i]=str(HERE/Path(arg).name)
 binary=HERE/target;link[link.index('-o')+1]=str(binary)
 run(link,cwd=build);man['binaries'][target]=sha(binary);print('Linked',target,flush=True)
man['retained_inputs']={str(p.relative_to(BASE/'build')):sha(p) for p in (BASE/'build').rglob('*.o')}
man['retained_archives']={str(p.relative_to(BASE/'build')):sha(p) for p in (BASE/'build').rglob('*.a')}
man['candidate_archives']={p.name:sha(p) for p in [archive,perl_archive]}
symbols=subprocess.check_output(['nm','-C',str(HERE/'zone')],text=True)
for symbol in ['Client::AscendPaladinEpic()', 'Perl_Client_AscendPaladinEpic(Client*)']:
 assert any(' T '+symbol in line for line in symbols.splitlines()),symbol
man['exchange_and_perl_binding_symbols']='verified in final zone binary'
(HERE/'build-manifest.json').write_text(json.dumps(man,indent=2)+'\n')
