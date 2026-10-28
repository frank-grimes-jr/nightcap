"""Read-only verification of the already-deployed High Keep rescue. No rollout actions."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
NATIVE = ['common/highkeep_policy.h', 'zone/highkeep_rescue.inc', 'zone/dungeon_service.cpp',
          'zone/dungeon_service.h', 'zone/aggro.cpp', 'zone/attack.cpp', 'zone/client.cpp',
          'zone/npc.cpp', 'zone/spells.cpp']


def main():
    if not __debug__:
        raise RuntimeError('Verification requires assertions; do not use optimized Python')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists(), 'Preserve prior verification; choose a new receipt'
    private = args.release_root / 'docs/bazaar/private/seller-panel'
    build_path = private / 'integrated-build.json'
    identity_path = private / 'runtime-identity.json'
    build = json.loads(build_path.read_text())
    identity = json.loads(identity_path.read_text())
    if set(identity) != {'zone', 'world', 'shared_memory'}:
        raise ValueError('Require the complete zone/world/shared_memory runtime identity proof')
    pins = {}
    for name in NATIVE:
        digest = hashlib.sha256((ROOT / 'server-mods/code' / name).read_bytes().replace(b'\r\n', b'\n')).hexdigest()
        assert build['source_files'][name] == digest, name
        pins[name] = digest
    for name, proof in identity.items():
        assert proof['status'] == 'PASS' and proof['original_sha256'] == build['binaries'][name], name
    expected = {name: proof['sha256'] for name, proof in identity.items()}
    operator_hash = hashlib.sha256((ROOT / 'docs/bazaar/seller-panel/deployment/rollout.py').read_bytes().replace(b'\r\n', b'\n')).hexdigest()
    spec = importlib.util.spec_from_file_location('configured_ssh', ROOT / 'docs/quests/camil-chapterhouse/deployment/remote.py')
    configured = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(configured)
    code = r'''
import contextlib,datetime,hashlib,importlib.util,json,os,sys
from pathlib import Path
if not __debug__:
 raise RuntimeError('Remote verification requires assertions')
stage=Path('/opt/nightcap/releases/bazaar-grip-20261026')
operator=stage/'rollout.py'
assert hashlib.sha256(operator.read_bytes().replace(b'\r\n',b'\n')).hexdigest()==EXPECTED_OPERATOR
spec=importlib.util.spec_from_file_location('verified_release',operator)
op=importlib.util.module_from_spec(spec);spec.loader.exec_module(op)
with contextlib.redirect_stdout(sys.stderr):
 op.initialize();m=op.manifest();r=op.r
 deployed=op.read(op.EVIDENCE/'activation/deployed.json')
 assert deployed['gateway_open'] and not deployed['database_restored']
 assert m['runtime_identity']==EXPECTED_IDENTITY,'Retained runtime proof drift'
 for name,digest in EXPECTED_BINARIES.items():assert m['candidate_hashes']['bin/'+name]==digest,name
 before={name:r.compact(name) for name in ('game','gateway','db','web','tunnel')}
 current=r.running(deployed['runtime']['image_id'],op.binaries())
 op.base.health();r.closed_ports()
 assert before['gateway']['running']
 flag=op.sql('SELECT id,revision,enabled FROM nightcap_highkeep_state;').strip()
 assert flag=='1\t2026102401\t1',flag
 engines=op.sql("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE() AND engine='InnoDB' AND table_name IN ('nightcap_highkeep_state','nightcap_highkeep_runs');").strip()
 triggers=op.sql("SELECT COUNT(*) FROM information_schema.triggers WHERE trigger_schema=DATABASE() AND event_object_table IN ('nightcap_highkeep_state','nightcap_highkeep_runs');").strip()
 assert engines=='2' and triggers=='0'
 columns=op.sql("SELECT table_name,GROUP_CONCAT(CONCAT(column_name,':',data_type,':',is_nullable) ORDER BY ordinal_position SEPARATOR ',') FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name IN ('nightcap_highkeep_state','nightcap_highkeep_runs') GROUP BY table_name;").strip().splitlines()
 assert set(columns)=={'nightcap_highkeep_state\tid:tinyint:NO,revision:bigint:NO,enabled:tinyint:NO','nightcap_highkeep_runs\trun_id:char:NO,alarm:tinyint:NO,rescued_at:bigint:NO'}
 for table,key in [('nightcap_highkeep_state','id'),('nightcap_highkeep_runs','run_id')]:
  index=op.sql("SELECT GROUP_CONCAT(CONCAT(index_name,':',column_name) ORDER BY index_name,seq_in_index) FROM information_schema.statistics WHERE table_schema=DATABASE() AND table_name='"+table+"';").strip()
  assert index=='PRIMARY:'+key
 assert op.sql("SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='nightcap_highkeep_runs' AND column_name='run_id' AND character_maximum_length=36 AND character_set_name='ascii' AND collation_name='ascii_bin';").strip()=='1'
 counts=[int(x) for x in op.sql('SELECT COUNT(*),COALESCE(SUM(alarm=1),0),COALESCE(SUM(rescued_at>0),0) FROM nightcap_highkeep_runs;').strip().split('\t')]
 maps={}
 for rel,expected in [('base/highkeep.map','0640d5c11de83e128facb5b77331bf599b3d495e66974d22d8396527f9562a4b'),('nav/highkeep.nav','f88eb95d03722bd50e974fbbac9b8b0146a71c8bc678511ae0087f90520f702a')]:
  digest=hashlib.sha256((op.ROOT/'data/server/maps'/rel).read_bytes()).hexdigest();assert digest==expected,rel;maps[rel]=digest
 wiki=os.readlink(op.ROOT/'data/public/wiki/current')
 after={name:r.compact(name) for name in before}
 assert before==after,'Service identity changed during read-only check'
 result={'result':'PASS','verified_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
  'runtime':current,'rescue_revision':2026102401,'rescue_enabled':True,'schema_checks':'exact native loader requirements passed',
  'run_counts':dict(zip(('enrolled','alarmed','rescued'),counts)),'maps':maps,'wiki_pointer':wiki,
  'gateway_open':True,'service_lifetimes_preserved':True,'production_changed':False,'owner_gameplay_accepted':False}
print(json.dumps(result))
'''.replace('EXPECTED_OPERATOR', repr(operator_hash)).replace('EXPECTED_BINARIES', repr(expected)).replace('EXPECTED_IDENTITY', repr(identity))
    result = subprocess.run(list(configured.SSH) + ['sudo -n python3 -B -'], input=code, text=True,
                            capture_output=True, timeout=180)
    if result.returncode:
        raise RuntimeError('Read-only live verification failed: ' + result.stderr[-3000:])
    receipt = json.loads(result.stdout)
    receipt.update(reviewed_source_files=pins, build_manifest_sha256=hashlib.sha256(build_path.read_bytes()).hexdigest(),
                   runtime_identity_sha256=hashlib.sha256(identity_path.read_bytes()).hexdigest(),
                   source_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(receipt, stream, indent=2); stream.write('\n')
    print(json.dumps({k:receipt[k] for k in ('result','verified_at','rescue_enabled','run_counts','wiki_pointer','gateway_open','production_changed')}))


if __name__ == '__main__':
    main()
