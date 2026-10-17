"""Prepare/install guarded wiki and installed-knowledge updates; retain exact patches."""
import difflib
import hashlib
import json
import subprocess
import sys
from pathlib import Path

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
SKILL=Path('C:/Users/verre/.codex/skills/nightcap-development')
WIKI=Path('C:/Users/verre/.codex/worktrees/nightcap-wiki/EQ_Local_Dev')
sha=lambda b:hashlib.sha256(b).hexdigest()
stage=OUT/'maintenance'

if sys.argv[1:]==['install']:
    entries=json.loads((stage/'preimages.json').read_text())
    for e in entries:
        assert sha(Path(e['target']).read_bytes())==e['before'], 'Concurrent edit: '+e['target']
        assert sha((stage/e['payload']).read_bytes())==e['after']
    for e in entries:
        Path(e['target']).write_bytes((stage/e['payload']).read_bytes())
    (stage/'install-receipt.json').write_text(json.dumps(entries,indent=2)+'\n')
    print('Installed four guarded wiki/knowledge files.')
    raise SystemExit

stage.mkdir(exist_ok=True)
updates={}
recent_path=WIKI/'wiki/articles/recent-changes.json'
recent=json.loads(recent_path.read_text())
notice='<h2 id="idle-zone-20261017">October 17, 2026: idle-zone reliability correction</h2><ul><li>A server configuration correction has been applied for whole-game disconnects triggered when an empty zone unloads. The live reload completed without a restart; normal idle-unload and player-continuity verification are still pending.</li></ul>\n'
assert 'idle-zone-20261017' not in recent['body']
recent['body']=notice+recent['body']
recent['sources'].append('docs/ops/dynamic-zone-worker-lifetime-20261017/README.md and result.json; live rule reload verified, idle-unload/player acceptance pending')
updates[recent_path]=json.dumps(recent,ensure_ascii=False,indent=2)+'\n'

op_path=SKILL/'references/operations.md'
op=op_path.read_text()
marker='On OVH any native child exit can restart the entire runtime.'
assert marker in op
op=op.replace(marker,'On OVH any native child exit can restart the entire runtime. The October 17\ncorrection disables inherited `Zone:KillProcessOnDynamicShutdown` in default\nruleset 1; no alternate override existed. Preserve false in future rulesets.',1)
op+='''
## Idle-zone lifetime correction

October 17 14:47 UTC: production default `Zone:KillProcessOnDynamicShutdown`
changed true to false. `RuleManager::LoadRules` loads default before alternate
rulesets; a single stored row covered all active zones. `Zone::Shutdown` still
unloads data and saves state, but skips event-loop shutdown when false. The
supervisor itself is unchanged and still restarts everything on a native exit.

Runbook/source authority: `E:/EQ_Local_Dev/_worktrees/dynamic-zone-worker-lifetime/`
at origin/main a59974d plus the reviewed correction. Read
`docs/ops/dynamic-zone-worker-lifetime-20261017/README.md`, `ops/apply.py`,
`result.json`, `followup.json`, and `server-mods/code/zone/zone.cpp`. The deployed
journal manifest pins that zone source and the common rule loader, world/zone
reload handlers and wire declarations. Current local full-source zone.cpp lags.

Forward/inverse rollback-only transaction rehearsal passed before exactly one
live update; complete rule preimage retained privately. Authenticated global
Rules reload completed in world and all12 workers, preserving all15 native
lifetimes and all5 service identities. No binary/cache/client pairing is needed.
Natural timer-driven unload and player continuity acceptance remain pending.
Do not force a process exit to test or refresh a zone. Keep a player elsewhere
while an empty East Commonlands or Befallen instance reaches its existing timer;
verify the same worker lifetime, no supervisor restart, and continued play.

Both October16 reported incidents and another October17 10:42 a.m. Eastern
incident are in retained Docker logs. Capture the full relevant interval and
both stdout/stderr before filtering; a filtered tail missed the original cause.
OS exit code and introduction date remain unknown. Native file log time differs
from Eastern; correlate using UTC Docker timestamps. On uncertain activation,
inspect the receipt and row, retain false and retry the supported reload; never
automatically re-enable the restart cause or restore old player data. Historical
October9/11 true-rule operations notes are dated, not current instructions.
'''
updates[op_path]=op
wiki_path=SKILL/'references/wiki.md'
wiki=wiki_path.read_text()
wiki+='''
October17 idle-zone reliability correction: all21 maintained guides and432
generated reward routes assessed. Only Recent changes receives a local notice:
production rule correction/reload verified, natural unload/player continuity
pending. Features/home/commands/travel/dungeons/catalog values and release labels
remain correct. No public wiki release was made. Exact review, source-drift
report, maintenance patch and guarded install receipt are in
`E:/EQ_Local_Dev/_worktrees/dynamic-zone-worker-lifetime/docs/ops/dynamic-zone-worker-lifetime-20261017/`.
Preserve the prior candidate notices and global historical audit revision.
'''
updates[wiki_path]=wiki

sources_path=SKILL/'references/sources.json'
sources=json.loads(sources_path.read_text())
revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()+' + reviewed operational correction'
sources['observed_revisions']['idle_zone_lifetime_20261017']=revision
for rel,role in [
    ('server-mods/code/zone/zone.cpp','Manifest-matching Zone::Shutdown and idle timer behavior'),
    ('deploy/production/start.py','Inspected production-matching any-child-exit supervisor'),
    ('docs/ops/dynamic-zone-worker-lifetime-20261017/README.md','Live correction, retained incidents, pending natural-unload/player QA'),
    ('docs/ops/dynamic-zone-worker-lifetime-20261017/ops/apply.py','Guarded one-rule operation, rollback rehearsal and global reload verification'),
    ('docs/ops/dynamic-zone-worker-lifetime-20261017/ops/verify.py','Read-only native lifetime and incident follow-up'),
    ('docs/ops/dynamic-zone-worker-lifetime-20261017/result.json','Verified live rule reload with native/service identities preserved'),
    ('docs/ops/dynamic-zone-worker-lifetime-20261017/followup.json','Dated follow-up; no natural unload observed yet'),
    ('docs/ops/dynamic-zone-worker-lifetime-20261017/wiki-review.md','Whole-wiki impact assessment; local notice, not publication'),
]:
    sources['topics']['operations'].append({'root':ROOT.as_posix(),'path':rel,'role':role,'revision':revision,'sha256':sha((ROOT/rel).read_bytes())})
for entries in sources['topics'].values():
    for entry in entries:
        if Path(entry['root'])/entry['path']==recent_path:
            entry.update(sha256=sha(updates[recent_path].encode()),revision='f106a5d + reviewed reliability notice; not published')
updates[sources_path]=json.dumps(sources,ensure_ascii=False,indent=2)+'\n'

patch=[]; preimages=[]
for number,(target,text) in enumerate(updates.items()):
    before=target.read_bytes(); after=text.encode()
    payload=str(number)+'-'+target.name
    (stage/payload).write_bytes(after)
    preimages.append({'target':target.as_posix(),'before':sha(before),'after':sha(after),'payload':payload})
    (stage/('before-'+payload)).write_bytes(before)
    patch.extend(difflib.unified_diff(before.decode().replace('\r\n','\n').splitlines(True),text.splitlines(True),fromfile=target.as_posix(),tofile=target.as_posix(),n=0))
(stage/'preimages.json').write_text(json.dumps(preimages,indent=2)+'\n')
(stage/'update.patch').write_bytes(''.join(patch).encode())
print('Prepared four files and exact patch; external files unchanged until install.')
