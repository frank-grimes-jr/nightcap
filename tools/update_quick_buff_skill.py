"""Prepare the exact installed Nightcap skill patch; --write applies it."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/releases/quick-buff-20261112'
MULTICLASS = '''## Quick Buff — November 12 source candidate, not deployed

Owner-confirmed behavior: AA hotkey casts eligible memorized buffs immediately
on self, normal group/pet delivery, one cost of50%maximum mana, no reuse.
Family48/ranks147–149 retain earned state, class masks and purchase costs; their
loaded graph becomes active type3 and loses the old passive haste. common/quick_buff.h
projects metadata on load; existing spell8 is presentation only and never cast.
zone/aa.cpp retains earned/rank/class/charge/native-slot authorization before
CastQuickBuff. zone/aa_quick_buff.inc snapshots/deduplicates buffs, checks canonical
held-class/current-level/scribed access and native caster/zone/target gates, then
debits once before native instant CastSpell calls. Native reagents, stacking,
range, events and group/pet delivery remain. Completion failures do not refund
the activation. No eligible buffs/insufficient mana costs nothing. Active casting,
recovery, death, unconsciousness and recursive activation are rejected.

Only active Quick Buff completion skips spell reuse and10ms recovery; its zero
family timer leaves unrelated deadlines intact. New Client member means a full
zone rebuild is mandatory. No SQL/rule/cache/quest/new spell asset or DLL delta.
tools/quick_buff_client.py produces only unsigned scoped147hotkey/description
strings from the authenticated current dbstr; pair via normal signed delivery,
full EQ exit/launcher Play. AA reload alone cannot install native behavior; use
supported whole-runtime activation, never kill a production zone.

Source E:/EQ_Local_Dev/_worktrees/quick-buff-hotkey, branch feature/quick-buff-hotkey,
baseb7e404b2. tools/tests/test_quick_buff.py compiles actual dispatcher/projection;
test_aa_cooldown_identity.py compiles activation/packet guards and unrelated timer
regressions. Both full modified translation units pass retained-Nov7-header syntax
checks; native-compile.json records exact pins. Not a full link/runtime/client QA.
docs/releases/quick-buff-20261112/README.md owns behavior, rollout/recovery and
exact East Commonlands player/balance QA. Server/client/wiki publication and
owner acceptance remain OPEN. Wiki candidate edits are local only; global source
drift remains REVIEW REQUIRED. Reviewed fingerprints: context.py --topic quick-buff.

'''
WIKI = '''## Quick Buff — November 12 unpublished candidate

Current source candidate: E:/EQ_Local_Dev/_worktrees/quick-buff-hotkey. Combat,
Multiclass, Features, In development and Change Log explicitly label the activated
Quick Buff hotkey Not released: instant eligible memorized buffs,50%maximum mana,
no reuse, normal self/group/pet delivery and spell restrictions. All42authored
article sources and generated/catalog impacts reviewed; Home navigation, commands,
item/zone/acquisition values stay accurate without edits. Fifteen wiki checks pass.
No public release, signed client publication or gameplay activation occurred.
Evidence: docs/releases/quick-buff-20261112/wiki-review.json and wiki-refresh.json.
Historical global source drift remains REVIEW REQUIRED, not blanket-approved.

'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skill', type=Path, default=Path('C:/Users/verre/.codex/skills/nightcap-development'))
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    names = ['SKILL.md', 'references/multiclass.md', 'references/wiki.md', 'references/sources.json']
    before = {n: (args.skill / n).read_text(encoding='utf-8') for n in names}
    after = dict(before)
    if '## Quick Buff — November 12 source candidate' not in before[names[1]]:
        heading, rest = before[names[1]].split('\n', 1)
        after[names[1]] = heading+'\n\n'+MULTICLASS+rest.lstrip('\n')
    if '## Quick Buff — November 12 unpublished candidate' not in before[names[2]]:
        heading, rest = before[names[2]].split('\n', 1)
        after[names[2]] = heading+'\n\n'+WIKI+rest.lstrip('\n')
    route = '| Quick Buff AA hotkey candidate | [Multiclass and progression](references/multiclass.md) / `quick-buff` |\n'
    if route not in before['SKILL.md']:
        anchor = '| Classes, spells, skills, AA ownership, XP |'
        position = after['SKILL.md'].index('\n', after['SKILL.md'].index(anchor))+1
        after['SKILL.md'] = after['SKILL.md'][:position]+route+after['SKILL.md'][position:]
    manifest = json.loads(before[names[3]])
    paths = ['server-mods/code/common/quick_buff.h', 'server-mods/code/zone/aa_quick_buff.inc',
             'server-mods/code/zone/aa.cpp', 'server-mods/code/zone/client.h', 'server-mods/code/zone/spells.cpp',
             'tools/quick_buff_client.py', 'tools/tests/test_quick_buff.py',
             'tools/tests/test_aa_cooldown_identity.py', 'tools/tests/test_gameplay_policies.py',
             'docs/releases/quick-buff-20261112/README.md',
             'docs/releases/quick-buff-20261112/native-compile.json',
             'docs/releases/quick-buff-20261112/wiki-review.json']
    manifest['observed_revisions']['quick_buff_candidate_20261112'] = 'b7e404b2 + reviewed feature/quick-buff-hotkey working changes; not deployed'
    manifest['topics']['quick-buff'] = [dict(root=ROOT.as_posix(), path=n,
        role='Reviewed Quick Buff source/test/evidence candidate; no deployment or native acceptance',
        revision='b7e404b2 + reviewed candidate, 2026-11-12',
        sha256=hashlib.sha256((ROOT/n).read_bytes()).hexdigest()) for n in paths]
    after[names[3]] = json.dumps(manifest, ensure_ascii=False, indent=2)+'\n'
    patch = ''.join(''.join(difflib.unified_diff(before[n].splitlines(keepends=True),
        after[n].splitlines(keepends=True), fromfile='a/'+n, tofile='b/'+n)) for n in names)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/'installed-skill.patch').write_text(patch, encoding='utf-8', newline='\n')
    if args.write:
        for name in names:
            if before[name] != after[name]:
                (args.skill/name).write_text(after[name], encoding='utf-8', newline='\n')
    print(json.dumps(dict(status='installed' if args.write else 'prepared', files=names,
                         patch_bytes=len(patch.encode('utf-8')))))


if __name__ == '__main__':
    main()
