"""Prepare the exact installed-knowledge patch; apply only with --apply."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
SKILL=Path('C:/Users/verre/.codex/skills/nightcap-development')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    originals={p:(SKILL/p).read_text(encoding='utf-8') for p in ('SKILL.md','references/client.md','references/sources.json')}
    updated=dict(originals)
    route='| RoF2 UI, pets, buffs, models, signed client delivery | [Client and pets](references/client.md) / `client` |'
    assert route in updated['SKILL.md']
    updated['SKILL.md']=updated['SKILL.md'].replace(route,route+'\n| Heroic stats, yellow totals and Inventory display | [Client and pets](references/client.md) / `heroic-stats` |')
    note='''## Heroic stats — November12 production audit; main Inventory candidate

E:/EQ_Local_Dev/_worktrees/heroic-stats-inventory and
docs/releases/heroic-stats-inventory-20261112/ own source, read-only evidence,
candidate hashes and exact QA. Production world/12zone hashes match retained
November7 release; six standard heroic multipliers are1.0 and Nightcap melee/
spell scaling are true. HeroicStatsUseDataBucketsToScale=false disables only
extra bucket scaling, not heroics. Direct heroic INT-to-Spell Damage/WIS-to-Heal
rules remain0 and must not be enabled to repair a display. No balance change.

Signed2026110701 retains November6 Inventory XML cf0402a3. Stats already has
native gold heroic EQTypes251–257. Main Inventory lacked them. Unpublished,
unsigned one-XML candidate adds seven + signs/native values at x81/89 within
the existing120px stat column, using the existing gold214/178/40 and preserving
all existing controls/native normal-stat coloring. Tooltips explain heroics
are already included in the total. No command/poll/server/SQL/cache/ABI change.
tools/client_character_stats_ui.py::add_inventory_heroics is called by the
normal generator; inventory_heroics_xml inserts only additions into actual
published bytes. tools/stage_heroic_stats_client.py checks the descriptor and
unchanged controls; tools/probe_heroic_stats.py is production read-only.
Regression RED then5UI/5gameplayUI/11resource checks pass. Visible pixels,
equip/remove, zero/long values, zone/relog/skin reload remain owner QA.

Candidate is not installed or published. Freshly verify/sign a higher counter
with only this XML; preserve147other descriptors/URLs, current DLL/catalog/
config, notes/tombstones and gameplay assets. No server restart/build/reload.
After authorized publication exit EQ/use normal launcher Play. Rollback uses a
higher signed counter with previous XML and current unrelated assets, never a
player snapshot. Wiki Equipment/Augments/Features/Change Log have explicit
local Not released guidance; all42articles/Home/commands/catalogs assessed.
Global unrelated refresh drift remains review-required; publication pending.

'''
    text=updated['references/client.md'];pos=text.index('\n')+1
    updated['references/client.md']=text[:pos]+'\n'+note+text[pos:].lstrip('\n')
    manifest=json.loads(updated['references/sources.json'])
    paths=['tools/client_character_stats_ui.py','tools/tests/test_client_character_stats.py',
           'tools/probe_heroic_stats.py','tools/stage_heroic_stats_client.py',
           'server-mods/code/zone/bonuses.cpp','server-mods/code/zone/client_mods.cpp',
           'server-mods/code/common/patches/rof2.cpp','server-mods/code/common/ruletypes.h',
           'docs/releases/heroic-stats-inventory-20261112/README.md',
           'docs/releases/heroic-stats-inventory-20261112/verification.json',
           'docs/releases/heroic-stats-inventory-20261112/wiki-impact.json']
    entries=[]
    for path in paths:
        entries.append({'root':ROOT.as_posix(),'path':path,
            'role':'Reviewed November12 heroic production audit and unpublished main Inventory display; native visual QA pending',
            'revision':'b7e404b2 + reviewed feature/heroic-stats-inventory candidate',
            'sha256':hashlib.sha256((ROOT/path).read_bytes()).hexdigest()})
    assert 'heroic-stats' not in manifest['topics']
    manifest['topics']['heroic-stats']=entries
    for entry in manifest['topics']['character-stats-display']:
        if entry['path'] in paths[:2]:entry.update(next(e for e in entries if e['path']==entry['path']))
    manifest['observed_revisions']['heroic_stats_inventory_20261112']='b7e404b2 + reviewed feature/heroic-stats-inventory candidate; production read-only/native hashes match November7; display unsigned/unpublished; pixels pending'
    updated['references/sources.json']=json.dumps(manifest,indent=2,ensure_ascii=False)+'\n'
    patch=''.join(''.join(difflib.unified_diff(originals[p].splitlines(True),updated[p].splitlines(True),fromfile='a/'+p,tofile='b/'+p)) for p in originals)
    (HERE/'installed-skill.patch').write_text(patch,encoding='utf-8')
    if args.apply:
        for p in updated:
            assert (SKILL/p).read_text(encoding='utf-8')==originals[p]
            (SKILL/p).write_text(updated[p],encoding='utf-8')
    print('Installed skill updated' if args.apply else 'Exact installed-skill.patch saved; not applied')


if __name__=='__main__':main()
