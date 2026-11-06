"""Prepare the exact installed Nightcap knowledge patch; --apply requires skill-write access."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'docs/dungeons/readiness-20261106'
SKILL = Path('C:/Users/verre/.codex/skills/nightcap-development')


def section(text, heading, replacement):
    start = text.index(heading)
    end = text.index('\n## ', start+len(heading))
    return text[:start]+replacement.rstrip()+'\n'+text[end:]


def main(apply):
    revision = subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip()
    names = ('world.md','operations.md','sources.json')
    originals = {n: (SKILL/'references'/n).read_text(encoding='utf-8') for n in names}
    changed = {}
    native = json.loads((HERE/'native-build-current.json').read_text())
    changed['world.md'] = section(originals['world.md'],
        '## Every Classic dungeon and unique rewards — October22 deployed for live testing', f'''## Classic dungeons and compiled release readiness — November6 repair candidate

Raid/Grind remains a live-testing system:21Classic zones plus separate level50
Chapterhouse/Kael expeditions. Existing revision2026101601, permanent run UUIDs,
native allocation generations, boss credit, corpse envelopes, timers, journal
history and once-only reward receipts remain authoritative. Owner entry/full-clear
and solo/multiclass balance QA are separately scoped; never reset a run to repair
a server/catalog mismatch or infer current acceptance from October16's Befallen QA.

November6 owner reports both modes rejected in Crushbone. Read-only checks against
the exact retained deployed header pass51schema and669/671content: only
vigil/items/0 and compact/items/0 reject the already-released eight expedition
augments. Operator overrides validated new SQL afterimages but left compiled
SQL/cache guards stale. All dungeons share this fail-closed admission gate.
The repaired target passes all51/671 read-only production checks. This proves
compatibility, not installation or successful player entry.

Current repair source: {ROOT.as_posix()},
base{revision} with reviewed task edits. Evidence and exact QA:
docs/dungeons/readiness-20261106/README.md and its native-build-current.json,
production-before.json, production-target-contract.json and wiki-review.json.
Context topic dungeon-readiness pins reviewed source/tests/evidence.
tools/dungeon_refresh_contract.py applies only the reviewed November6 audit
delta to historical compilers/SQL predicates, rejects preimage drift and preserves
the current106 Hate layout/density/landmark checks. Do not regenerate from the
older650-check/176point main mirror: actual retained live is671checks/223points.
Never rerun October16/22 dungeon or November6 augment migrations for this fix.

Candidate native{native['candidate_shipping_sha256'][:16]} is built/tested,
not deployed or player-accepted. Exactly two SQL checks/eight cache cases change;
all other native cases,51schema/669other content checks and current Hate placement
remain. Actual ItemData/CacheMatches rejects all eight new afterimages before the
fix, accepts them after it and rejects icon/healing/focus metadata mutations.
Twenty-two dungeon regressions pass; generator output is reproducible. Focus
Type/Level/Level2 must accompany active Cinder focus IDs in cache validation.

The mandatory current-baseline relink preserves all12command archive members
and reproduces deployed3fc2b901 before replacing only dungeon_service.cpp.o.
Retain current #augstats, signed0.13.3/2026110601, world/shared_memory, quests,
current item definitions and generated cache. This fix needs only the matching
zone binary through an authorized supervised whole-runtime restart with a fresh
stopped backup and saved-state/market checks; no SQL/cache regeneration/client
update or quest/rule reload. Never kill one OVH zone child or restore players.

Whole wiki reviewed:41authored articles plus generated catalog impact; only
unpublished candidate history/development notes change. Public publication is
not claimed; main/server promotion and owner Crushbone Raid/Grind/campaign/Hate
regression QA remain pending. Existing reward budgets/rates and legal balance
pool are unchanged. Earlier October22 similar stale-item incident is historical;
maintain compiled admission guards with every content release.
''')
    marker = '\n## Hate boss placement — October30 deployed; indexed forward continuation'
    paragraph = f'''\nKeeper repair follow-up remains an unpublished local candidate in
{ROOT.as_posix()}.
Its native-build-current.json reproduces this3fc2b901 baseline and preserves the
complete current report command archive before replacing only the dungeon TU.
The earlier bc88-only readiness build is not the deployable pair. Compiled
expedition SQL/cache guards must follow content changes: operator contract
overrides alone do not update native Keeper admission. See world.md's compiled
release readiness section and topic dungeon-readiness for exact evidence/QA.
'''
    assert marker in originals['operations.md']
    changed['operations.md'] = originals['operations.md'].replace(marker, paragraph+marker, 1)
    manifest = json.loads(originals['sources.json'])
    paths = ['server-mods/code/common/dungeon_contract.h','tools/dungeon_contract.py',
             'tools/dungeon_refresh_contract.py','tools/tests/test_dungeon_release_readiness.py',
             'tools/tests/test_dungeon_lifecycle.py','tools/build_dungeon_readiness.py',
             'tools/relink_dungeon_current.py','tools/probe_dungeon_build.py',
             'tools/probe_dungeon_readiness.py','docs/dungeons/runtime-contract.json',
             'docs/audits/augments-20261106/item-preimages.json',
             'docs/dungeons/hate-boss-placement-20261030/runtime-checks.json',
             'docs/dungeons/readiness-20261106/README.md',
             'docs/dungeons/readiness-20261106/native-build-current.json',
             'docs/dungeons/readiness-20261106/production-before.json',
             'docs/dungeons/readiness-20261106/production-target-contract.json',
             'docs/dungeons/readiness-20261106/wiki-review.json']
    entries = [dict(root=ROOT.as_posix(),path=p,role='November6 reviewed Keeper repair candidate; built/tested, no deployment or owner entry QA',
                    revision=revision+' + reviewed task edits',sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()) for p in paths]
    manifest['topics']['dungeon-readiness'] = entries
    manifest['observed_revisions']['dungeon_readiness_candidate_20261106'] = revision+' + reviewed task edits; not deployed'
    bypath = {e['path']:e for e in entries}
    for entry in manifest['topics']['world']:
        if entry['path'] in bypath:
            entry.update(bypath[entry['path']])
    changed['sources.json'] = json.dumps(manifest, indent=2)+'\n'
    patch = ''.join(''.join(difflib.unified_diff(originals[n].splitlines(True), changed[n].splitlines(True),
                fromfile='a/references/'+n,tofile='b/references/'+n)) for n in names)
    (HERE/'installed-nightcap.patch').write_text(patch, encoding='utf-8')
    if apply:
        assert all((SKILL/'references'/n).read_text(encoding='utf-8')==originals[n] for n in names), 'Concurrent skill edit'
        for name in names:
            (SKILL/'references'/name).write_text(changed[name],encoding='utf-8',newline='\n')
    print(json.dumps(dict(status='applied' if apply else 'prepared; installation pending',files=list(changed),fingerprints=len(entries))))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    main(parser.parse_args().apply)
