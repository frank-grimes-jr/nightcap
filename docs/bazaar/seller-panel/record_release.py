"""Reconcile documentation only after matching runtime, client and public wiki receipts."""
from pathlib import Path
import json,subprocess
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text(encoding='utf8'))
write=lambda p,d:p.write_text(json.dumps(d,indent=2)+'\n',encoding='utf8')
runtime=read(HERE/'deployed.json');client=read(ROOT/'docs/bazaar/private/seller-panel/client-published.json');verified=read(ROOT/'docs/bazaar/private/seller-panel/client-public-verified.json');wiki=read(HERE/'deployment/wiki-public-verification.json')
assert runtime['gateway_open'] and not runtime['owner_gameplay_accepted']
assert client['release']==verified['release']==2026102601 and verified['hosted'] and verified['managed_files']==141
assert wiki['result']=='PASS' and wiki['files']==499
main=subprocess.check_output(['git','rev-parse','origin/main'],cwd=ROOT,text=True).strip()
e=read(HERE/'evidence.json');e.update(status='Deployed on main for live QA; paired client/wiki verified; owner gameplay acceptance open',deployment=True,main_revision=main)
e['client'].update(status='Signed2026102601 published; all141HTTPSassets/signature/pairing verified',published=True)
e['remaining']=['Owner native gameplay/visual/balance QA for Bazaar and Paladin grips']
e['checks']['wiki']='19 content/refresh tests and16Linux publication tests PASS; all499HTTPSfiles/hash/securityheaders and5private-route denials verified'
e['publication']={'client_release':2026102601,'wiki_release':wiki['release'],'zone_workers':sum(p[0]=='zone' for p in runtime['runtime']['processes']),'checks':runtime['checks'],'state_tables':runtime['state_tables']}
write(HERE/'evidence.json',e)
write(HERE/'client/published.json',{k:client[k] for k in ['release','channel_sha256','changed_assets','preserved_assets','desktop_starter_guide_unchanged']})
write(HERE/'client/public-verification.json',verified)
c=read(HERE/'deployment/coordination.json');c.update(production_writes=True,status='One combined main/server/client/wiki release completed; owner QA open',main_revision=main);write(HERE/'deployment/coordination.json',c)
w=read(HERE/'wiki-review.json');w.update(published=True,status='Combined publication and all499publicfiles verified; owner gameplay acceptance open',public_release=wiki['release']);w.pop('public_release_unchanged',None)
w['built_delta']['published']=True;w['built_delta']['status']='Published and verified';w['package']['status']='Published and verified';write(HERE/'wiki-review.json',w)
for name in ['tunnel','commands','features','recent-changes','ascension','equipment','item-upgrades','unreleased']:
 p=ROOT/'wiki/articles'/(name+'.json');d=read(p)
 d['sources']=[s for s in d.get('sources',[]) if 'docs/bazaar/seller-panel/' not in s and 'docs/items/paladin-weapon-grip/' not in s]
 d['sources'].append('docs/bazaar/seller-panel/deployed.json, evidence.json and deployment/wiki-public-verification.json; combined October26 main/runtime/client2026102601/wiki release verified, native owner acceptance open')
 write(p,d)
p=ROOT/'docs/status.md';s=p.read_text(encoding='utf8');a=s.index('## 2026-10-26');b=s.index('## 2026-10-26 — Commonlands bazaar deployed',a)
s=s[:a]+"""## 2026-10-26 — Bazaar seller panel and Paladin grips deployed for live QA

Owner-authorized main PR345/e43f2d4b and one combined runtime release are verified.
All12zone workers and matching world/shared_memory run the integrated candidate;
51schema/565content checks, fresh stopped backup and102saved-state tables including
all5Bazaar tables pass. Gateway reopened; quests, cache, content and other services
are preserved. Signed client2026102601 publishes the Sell / My Listings tab and
all141assets verify. Wiki20261026-bazaar-grip-v1 verifies all499files.

Post, cancel and collect with the Bazaar buttons after exiting EQ and using launcher
Play. SoulFire, Fiery Avenger and Fiery Defender also gain right-click1HS/2HS grips,
replacing SoulFire's heal click. Retain grip-aware binaries for forward recovery;
never restore old player data. Native rendering, offline buying and weapon-grip
behavior/balance are still owner QA gates. [Release evidence](bazaar/seller-panel/evidence.json),
[Bazaar steps](bazaar/seller-panel/QA.md), [weapon steps](items/paladin-weapon-grip/QA.md).

"""+s[b:];p.write_text(s,encoding='utf8')
p=ROOT/'CHANGES.md';s=p.read_text(encoding='utf8').replace('Bazaar seller panel candidate (not deployed)','Bazaar seller panel deployed for live QA').replace('Paladin weapon grip candidate','Paladin weapon grips deployed for live QA')
s=s.replace('power changes. [Candidate and QA]','power changes. Combined main PR345, matching world/zone/shared_memory and signed\nclient2026102601 are deployed. All499wiki files verified; owner gameplay QA remains open.\n[Release and QA]')
s=s.replace('only; no production installation or wiki publication.','included in the coordinated Bazaar main/server/client/wiki release. Owner native\ngameplay and balance acceptance remain open.')
s=s.replace('No content/cache/client migration. Candidate\nincluded','No content/cache migration. Weapon code is\nincluded');p.write_text(s,encoding='utf8')
p=HERE/'QA.md';s=p.read_text(encoding='utf8');a=s.index('Candidate only.');b=s.index('## Main offline-seller test',a);s=s[:a]+'Deployed for live QA with signed client2026102601 and the integrated server binaries.\nFully exit EQ and use launcher Play before testing. These are acceptance steps,\nnot completed owner observations.\n\n'+s[b:];p.write_text(s,encoding='utf8')
p=HERE/'README.md';s=p.read_text(encoding='utf8');s=s.replace('signed local2026102601 candidate; publication awaits verified integrated runtime.','signed2026102601 is published and all141HTTPSassets/signature/pairing verify.')
s=s.replace('# Bazaar seller panel candidate','# Bazaar seller panel — live QA');s=s.replace('Candidate only; not deployed or owner accepted.','Deployed for live QA; owner gameplay acceptance remains open.')
s=''.join([s.split('\n',1)[0],'\n\nMain PR345/e43f2d4b and the paired runtime/client/wiki release are verified.\nAll12workers,51schema/565content checks and102saved-state tables pass; access is open.\nSigned client2026102601 and wiki20261026-bazaar-grip-v1 are published.\nNative player acceptance remains open. See deployed.json and evidence.json.\n',s.split('\n',1)[1]])
p.write_text(s,encoding='utf8')
p=ROOT/'docs/items/paladin-weapon-grip/README.md';s=p.read_text(encoding='utf8').replace('# Paladin weapon grip — October 26 candidate','# Paladin weapon grip — October26 live QA').replace('Not deployed or accepted in the game. Wiki edits are an unpublished candidate.','Integrated main PR345/e43f2d4b and the combined Bazaar runtime/client/wiki release\nare verified in docs/bazaar/seller-panel/deployed.json and evidence.json. Owner\nnative gameplay and balance acceptance remain open.').replace('This candidate has performed no production writes.','The combined release is deployed; no separate weapon runtime installation occurred.')
p.write_text(s,encoding='utf8')
p=ROOT/'docs/items/paladin-weapon-grip/QA.md';s=p.read_text(encoding='utf8').replace('Use a candidate test server with matching native binaries and current signed','Use the deployed live QA server with matching native binaries and signed2026102601');p.write_text(s,encoding='utf8')
p=ROOT/'docs/milestones/phase-77-report.md';assert not p.exists();p.write_text("""# Phase77: Bazaar seller controls and coordinated Paladin grips

Built a native Bazaar Sell / My Listings tab with confirmed posting/cancellation,
owned listing pages and offline proceeds collection. Integrated Paladin grip code
from the coordinated chat, preserving item metadata through Bazaar escrow.
Main PR343→344→345 and one runtime restart deliver both changes. Paired signed\nclient2026102601 and wiki20261026-bazaar-grip-v1 are verified.

Validation: integrated fullworld/zone/shared_memory build;26realMariaDB Bazaar
cases,4native Bazaar groups including40grip transfer flows;4weapon groups and39SQL
cases;10x86runtime groups,115exact guards, actual DLL/catalog pairing, signed141asset
inventory;21Linux rollout,17Linux publisher and4ELF identity cases;499wiki HTTPSfiles.
Fresh stopped backup and102saved-state tables preserved. No schema/content/cache
migration. An exact unmounted previous Bazaar staging executable was losslessly
archived with decompressed-hash proof; active images and DBbackups were preserved.

No requested controls were cut. Native rendering, focus/skin reload, offline buying,
collection/cancellation and weapon combat/balance acceptance remain unverified by
the owner. Follow docs/bazaar/seller-panel/QA.md and docs/items/paladin-weapon-grip/QA.md.
Recovery must retain grip-aware binaries and earned data; never replay uncertainty.
""",encoding='utf8')
print('Recorded combined runtime/client/wiki publication; owner acceptance remains open')
