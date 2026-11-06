"""Record verified augment visibility release; install only after all receipts exist."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
SKILL=Path('C:/Users/verre/.codex/skills/nightcap-development/references')


def section(text,heading,replacement):
    start=text.index(heading);end=text.index('\n## ',start+len(heading))
    return text[:start]+replacement.rstrip()+'\n'+text[end:]


def main(apply):
    deployed=json.loads((HERE/'deployed.json').read_text())
    client=json.loads((HERE/'client-public-verification.json').read_text())
    wiki=json.loads((HERE/'wiki-publication.json').read_text())
    assert deployed['gateway_open'] and deployed['command_access']==0 and not deployed['cache_changed']
    assert client['release']==2026110601 and client['hosted'] and client['changed_assets']==2
    assert wiki['result']=='PASS' and wiki['files']==510
    old={n:(SKILL/n).read_text(encoding='utf-8') for n in ('items.md','operations.md','client.md','wiki.md','sources.json')}
    new=dict(old)
    text='''## Augment visibility and equipped totals — November6 deployed for live QA

Source E:/EQ_Local_Dev/_worktrees/augment-item-window; main PR408/3343d6c8.
docs/releases/augment-item-window-20261106/ owns native/signature/HTTPS/runtime
receipts and QA. Owner reported hidden Understone Shield Block and unchanged
Shielding during augment live QA. Shield Block is a shield-gated nominal chance
to block; Shielding reduces melee damage separately. Item power/stacking unchanged.

Client0.13.3/signed2026110601 puts the property in native item Description for the
nine qualifying Hunt augment definitions: Polished/Exalted+1%, Ascension+2%; three
families, strongest Hunt only, eligible worn socket plus usable shield required.
Lore is not normal Description: DB lore text alone is not visible QA evidence.
The guarded CItemDisplayWnd::UpdateStrings hook (RVA29ae30) annotates ItemInfo0x294
before native rendering, snapshot-bounded16KiB, idempotent across refresh/reuse.
Description0x220/ItemPtr0x2b0 and native definitionID0xec are pinned. Uses the same
common/zone_hunt_policy.h helper as the server. Future ID/value tuning needs
matching presentation policy, not just changing lore. Names/spells remain native.

Player #augstats is self-only/read-only: actual equipped Shield Block, active
strongest Hunt contribution, item/spell/AA components, Shielding, Spell Shielding,
Avoidance, Accuracy, damage/healing totals plus live caps/headroom, relative Dodge
modifier and stacking guidance. Native stock250healing label is not server truth;
current750base caps and up30earned headroom remain. Numeric copies add within
caps; duplicate Hunt block/focus/Improved Dodge I/Faerune effects do not multiply.
Focus limits still depend on the cast spell. Bagged/training items give no stats.

Tests: actual native Description RED then25GREEN assertions,22client runtime/native
groups,120exact-client guards, Go preflight/manifest/runtimehealth,2report/7augment
regressions,4Linux rollout/20client recovery tests,15wiki plus3public-scope/link tests.
Native report build first reproduces bc88a468 from144authenticated inputs, then
changes only the command unity unit. No item/cache/rule/schema/player migration;
native boot adds only player-access augstats settings. All other command rows,
world/shared_memory, metadata compatibility, cached definitions and saved state
preserved. Stopped backup and supported whole-runtime restart verified. Never
restore old player snapshots or replay a completed activation.

Signed DLL/catalog only:146other assets/URLs retained; all148HTTPS/signature/pair
checks pass. Fully EXIT EQ and use normal launcher Play; relog alone cannot load a
new DLL. No protected reference-client writes. Owner native visual/gameplay QA
remains open. Current AlwaysTake preferences plus durable loot receipts establish
configuration/collection, but receipts do not separately log automatic/manual mode.
Context topic augment-display pins this reviewed source and verified evidence.
'''
    marker='## Zone augment audit — November6 deployed for live QA'
    new['items.md']=old['items.md'].replace(marker,text+'\n'+marker,1)
    new['operations.md']=section(old['operations.md'],'## Current native baseline — November6 augments deployed for live QA',f'''## Current native baseline — November6 augment Description/report follow-up

Main PR408/3343d6c8 is deployed for owner live QA. Evidence/worktree:
E:/EQ_Local_Dev/_worktrees/augment-item-window,
docs/releases/augment-item-window-20261106/{{deployed.json,native-build.json,README.md}}.
Zone3fc2b901c98dfc2816298a051f3462a6db0a724ccfa649ff213da3d840186588;
runtime image {deployed['runtime']['image_id']}. Gateway reopened after verified
stopped backup, exact content/rules/cache/native identities, saved-state boot
model and expected market rotation. Only player-access augstats command row added;
all other command rows retained. No player snapshot restored. Worldf33c5925 and
shared_memory569394cf remain compatible; no rule/ItemData/schema or item changes.

Retained source/build /tmp/nightcap-augment-item-window-20261106-v4 in local
akk-stack-eqemu-server-1. It first reproduces live augmentbc88a468 byte-for-byte
from144authenticated link inputs, then rebuilds unity_1_cxx.cxx containing both
command.cpp registration and gm_commands/nightcapui.cpp. Do not assume standalone
command.cpp.o is a link input; preserve the other11command archive members.
Includes prior Power Source metadata, SSF, Hunt rates, placeholder-loot repair and
live Hate spawn-source join. Do not rebuild from the older selective/default mirror.

Signed client0.13.3/2026110601 DLL+catalog is published and all148assets verified.
Old client can use #augstats; new Description requires full EQ exit/launcher Play.
Native visual/gameplay acceptance remains open. Current full-runtime child-exit
supervision remains: never refresh OVH by killing one zone. Reuse immutable job
receipts, not activation replay; after opening use fresh compatible forward repair.
''')
    client_text='''## Hunt augment descriptions — November6 signed client published; native QA open

Main PR408/3343d6c8; worktree E:/EQ_Local_Dev/_worktrees/augment-item-window.
Signed2026110601/proxy0.13.3 replaces DLL/catalog only, preserving146assets/URLs,
history/tombstones/config, cast-bar spell repair and recall strings. All148HTTPS
bytes/shipped-key signature and proxy/catalog pairing verify. No desktop/starter
or protected-reference-client changes. Fully EXIT EQ/use launcher Play.

eq-client-dll/src/{augment_item_description.h,ui_hooks.h} adds explicit Hunt
Shield Block, worn-socket/shield requirements and strongest-only rule to normal
Description. Existing item names/spells/bonuses unchanged. Native regression runs
the pinned UpdateStrings renderer; 25assertions plus22runtime/native groups pass.
120catalog sites bind the new6-byte entry instruction and layout reads. The hook
is required by existing class_ui startup success; failure cannot silently launch.
Local NOMINMAX plus scoped min/max preservation allows the shared server policy
header under Windows. Report command #augstats is available from paired zone3fc2b901.
All implementation/QA/recovery evidence: docs/releases/augment-item-window-20261106/.
Pixels, skin sizing, chat-link/socket views and owner visible acceptance remain
live QA; isolated renderer text/signature verification is not visible acceptance.
'''
    first=old['client.md'].index('\n## ')
    new['client.md']=old['client.md'][:first]+'\n\n'+client_text+old['client.md'][first:]
    new['wiki.md']=section(old['wiki.md'],'## Zone augment audit — November6 published for live QA','''## Zone augment audit — November6 published; Description follow-up live QA

Current public release20261106-augment-description-v1 replaces20261106-augment-audit-v2.
All510files/503HTML routes, HTTPS/private-download guards, rollback rehearsal and
unchanged service image/start identities verify. Five owning guides/Features/Change
Log update Description/Shield Block versus Shielding, #augstats and stacking.
Home/navigation, all item/zone/catalog data, Build Lab models/spells and assets
unchanged. Full58family list and50Classic/392variants/98families remain; CT/Hate B
augment-only, six dormant pools excluded. Artwork accepted; new UI/gameplay QA open.

Evidence in E:/EQ_Local_Dev/_worktrees/augment-item-window:
docs/releases/augment-item-window-20261106/{wiki-publication.json,wiki-baseline.json,
wiki-impact.json,test_release_content.py,published-source-overrides.patch}.
The exact prior public source is retained/reproduced before scoped edits. Main
keeps unrelated source-only previews; use recorded overrides for actual publication
source and never blindly publish a selective main mirror. Historical global
source drift stays REVIEW REQUIRED; no blanket ledger advancement. The signed
client0.13.3/2026110601 and report-only zone3fc2b901 are independently verified;
published labels are Live testing, not completed native visual/gameplay acceptance.
''')
    manifest=json.loads(old['sources.json'])
    revision='3343d6c8bb9c2d1c66de3e68c1c01309479838f6 plus reviewed verified release records'
    paths=['eq-client-dll/src/augment_item_description.h','eq-client-dll/src/ui_hooks.h','eq-client-dll/src/dllmain.cpp',
           'eq-client-dll/config/patch-sites.json','eq-client-dll/tests/augment-item-window.cpp','tools/generate-client-patch-catalog.py',
           'server-mods/code/zone/command.cpp','server-mods/code/zone/command.h','server-mods/code/zone/gm_commands/nightcapui.cpp',
           'tools/tests/test_augment_stats.py']
    paths+=['docs/releases/augment-item-window-20261106/'+n for n in ['README.md','native-build.json','client-tests.json',
           'rollout.py','deployed.json','client-public-verification.json','client-published.json','wiki-publication.json',
           'wiki-impact.json','test_release_content.py','published-source-overrides.patch']]
    entries=[dict(root=ROOT.as_posix(),path=p,role='Reviewed November6 augment Description/report release; native visual/gameplay QA open',revision=revision,
                  sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()) for p in paths]
    manifest['topics']['augment-display']=entries
    manifest['observed_revisions']['augment_description_20261106_deployed']=revision
    for topic in ('items','operations','client','wiki'):
        manifest['topics'][topic]+=[e for e in entries if e['path'].startswith('docs/releases/') and e['path'].endswith(('README.md','deployed.json','client-public-verification.json','wiki-publication.json'))]
    new['sources.json']=json.dumps(manifest,indent=2)+'\n'
    patch=''.join(''.join(difflib.unified_diff(old[n].splitlines(True),new[n].splitlines(True),fromfile='a/references/'+n,tofile='b/references/'+n)) for n in new)
    (HERE/'installed-skill-update.patch').write_text(patch,encoding='utf-8')
    if apply:
        for n,text in new.items():(SKILL/n).write_text(text,encoding='utf-8',newline='\n')
    (HERE/'skill-maintenance.json').write_text(json.dumps({'status':'applied' if apply else 'prepared','reviewed_entries':len(entries),'revision':revision},indent=2)+'\n')
    print('Applied' if apply else 'Prepared',len(entries),'reviewed deployed-state fingerprints')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');main(p.parse_args().apply)
