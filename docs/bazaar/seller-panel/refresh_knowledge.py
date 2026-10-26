"""Maintain the installed Nightcap references for this reviewed candidate only."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[3]
SKILL=Path('C:/Users/verre/.codex/skills/nightcap-development')
REF=SKILL/'references'
revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
evidence=json.loads((ROOT/'docs/bazaar/seller-panel/evidence.json').read_text())
state='Full integrated zone/world/shared_memory build passed.' if evidence.get('integrated_build',{}).get('status')=='PASS' else 'Integrated build and authorized deployment remain in progress.'
blocks={
'items':"""## Bazaar seller panel — October26 unpublished candidate

Source: managed commonlands-bazaar checkout, feature/bazaar-seller-panel.
Sell / My Listings adds cursor price/preview/Confirm Post, eight owned rows/page,
confirmed cancellation and proceeds collection. Existing escrow ownership, exact
metadata, offline credits and disabled-trading recovery remain. No schema or item
power changes. PrepareBazaarPost/ConfirmBazaarPost are shared with command fallback;
ReadSeller uses a coherent owner-only read under the escrow lock and ends ROLLBACK.
Uncertain rollback quarantines; incomplete snapshots never enable actions.

Source: common/bazaar_panel_{protocol,query}.h, zone/client_bazaar.cpp/client.h;
26disposable MariaDB cases and4production native guard groups pass, including
current weapon-grip restore and40buy/cancel metadata cases. Pair integrated world/zone/shared_memory with proxy/catalog0.13.0, config and Bazaar XML. Graceful whole-runtime restart
is required on OVH; never kill one zone, drop escrow or restore old player data.
Earlier command-only deployment/approval remains scoped to zone84b6b9ff.
""",
'client':"""## Bazaar Sell / My Listings — October26 unpublished candidate

Source: managed commonlands-bazaar checkout, feature/bazaar-seller-panel. Native
Bazaar Search is the first TabBox page; seller controls occupy the second. Keep all
stock controls/names and recursive child lookup. Specific Bazaar notify/frame/
deleting-destructor slots are HIGHLOW relocations; preserve stock frame once and
its return/destructor flags. Do not trampoline the relative-CALL frame prologue.
Price notifications must be consumed: native message14 updates Search without a
sender check. Enter never submits. Re-resolve children and recheck identity on click.

NCBZ1 counted snapshots correlate character/request,8rows/page,100maximum.
Client waits for complete authoritative replies; quote/cancel confirmation is local
presentation, with server ownership decisive. Timeout permits read refresh only.
300ms send/reply cooldown exceeds the250ms server gate; initial-view pending retry
handles fast tab switches. Close/zone/character/UI teardown invalidates selections.

Source: eq-client-dll/src/bazaar_panel_{state,controller,hooks}.h, ui_hooks.h,
tools/client_bazaar_ui.py and generated contracts.10x86runtime groups,115exact
client guards,3XML cases,288native animation cases and invisible regression pass.
Actual signed baseline2026102402 preserves137assets/history; candidate141inventory
changes proxy/catalog/config and adds Bazaar XML. Signed2026102601 candidate is locally verified but unpublished;
protected reference and installed player clients remain untouched. No launcher build.

Actual candidate pairing caught a linker-layout bug: hash text followed a pointer,
so its implicit leading NUL was absent. Generated identity structs now supply an
explicit zero boundary; keep strict CheckProxyCatalog. Actual rebuilt0.13.0DLL and
both runtime pairs pass TestBazaarPanelCandidate; mixed pair fails. A signature or
source catalog alone is insufficient. Native visual/focus/resize/skin-reload and
end-to-end search/offline purchase still require player QA.
""",
'wiki':"""## Bazaar seller panel — October26 unpublished wiki overlay

Source: managed commonlands-bazaar checkout, feature/bazaar-seller-panel. Entire
40article-source wiki and generated catalogs/Home/Features/commands/release labels
reviewed. Eight articles prepare combined Bazaar and Paladin grip live-testing guidance;
publish only after verified runtime/client receipts. Built499files changes nine
files, preserving490exact files with no additions/removals.
No item/reward/acquisition or Home changes.19content/refresh tests pass.

Current public release remains20261026-commonlands-bazaar-v1. This candidate wiki
is not published. CurrentHEAD plus worktree check_refresh retains REVIEW REQUIRED
for the historical global ledger; reviewed scoped evidence does not authorize blind
advancement. Reconcile any later public/source changes before authorized publication.
"""}
common='\n'+state+' Evidence and exact QA: docs/bazaar/seller-panel/{README.md,QA.md,evidence.json}.\nOwner October26 instruction authorizes the coordinated main/server/client/wiki release;\nweapon chat holds writes while this chat owns deployment. Native player acceptance remains open.\n'
for topic,block in blocks.items():
 p=REF/(topic+'.md');text=p.read_text(encoding='utf8');heading=block.split('\n')[0]
 if heading in text:
  start=text.index(heading);end=text.find('\n## ',start+len(heading));text=text[:start]+text[end+1:] if end>=0 else text[:start]
 first=text.find('\n')+1;text=text[:first]+'\n'+block+common+'\n'+text[first:].lstrip('\n');p.write_text(text,encoding='utf8')
paths={
'items':['server-mods/code/common/bazaar_panel_protocol.h','server-mods/code/common/bazaar_panel_query.h','server-mods/code/zone/client_bazaar.cpp','server-mods/code/zone/client.h','tools/tests/test_bazaar_escrow.py','tools/tests/test_bazaar_native.py','tools/build_bazaar_panel_candidate.py'],
'client':['eq-client-dll/src/bazaar_panel_state.h','eq-client-dll/src/bazaar_panel_controller.h','eq-client-dll/src/bazaar_panel_hooks.h','eq-client-dll/src/ui_hooks.h','eq-client-dll/src/dllmain.cpp','eq-client-dll/config/patch-sites.json','eq-client-dll/config/nightcap-patches.cfg','eq-client-dll/src/runtime_contract.h','eq-client-dll/tests/bazaar-panel.cpp','eq-client-dll/tests/bazaar-panel-native.cpp','eq-client-dll/tests/test_runtime.py','tools/client_bazaar_ui.py','tools/client_gameplay_assets.py','tools/generate-client-patch-catalog.py','tools/tests/test_client_bazaar_ui.py','eq-launcher/internal/preflight/bazaar_panel_candidate_test.go'],
'wiki':['wiki/articles/tunnel.json','wiki/articles/commands.json','wiki/articles/features.json','wiki/articles/recent-changes.json','docs/bazaar/seller-panel/wiki-review.json']}
manifest_path=REF/'sources.json';manifest=json.loads(manifest_path.read_text(encoding='utf8'));scoped={'audited_at':'2026-10-26','topics':{}}
for topic,names in paths.items():
 names+=['docs/bazaar/seller-panel/README.md','docs/bazaar/seller-panel/QA.md','docs/bazaar/seller-panel/evidence.json']
 manifest['topics'][topic]=[e for e in manifest['topics'][topic] if e['path'] not in names]
 entries=[{'root':ROOT.as_posix(),'path':name,'role':'Reviewed combined Bazaar/weapon QA release; authorized deployment in progress, native acceptance pending','revision':revision+' plus reviewed candidate evidence','sha256':hashlib.sha256((ROOT/name).read_bytes()).hexdigest()} for name in names]
 manifest['topics'][topic]+=entries;scoped['topics'][topic]=entries
manifest['observed_revisions']['bazaar_panel_candidate_20261026']=revision+'; unpublished candidate; '+state
manifest_path.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')
(ROOT/'docs/bazaar/private/seller-panel/reviewed-sources.json').write_text(json.dumps(scoped,indent=2)+'\n')
print('Updated items/client/wiki references and',sum(map(len,scoped['topics'].values())),'reviewed fingerprints')
