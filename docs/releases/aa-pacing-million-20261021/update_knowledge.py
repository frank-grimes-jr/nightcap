"""Apply reviewed installed knowledge only after verified deployment/publication."""
from pathlib import Path
import difflib,hashlib,json,subprocess
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
SKILL=Path('C:/Users/verre/.codex/skills/nightcap-development')
ART=Path('E:/EQ_Local_Dev/artifacts/aa-pacing-million-20261021')
def replace_section(text,title,replacement):
    a=text.index(title);b=text.find('\n## ',a+len(title))
    return text[:a]+replacement.rstrip()+'\n'+(text[b:] if b>=0 else '')
def main():
    deployed=json.loads((HERE/'deployed.json').read_text())
    assert deployed['gateway_open'] and not deployed['database_restored']
    assert json.loads((HERE/'wiki-public-verification.json').read_text())['result']=='PASS'
    assert json.loads((HERE/'guide-public-verification.json').read_text())['result']=='PASS'
    source='C:/Users/verre/.codex/worktrees/aa-point-cost-40000/EQ_Local_Dev'
    release='docs/releases/aa-pacing-million-20261021/'
    xp="""## XP
OVH uses **1,000,000 XP per AA and 10% passive earning**, owner-authorized and
deployed October 21, 2026 (EDT), main PR268/e64f502. This replaces the earlier
same-day 40,000-point trial. Earned points, purchases and raw partial XP remain;
2,000 XP now represents 0.2% of a point. The rule change leaves raw awards and
normal XP alone; retiring Goldwind's +50% package separately removes its boost.

At level38, unboosted Mistmoore35-37 dark blues model25,081-28,030 passive AA XP
per kill, about36-40 kills/point or about4 with full focus. Level50 Hole47-49
dark blues model12-13 passive kills. Corrected continuous normal-level1-50
model includes per-level AA/normal modifiers:19,740,195 AA XP, about19.7 points
at1m (493.5 at40k, correcting the earlier simplified412 estimate). These are
conditional models, not measured player trajectories. Carry, quests, group/
con/zone/level modifiers, focus and rounding matter.

No verified THJ raw XP/point constant was discovered. Archived forum posts357/
387 report level60 ChardokB percentages and an XP-buff drop from16% to9% on
yellow kills. Nightcap counterpart mob277022 yields2,095,154 focused AA XP;
dividing by9% gives a conditional23.28m equivalent, not a THJ rule or suitable
low-level target. Level51 Veksar40-45AA/hour lacks kill counts. Research source/
assumptions remain in E:/EQ_Local_Dev/artifacts/aa-thj-rate-inference-20261021/
and aa-pacing-options-20261021/. The reported one-AA dark blue was compatible
with the previous40k threshold and +50% buff; it was not proof of an award bug.

PercentXPIncrease buffs now join the temporary-duration branch in
Mob::GetBuffDurationForTarget (spells.cpp). Positive remaining/focused timers
survive load; stale -1000/-1 finite-duration copies become1, then0, then fade
across two unsuspended BuffProcess callbacks. Native permanent/aura formulas,
ordinary blessings and NPC policy remain unchanged. ZoneDatabase::LoadBuffs
and pet restore already invoke this policy. No offline buff DELETE is needed.
The observed spell21030 is finite formula3600/cap2400, effect337/base50.
Goldwind no longer grants it; future earned boosts remain a separate proposal.

Source: SOURCE. RELEASE contains native-build-manifest.json,
rollout.py,23 Windows/Linux operation tests, fresh backup/preservation and
deployed.json receipts. The zone-only build reproduces current59831725 before
replacing spells.cpp.o; deployed successor5dd5a655 preserves world/shared/client
and caches. Full supported runtime restart loads the rule and quest pair.
197 native AA arithmetic checks,21 duration groups and6 Goldwind interactions
pass; these use actual functions with boundary fakes, not full-game acceptance.
Wiki465/private guide5 HTTPS files verify. Owner gameplay/balance QA remains open.

Classic50 and level1 AA eligibility remain. #aaexp off adds10% passive AA
without reducing normal XP; #aaexp on diverts to full AA with no passive extra.
Modern scaling and normalized mode remain false. Compiled fallbacks remain
1%/23,976,503, so retain production overrides. No rank, cost or legal-pool change.
Rollback restores only the prior image/quest/rule; retained remainder may convert
under a lower threshold on the next award. Never restore old player snapshots.
""".replace('SOURCE',source).replace('RELEASE',release)
    world="""## Commonlands XP blessing - retired October 21
Owner-authorized main PR268 and production release retire both ecommons and
legacy poknowledge Magus_Goldwind.pl payment/grant paths. Hail/empower direct
players to Matron Restora's free ordinary buffs. Matron scripts remain exact.
No replacement earned boost is released.

The old explicit2400-tick spell21030 grant could inherit ordinary buff permanence.
The zone now classifies PercentXPIncrease effects as temporary: positive timers
are preserved; stale finite-duration -1000/-1 copies receive the minimum native
countdown on load (two unsuspended processing callbacks to fade). Native
permanent/aura formulas remain intact. Offline character rows are not deleted.
Do not infer every existing boost came from Goldwind or clear unrelated buffs.

Source/tests/evidence: SOURCE, RELEASE.
Zone5dd5a655 plus the paired quest scripts and1m AA rule are deployed through a
supported full-runtime restart. Client/world/shared caches unchanged; earned
state preserved. Native21 duration groups,6 quest interactions and23 operation
tests pass; public guides verify. Owner gameplay acceptance remains open.
""".replace('SOURCE',source).replace('RELEASE',release)
    wiki="""## AA pacing and XP blessings - published October 21
Wiki20261021-aa-million-v1 and private guide20261021-aa-million-guide-v1 replace
the earlier same-day40k guidance after verified main/server activation. Current
guidance:1,000,000 XP per AA,10% passive, earned state retained; Goldwind retired,
Matron free buffs preserved, XP boosts timed and stale copies repaired on load.

All21 maintained guides and432 generated reward routes reviewed. Eight guides
(home,Features,Getting started,Commands,Multiclass,Combat,Tunnel,Recent changes)
and private HTML changed; catalog values, item/zone acquisition and commands
remain unchanged. Future earned boosts are labeled under consideration.
All465 wiki and5 private guide HTTPS hashes/header protections verify. Guarded
publishers rehearse rollback and preserve private downloads/config/service
identities. Evidence: SOURCE/RELEASE, including wiki-review.json,
guides-publication.json and both public-verification.json receipts. Source
ledger is private. Owner gameplay/balance acceptance remains open.
""".replace('SOURCE',source).replace('RELEASE',release)
    originals={};updated={}
    for filename,title,new in [('multiclass.md','## XP',xp),('world.md','## Commonlands XP blessing',world),('wiki.md','## AA pacing',wiki)]:
        p=SKILL/'references'/filename;originals[p]=p.read_text(encoding='utf-8')
        updated[p]=replace_section(originals[p],title,new)
    p=SKILL/'references/operations.md';originals[p]=p.read_text(encoding='utf-8')
    block="""## AA million-point release - October 21, deployed for live QA
Main PR268/e64f502 and SOURCE/RELEASE record owner-authorized
1m XP per point,10% passive, retired Goldwind scripts and timed XP boost policy.
Zone-only successor5dd5a655 is built from exact reproduced59831725 baseline;
world/shared/client/caches are retained. Full-runtime restart, fresh stopped
backup, current player/content checks and all12 zones verify before reopening.
Never kill one child or restore old player snapshots.

Two preflights stopped before live changes because image construction consumed
more than a raw zone layer. Recovery pruned only three named task build caches
and four upload archives with exact retained local copies. Pinned candidate reuse
avoided another build; backups and active services were retained. Reserve512MiB
runtime headroom after backup and before reopening.

First boot naturally expired485 non-corpse NPC cache rows older than7days in
zones38/75. An exact cache-only scratch restore authenticated the original hash,
removed set and surviving fields; all other player/custom state was unchanged.
finish_cache.py pins the after hash, preserves the original hold, takes another
stopped backup and verifies a fresh restart before reopening. Never ignore cache
drift generically or restore old earned state. Deployment and website evidence
remain distinct from owner gameplay acceptance.
""".replace('SOURCE',source).replace('RELEASE',release)
    updated[p]=originals[p].replace('\n## ', '\n'+block+'\n## ',1)
    p=SKILL/'references/sources.json';originals[p]=p.read_text(encoding='utf-8')
    d=json.loads(originals[p]);revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()+' + verified deployment/publication evidence'
    common=[release+n for n in ['README.md','rollout.py','native-build-manifest.json','deployed.json','verification.json','review.md','finish_cache.py','test_finish_cache.py','cache-diagnosis.json','cache-source-pairing.json']]
    requested={
      'multiclass':common+['server-mods/code/zone/spells.cpp','tools/tests/test_aa_temporary_buffs.py','tools/tests/test_aa_point_cost_million.py'],
      'world':common+['server-mods/quests/ecommons/Magus_Goldwind.pl','server-mods/quests/poknowledge/Magus_Goldwind.pl','tools/tests/test_goldwind_retired.pl'],
      'wiki':[release+n for n in ['wiki-review.json','guides-publication.json','wiki-public-verification.json','guide-public-verification.json']]+['wiki/README.md','wiki/content-review.json','wiki/test_wiki.py','index.html','docs/ops/player-website.md','docs/ops/nightcap-wiki.md']+['wiki/articles/'+n+'.json' for n in ['combat','commands','features','getting-started','index','multiclass','recent-changes','tunnel']],
      'operations':common}
    for topic,paths in requested.items():
        d['topics'][topic]=[e for e in d['topics'][topic] if e['path'] not in paths]
        for name in paths:
            file=ROOT/name;assert file.is_file(),name
            d['topics'][topic].append({'root':str(ROOT).replace('\\','/'),'path':name,'revision':revision,'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'role':'Reviewed1m AA/XP boost release and verified deployment/publication; owner gameplay acceptance open'})
        for e in d['topics'][topic]:
            if 'aa-pacing-options-20261021' in e.get('root',''):e['role']='Historical pre-release analysis; superseded by verified1m AA/XP boost release'
            if 'aa-point-cost-40000-20261021' in e['path']:e['role']='Historical40k trial evidence; superseded by verified1m AA/XP boost release'
    updated[p]=json.dumps(d,ensure_ascii=False,indent=2)+'\n'
    patch=''.join(''.join(difflib.unified_diff(originals[p].splitlines(True),v.splitlines(True),fromfile=str(p),tofile=str(p))) for p,v in updated.items())
    (ART/'knowledge-update.patch').write_text(patch,encoding='utf-8')
    for p,v in updated.items():p.write_text(v,encoding='utf-8')
    (ART/'knowledge-update-receipt.json').write_text(json.dumps({'files':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in updated},'status':'applied'},indent=2)+'\n')
    print('Installed knowledge updated; exact patch retained')
if __name__=='__main__':main()
