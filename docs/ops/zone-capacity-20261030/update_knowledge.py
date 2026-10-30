"""Prepare/apply the scoped owner-required installed Nightcap knowledge update."""
import difflib
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
SKILL=Path('C:/Users/verre/.codex/skills/nightcap-development')
revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
section='''## Zone capacity — October30 tested candidate; storage blocks activation

Palwar's October29 19:43:33 EDT Fear transfer exhausted all12 loaded workers;
Fear never booted and the client returned to Feerrott. Misty freed the first
worker19:53:42. The October30 read-only diagnosis is retained under
E:/EQ_Local_Dev/docs/ops/fear-entry-20261030/; no successful retry is claimed.

Candidate source: E:/EQ_Local_Dev/_worktrees/zone-capacity,
feature/zone-capacity-20261030. tools/zone_capacity.py plans20 workers and only
five version0 retention changes: ecommons/rivervale5min, feerrott10min,
commons15min, eastkarana30min. Complete row guards preserve613other zone rows,
player/corpse/checkpoint state and all dungeon timers. Recursive installed-quest
review preserves Misty's stateful seasonal encounter, Highpass's combat-paused
Stanos timer, public Fear's spawn-triggered reset and special Sky/Kithicor/Tacvi
timers. Quest timers tick independently of idle NPC AI; finite cleanup windows
in the five selected zones fit the mixed policy. Do not replace this allowlist
with a global cap or claim unlimited capacity. Future scripts require review.

Eight policy/capacity tests and eight real MariaDB10.11 rehearsal groups pass,
including original failure, sustained160-step travel model, exact inverse and
drift/trigger/engine rejection. Five Linux production safeguards and resolved
Compose checks pass; independent source review has no blocking finding.
Evidence, resource snapshot, full rollback and exact in-game QA are in
docs/ops/zone-capacity-20261030/. Models/tests are not owner gameplay acceptance.

Not deployed. Production remains12 workers. Game peak1.54GiB/4500MiB and no OOM
support20 with eight additional256MiB worker budgets and512MiB reserve. No RAM
upgrade indicated by this snapshot; larger pools require new measurements.
Only512MiB host disk free: require3GiB before backup and2GiB after; do not delete
retained release evidence or player state. Strict preflight rejects stale captures,
unsafe rule overrides, OOM/service/resource drift. Main/maintenance approval,
storage remediation and owner QA remain pending. No wiki publication claimed.

Pair exact current image/binaries/cache/quests/signed client; no native rebuild.
Apply only the worker scalar and five guarded metadata fields during supported
whole-game maintenance with a verified fresh stopped backup. ZoneStore caches
the delay in each process and ResetShutdownTimer reuses it: SQL/natural unload
or ZoneData reload does not activate all timers. Never kill a zone worker.
Keep StateSavingOnShutdown=true and KillProcessOnDynamicShutdown=false; public
save-state replacement is not atomic. Full restart rotates the market normally.
Historical operator assertions of12 workers are frozen release evidence, not a
current20-worker verification contract. Recover metadata/config forward or by
guarded inverse; never restore old player/checkpoint snapshots.

'''
path=SKILL/'references/operations.md'
before=path.read_text(encoding='utf-8')
heading='## Zone capacity — October30'
start=before.index(heading)
end=before.find('\n## ',start+len(heading))
if end<0:end=len(before)
after=before[:start]+section+before[end:].lstrip('\n')
changes={path:(before,after)}
path=SKILL/'references/sources.json'
before=path.read_text(encoding='utf-8')
data=json.loads(before)
files={
 'tools/zone_capacity.py':'Scoped retention plan and fresh resource/rule safety gate',
 'tools/tests/test_zone_capacity.py':'Original and sustained travel regression and policy guards',
 'tools/tests/rehearse_zone_capacity.py':'Production-schema isolated MariaDB forward/inverse/fault proof',
 'deploy/production/compose.yaml':'Twenty-worker candidate; unchanged native image and memory/port contract',
 'deploy/production/test_compose.py':'Resolved worker/memory/network configuration proof',
 'docs/ops/zone-capacity-20261030/README.md':'Candidate status, resource blocker, maintenance/recovery and exact owner QA',
 'docs/ops/zone-capacity-20261030/review.md':'Independent recursive quest and implementation review',
 'docs/ops/zone-capacity-20261030/quest-review.json':'Read-only installed quest and inspected native source fingerprints',
 'docs/ops/zone-capacity-20261030/rehearsal.json':'Eight real MariaDB10.11 migration proof groups',
 'docs/ops/zone-capacity-20261030/resources.json':'Dated capacity, memory and disk evidence; no activation',
 'docs/ops/zone-capacity-20261030/wiki-review.json':'Whole-wiki candidate impact review; no publication',
 'docs/ops/zone-capacity-20261030/verification.json':'Automated verification and separate open deployment/owner gates',
}
entries=data['topics']['operations']
for relative,role in files.items():
    entry={'root':ROOT.as_posix(),'path':relative,'role':role,'revision':revision,
           'sha256':hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()}
    entries[:]=[e for e in entries if not(e['root']==entry['root'] and e['path']==relative)]
    entries.append(entry)
changes[path]=(before,json.dumps(data,indent=2,ensure_ascii=False)+'\n')
patch=''.join(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),
             fromfile=str(path),tofile=str(path))) for path,(old,new) in changes.items())
private=HERE/'private';private.mkdir(exist_ok=True)
(private/'installed-knowledge.patch').write_text(patch,encoding='utf-8')
if '--apply' in sys.argv:
    for path,(_,new) in changes.items():path.write_text(new,encoding='utf-8')
    print('Applied scoped operations knowledge and12 reviewed fingerprints.')
else:
    print('Prepared exact private/installed-knowledge.patch; not applied.')
