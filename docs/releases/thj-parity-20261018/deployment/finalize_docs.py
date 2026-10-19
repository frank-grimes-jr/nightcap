"""Record verified deployment and publication; never infer gameplay acceptance."""
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]


def read(p):return p.read_text(encoding='utf-8')
def write(p,s):p.write_text(s,encoding='utf-8')


def main():
    deployed=json.loads(read(HERE/'receipts/deployed.json'))
    hosted=json.loads(read(HERE/'hosted-verification.json'))
    wiki=json.loads(read(HERE/'wiki-public-verification.json'))
    assert deployed['gateway_open'] and hosted['hosted'] and wiki['result']=='PASS'
    status=f'''## Combined THJ item/spell and pet/WPM — deployed October 18, live QA open

Owner-authorized main promotion and OVH activation are complete. PR235 merged
the tested candidate at1039fdd. All12 zone processes and paired world/cache-loader
match the reviewed build; signed client2026101802/proxy0.11.0 verifies all138 files.
Classic level50, existing era/vendor gates and prior travel assets are preserved.
A fresh stopped backup and {deployed['player_tables']} player/{deployed['custom_tables']} custom-table receipts verify
preservation without restoring player state. Ten ordered migrations and matching
caches are installed. World normalized three rule descriptions on first boot;
an exact reviewed forward resume retained all values, content and owned state.
Rule recovery scripts now use compiled descriptions and pass disable/enable/reapply.

The release covers131 observed Ascended targets,1393 changed existing definitions,
modest starter progression, additive direct SD, half-SD ordinary ticks, direct
heroic INT/WIS and the integrated pet/WPM equipment, AA and melee changes.
165 unique regression/migration tests and47 native scenarios remain the gameplay
source evidence; deployment tests and whole-content rehearsal are additional.
WPM shield burst, caster spell-rank/mana choices and pet contribution need owner
testing. Level65/PoP and389 additional merchant entries remain staged.
Wiki20261018-thj-parity-v1 publishes15 updated guides; all465 public files verify.
[Deployment receipts and recovery](releases/thj-parity-20261018/deployment/README.md),
[exact owner QA](releases/thj-parity-20261018/QA.md) and
[measured balance limits](releases/thj-parity-20261018/COMPARISON.md).

'''
    p=ROOT/'docs/status.md';s=read(p);a=s.index('## Combined THJ');b=s.index('## October 18 ordinary loot rates',a)
    write(p,s[:a]+status+s[b:])
    p=ROOT/'CHANGES.md';s=read(p)
    entry='''## 2026-10-18 - Combined THJ release deployed for live testing

Promote the combined item/spell, starter/dungeon and pet/WPM candidate to main
and OVH at the owner's explicit request. Deploy matching world/zone/shared_memory,
ten guarded content components, fresh caches and signed client2026101802 over
all138 current assets. Preserve Classic50, owned items/augments, earned AAs and
saved cooldowns. Publish15 updated wiki guides and verify all465 public files.

The first boot rewrote only three new rule descriptions from its compiled
catalog. Exact review and clone recovery checks allowed a forward resume with
no production SQL replay or player restore. Match generated rule descriptions
to ruletypes.h so disable/enable guards survive world boot. The original hold,
stopped backup and all component receipts remain retained. Never fall back to
the older eight-location pet runtime while new state is owned. Gameplay and
balance acceptance remain open; see docs/releases/thj-parity-20261018/deployment/.

'''
    write(p,s.replace('# CHANGES\n\n','# CHANGES\n\n'+entry,1))
    p=HERE.parent/'README.md';s=read(p)
    s=s.replace('# Combined THJ item/spell, starter and pet/WPM candidate','# Combined THJ item/spell, starter and pet/WPM release',1)
    old='Implemented on `feature/thj-item-spell-parity`, based on `a8e0a913` and the\ncompleted pet/WPM working tree. This is a testing candidate. It is not installed\non production, signed, published, promoted to main or accepted in RoF2.'
    new='Deployed to main and OVH on October18 at the owner’s explicit request.\nPR235 promotes the tested tree; signed client2026101802/proxy0.11.0 and\nwiki20261018-thj-parity-v1 are verified. Classic50 remains active.\n[Deployment and recovery](deployment/README.md) retain the exact receipts,\nincluding the reviewed rule-description startup normalization. Owner RoF2\ngameplay and balance acceptance remain open.'
    assert old in s;s=s.replace(old,new)
    write(p,s)
    p=HERE.parent/'ACTIVATION.md';s=read(p)
    s=s.replace('# Combined candidate preparation and recovery','# Combined release activation and recovery',1)
    a=s.index('No live activation');b=s.index('\n1.',a)
    s=s[:a]+'The owner explicitly authorized main and server promotion on October18. The\nrelease is now installed for live testing; [deployment/README.md](deployment/README.md)\ncontains the guarded execution, first-boot rule-description hold and reviewed\nforward resume. Use its pinned-image entrypoint for this retained recovery.\nThe steps below explain the preparation contract; they are not an instruction\nto replay the completed activation. Owner gameplay acceptance remains open.\n'+s[b:]
    s=s.replace('Repeated application accepts exact afterimages only.','Repeated application accepts exact afterimages only. World rewrites rule notes\n   to compiled descriptions; the corrected rule generators match those notes.\n   A failed CREATE/CALL/DROP sequence can leave a procedure: inspect and\n   authenticate it before any retry; do not blindly replay an uncertain component.')
    s=s.replace('no client signing/publication occurred here.','signed client2026101802 is published; recovery must use a higher counter.')
    write(p,s)
    p=HERE.parent/'QA.md';s=read(p).replace('# Owner testing: combined scaling candidate','# Owner testing: combined deployed scaling release',1)
    s=s.replace('Run against the isolated test candidate with its matching world/zone/cache loader,\ngenerated item/spell caches and NCPA2/proxy0.11.0 client delta.',
        'The combined release is deployed for owner testing. Close EverQuest and reopen\nthe normal launcher for signed game2026101802 and NCPA2/proxy0.11.0. Use a\ndisposable GM character for later-era fixtures; the live era remains Classic50.\nThe same matching binaries and caches are retained for isolated comparisons.')
    write(p,s)
    for name in ('wpm-melee-20261018','thj-pet-scaling-20261018','starter-retune-20261018'):
        p=ROOT/'docs/releases'/name/'README.md';s=read(p);i=s.index('\n')+1
        note='\n**Current status:** This dated component candidate was integrated into the owner-authorized\n[combined THJ release](../thj-parity-20261018/deployment/README.md), deployed October18\nwith signed client2026101802. Its separate level65/PoP profile remains staged.\nUse the combined evidence and QA; older component-only measurements are historical.\n\n'
        write(p,s[:i]+note+s[i:])
    p=HERE/'wiki-review.json';d=json.loads(read(p));d['status']='published_verified';d['release']='20261018-thj-parity-v1';write(p,json.dumps(d,indent=2)+'\n')
    print('Updated status, CHANGES, release/recovery/QA and component boundaries.')


if __name__=='__main__':main()
