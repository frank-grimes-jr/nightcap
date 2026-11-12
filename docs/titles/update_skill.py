"""Prepare an exact installed-skill patch; apply only against its preimages."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL = Path('C:/Users/verre/.codex/skills/nightcap-development')
HERE = Path(__file__).resolve().parent

REFERENCE = '''# Earned cosmetic titles — November12 candidate

Source E:/EQ_Local_Dev/_worktrees/earned-titles, feature/earned-titles based on
origin/main423f9c3b. 77title definitions are generated with the wiki by
tools/earned_titles.py. Topic `titles` checks the reviewed implementation/evidence.
This is disabled source, not deployed, published or player accepted.

Native title selection/HasTitle authorizes permanent per-character awards using
IDs1900000000–1900000999. Existing database IDs in that range suspend this system.
No power/item/currency/XP or automatic worn-title change. Stable issued IDs must
never be reused. Three new InnoDB tables install disabled; separate enabled row
and catalog_version1 fence activation. Keep awards/counters during recovery.

Slayer totals100/1000/10000; undead100/1000/5000; giants100/1000; dragons1/10/100.
Native finalized deaths and normalized owner/party credit fence counting. Victims
must have native spawn points and be unowned/non-transient/non-merchant/non-chest;
ordinary status0, loaded/connected/alive members within200units and non-gray con
qualify. New counters start at activation, saturate10000 and are never backfilled
from guesses. Failed/uncertain cosmetic writes log without replay or combat veto.
Named home-zone Nagafen/Vox/dracoliche victories can recover from personal boss
ledger credit. General totals cannot. Native body types determine families.

Personal completed_at>0 Keeper ledgers own full-clear titles; Raid mode1 across
all21Classic zones owns Conqueror of Classic. Normalize historical Hate76 to186;
Chapterhouse760/Kael113 cannot substitute. Partial/global/other-member credit is
insufficient.34skill titles require level50+ and persisted/loaded raw skill at the
highest held-class native level50 cap; zero caps and skill bonuses do not qualify.
Existing race/class/crafting/New Tanaan policy remains. Seven crafts together
earn Master Artisan. Native completed_tasks9515/activity-1 owns Last Lantern.
Awards survive class release; the title list/#titles lazily reconciles old goals.
Finalized kills and successfully saved skill updates reconcile immediately.

Source: common/earned_title_{policy,catalog}.h; zone/earned_titles.{h,inc},
titles.cpp, attack.cpp, client.cpp, command.{cpp,h}. Four focused test groups
include compiled policy and actual adapter/failure controls. Four complete native
units syntax-compile against retained November12 inputs;10isolated MariaDB checks
pass. Commands/hashes: docs/titles/native-compile.json and storage-tests.json.
No full linked shipping build or native player QA is claimed. Activation requires
the matching zone build/storage, no new Client layout/rules/cache/quest/client.
Production native refresh uses guarded whole-runtime activation, not worker kills.

Contract, exact player QA, activation/recovery and whole-wiki assessment live in
docs/titles/{SPEC,QA,README,wiki-impact}.md. New Titles guide plus Features/Home,
commands/previews/Change Log and five owning guides retain Not released labels.
607HTML pages/links/privacy/search build checks pass. No web browser is connected,
so rendered/mobile and RoF2 picker/nameplate acceptance remain open. Global wiki
historical drift stays REVIEW REQUIRED; no blind ledger advance or publication.
'''


def digest(data):
    return hashlib.sha256(data).hexdigest()


def prepare():
    changes = []

    def change(relative, after):
        path = SKILL/relative
        before = path.read_bytes() if path.exists() else b''
        changes.append(dict(path=relative, before_sha256=digest(before), after=after))

    skill = (SKILL/'SKILL.md').read_text(encoding='utf-8')
    anchor = '| Journal campaign, earned outfits, private company memories |'
    assert anchor in skill and '| Earned titles,' not in skill
    at = skill.index(anchor)
    skill = skill[:at] + '| Earned titles, slayer/dragon ranks, expansion conquest and skill mastery | [Earned titles](references/titles.md) / `titles` |\n' + skill[at:]
    change('SKILL.md', skill)
    change('references/titles.md', REFERENCE)
    wiki = (SKILL/'references/wiki.md').read_text(encoding='utf-8')
    at = wiki.index('\n')+1
    wiki = wiki[:at] + '\n## Earned titles — November12 disabled candidate\n\n77cosmetic titles have a generated Not released Titles guide, Features/Home and\ncommand/owning-guide links in E:/EQ_Local_Dev/_worktrees/earned-titles. See\nreferences/titles.md and docs/titles/wiki-impact.md.607HTML pages/link/privacy/\nsearch checks pass; browser/rendered QA is unavailable. No gameplay activation or\npublic publication. Preserve global REVIEW REQUIRED and newer public source.\n\n' + wiki[at:]
    change('references/wiki.md', wiki)
    manifest = json.loads((SKILL/'references/sources.json').read_text(encoding='utf-8'))
    files = {
        'tools/earned_titles.py': 'Reviewed 77-title source catalog and native/wiki generator',
        'server-mods/code/common/earned_title_policy.h': 'Threshold, cap, Classic checklist and credit policy',
        'server-mods/code/common/earned_title_catalog.h': 'Generated stable title IDs and exact requirements',
        'server-mods/code/zone/earned_titles.h': 'Title adapter interface',
        'server-mods/code/zone/earned_titles.inc': 'Persistent counters/awards, native ledgers and guarded reconciliation',
        'server-mods/code/zone/titles.cpp': 'Native earned title packet/selection integration',
        'server-mods/code/zone/attack.cpp': 'Finalized native death hook and captured ownership',
        'server-mods/code/zone/client.cpp': 'Successfully saved skill update hook and native multiclass caps',
        'server-mods/code/zone/command.cpp': 'Player #titles registration and pagination',
        'server-mods/code/zone/command.h': 'Native command declaration',
        'tools/tests/test_earned_titles.py': 'Compiled policy, actual adapter and generation regression groups',
        'tools/tests/earned_titles_service_fixture.cpp': 'Durable/failed/uncertain storage and selection controls',
        'docs/titles/setup.sql': 'Three additive disabled InnoDB tables',
        'docs/titles/native-compile.json': 'Four native syntax compile commands and source hashes; no deployment',
        'docs/titles/storage-tests.json': 'Ten real isolated MariaDB checks',
        'docs/titles/SPEC.md': 'Candidate contract, assumptions and alternatives',
        'docs/titles/QA.md': 'Exact normal-player acceptance gates, all OPEN',
        'docs/titles/README.md': 'Verification, activation and forward recovery boundary',
        'docs/titles/wiki-impact.md': 'Whole-wiki scoped candidate review and unavailable visual QA',
        'wiki/articles/titles.json': 'Generated unreleased player title requirements',
    }
    manifest['topics']['titles'] = [dict(root=ROOT.as_posix(), path=name, role=role,
                                        sha256=digest((ROOT/name).read_bytes())) for name, role in files.items()]
    manifest['observed_revisions']['earned_titles_candidate_20261112'] = 'origin/main423f9c3b plus reviewed feature/earned-titles working changes; disabled, not deployed/published/accepted'
    change('references/sources.json', json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
    patch = ''
    for item in changes:
        path = SKILL/item['path']
        before = path.read_text(encoding='utf-8') if path.exists() else ''
        patch += ''.join(difflib.unified_diff(before.splitlines(True), item['after'].splitlines(True),
                                             fromfile='a/'+item['path'], tofile='b/'+item['path'], n=0))
    (HERE/'installed-skill.patch').write_text(patch, encoding='utf-8', newline='\n')
    (HERE/'skill-maintenance-plan.json').write_text(json.dumps(changes, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print('Prepared exact patch for four installed skill files')


def apply():
    changes = json.loads((HERE/'skill-maintenance-plan.json').read_text(encoding='utf-8'))
    for item in changes:
        path = SKILL/item['path']
        assert digest(path.read_bytes() if path.exists() else b'') == item['before_sha256'], 'skill changed; re-review '+item['path']
    for item in changes:
        (SKILL/item['path']).write_text(item['after'], encoding='utf-8', newline='\n')
    print('Installed reviewed titles knowledge and source fingerprints')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    apply() if args.apply else prepare()
