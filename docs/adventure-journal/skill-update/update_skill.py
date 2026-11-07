"""Prepare the exact reviewed Nightcap knowledge patch; apply only with --apply."""
import argparse
import difflib
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SKILL = Path('C:/Users/verre/.codex/skills/nightcap-development')
OUT = Path(__file__).resolve().parent


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    paths = ['references/world.md', 'references/wiki.md', 'references/sources.json']
    before = {p: (SKILL / p).read_bytes() for p in paths}
    after = {p: b.decode('utf-8') for p, b in before.items()}

    world = after[paths[0]]
    start = world.index('Adventure Journal / Epic 0.5 remains a **candidate**')
    end = world.find('\n\n', start)
    if end < 0:
        end = len(world)
    replacement = '''Adventure Journal / Epic 0.5 remains an **unreleased eight-task candidate**;
the original compiled/tested scope is not recorded installed or player-accepted.
November6 owner intent extends it through Classic level50 with useful coordinated
progression armor. The Last Lantern proposal in
E:/EQ_Local_Dev/_worktrees/adventure-journal-endgame/docs/adventure-journal/CAMPAIGN.md
defines12playthrough chapters/16quest definitions, recurring companions and8armor
pieces across7visible regions, with40/46/final earned refits. Detailed story/reward
review precedes implementation; new scenes, armor, stats/materials and IDs are not
built or verified. Original catalog/plugins/native/client contracts are unchanged.
Native Tasks still own progress; nightcap_epic05_state owns attunement/cooldown.
Pair Epic05Contract(), plugins, item900501, tasks9500-9507 and spells42800-42805;
the gate starts disabled. Explore=5 credits movement; Touch=11 is a dynamic-zone
switch. Exact original checks/install boundaries remain in README.md, QA.md and
RELEASE.md. The expansion requires audited Classic materials, durable native
reward/refit receipts, preserved augments/custody and native appearance/balance QA;
LORE is not an ownership fence. No new runtime/cache/client reload is needed for
this proposal. Future implementation must ship its reviewed matching package.'''
    after[paths[0]] = world[:start] + replacement + world[end:]

    wiki = after[paths[1]]
    heading = '## Adventure Journal endgame — November6 unpublished design proposal'
    if heading in wiki:
        raise ValueError('Proposal knowledge is already installed; review before replay')
    first_line = wiki.index('\n') + 1
    addition = '''

## Adventure Journal endgame — November6 unpublished design proposal

Source E:/EQ_Local_Dev/_worktrees/adventure-journal-endgame. The owner requested
a living level50story and confirmed useful coordinated armor. The Last Lantern
proposal defines12chapters,16quest definitions and8pieces over7visible regions;
it is not implemented/installed or accepted in game. All41authored guides and
generated catalogs reviewed. Only In development/Change Log get explicit design
previews; Features keeps its Not released link, Home/commands/current acquisitions
and generated item/zone values remain. Original eight-task/charm build status is
preserved. No public publication is claimed; never republish this whole checkout
over newer public evidence. Twenty wiki/content/refresh checks pass with workspace
temp; historical global source drift remains REVIEW REQUIRED with no blanket
ledger advance. docs/adventure-journal/{CAMPAIGN.md,endgame-review.json} owns scope,
checks and the pending detailed design/implementation/native/material/balance gates.
'''
    after[paths[1]] = wiki[:first_line] + addition + wiki[first_line:]

    manifest = json.loads(after[paths[2]])
    revision = subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip()
    manifest['observed_revisions']['adventure_journal_endgame_proposal_20261106'] = revision + ' + reviewed design working tree'
    groups = {
        'world': {
            'docs/adventure-journal/README.md': 'eight-task built candidate; Last Lantern expansion proposed only; not installed',
            'docs/adventure-journal/CAMPAIGN.md': 'owner-requested level50 narrative and useful armor; detailed design review pending',
            'docs/adventure-journal/SPEC.md': 'original candidate contract with explicit proposed expansion boundary',
            'docs/adventure-journal/catalog.json': 'unchanged eight-task catalog; no expansion IDs or armor implemented',
            'tools/epic05.py': 'reviewed unchanged generator fixes first campaign at eight tasks; expansion needs deliberate versioned design',
            'server-mods/plugins/epic05.pl': 'reviewed unchanged task/attunement/charm service; no armor delivery adapter',
            'docs/lore/structure.md': 'Last Lantern original fiction proposal, not live NPCs or canonical claims',
        },
        'wiki': {
            'wiki/articles/unreleased.json': 'unpublished Last Lantern design preview; original candidate remains uninstalled',
            'wiki/articles/recent-changes.json': 'unpublished dated proposal entry; no release or player acceptance claim',
        },
    }
    for topic, entries in groups.items():
        for path, role in entries.items():
            rows = manifest['topics'][topic]
            rows[:] = [entry for entry in rows if entry['path'] != path or (topic == 'wiki' and entry['root'] != ROOT.as_posix())]
            rows.append({'root': ROOT.as_posix(), 'path': path, 'role': role,
                         'revision': revision + ' + reviewed design working tree',
                         'sha256': digest((ROOT / path).read_bytes())})
    after[paths[2]] = json.dumps(manifest, ensure_ascii=False, indent=2) + '\n'
    patch = ''.join(''.join(difflib.unified_diff(
        before[p].decode('utf-8').splitlines(keepends=True), after[p].splitlines(keepends=True),
        fromfile='a/' + p, tofile='b/' + p)) for p in paths)
    (OUT / 'installed-nightcap.patch').write_text(patch, encoding='utf-8', newline='')
    receipt = {'applied': False, 'skill': SKILL.as_posix(), 'files': [
        {'path': p, 'before_sha256': digest(before[p]), 'after_sha256': digest(after[p].encode('utf-8'))}
        for p in paths]}
    if args.apply:
        for p in paths:
            if (SKILL / p).read_bytes() != before[p]:
                raise ValueError('Concurrent skill change; refuse overwrite: ' + p)
        for p in paths:
            (SKILL / p).write_bytes(after[p].encode('utf-8'))
        receipt['applied'] = True
    (OUT / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print('Installed reviewed skill patch.' if args.apply else 'Saved exact pending skill patch; no installed files changed.')


if __name__ == '__main__':
    main()
