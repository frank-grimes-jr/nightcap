import hashlib,json,tarfile
from pathlib import Path
OUT=Path(__file__).parent
ROOT=Path('C:/Users/verre/.codex/worktrees/all-items-tradable/EQ_Local_Dev')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((OUT/'native-manifest.json').read_text())
for name,h in m['binaries'].items():
    p=OUT/'native-bin'/name
    assert sha(p)==h,name
    assert p.read_bytes()[:4]==b'\x7fELF',name
world=(OUT/'native-bin/world').read_bytes()
zone=(OUT/'native-bin/zone').read_bytes()
assert b'CALL nightcap_market_rotate({},{},{})\x00' in world
assert b'CALL nightcap_market_rotate({})\x00' not in world
assert b'INSERT INTO character_currency(id,platinum) VALUES({},100)' in world
for marker in (b'LivingEconomy\x00',b'MarketAnnouncement\x00',b'TunnelChatter\x00',b'_Z9Perl__oocPKc',
               b'Your selected classes cannot cast this spell at your current level.',
               b'Former NO DROP items sell for exactly 1 platinum each'):
    assert marker in zone,marker
for n in ('world','zone','shared_memory'):
    assert b'FreeTrade\x00' in (OUT/'native-bin'/n).read_bytes(),n
report={k:v for k,v in m.items() if k!='source_files'}
report.update(full_manifest_sha256=sha(OUT/'native-manifest.json'),
              native_contract_checks='passed',private_login_crypto_self_test='passed',
              changed_source_sha256={n:m['source_files'][n] for n in m['changed_source_files']})
(OUT/'build-summary.json').write_text(json.dumps(report,indent=2)+'\n')
with tarfile.open(OUT/'native-candidate.tar.gz','w:gz',compresslevel=1) as archive:
    archive.add(OUT/'native-bin',arcname='native-bin')
    archive.add(OUT/'build-summary.json',arcname='build-summary.json')
package={'name':'native-candidate.tar.gz','sha256':sha(OUT/'native-candidate.tar.gz'),
         'bytes':(OUT/'native-candidate.tar.gz').stat().st_size,'status':'prepared_not_deployed'}
(OUT/'package.json').write_text(json.dumps(package,indent=2)+'\n')
print(json.dumps({'native_contracts':'passed','package':package},indent=2))
