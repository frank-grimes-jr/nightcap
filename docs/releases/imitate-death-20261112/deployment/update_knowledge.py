"""Replace candidate knowledge only after verified native and public deployment."""
import argparse
import difflib
import hashlib
import json
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
SKILL=Path('C:/Users/verre/.codex/skills/nightcap-development')

def section(text, heading, replacement):
    start=text.find('## '+heading)
    if start<0:
        pos=text.index('\n## ')+1
        return text[:pos]+replacement+'\n'+text[pos:]
    end=text.find('\n## ',start+3)
    return text[:start]+replacement+'\n'+(text[end+1:] if end>=0 else '')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--write',action='store_true')
    parser.add_argument('--patch-name',default='installed-skill-live.patch');args=parser.parse_args()
    assert Path(args.patch_name).name==args.patch_name
    live=json.loads((OUT/'production-verification.json').read_text(encoding='utf-8'))
    wiki=json.loads((OUT/'wiki-public-verification.json').read_text(encoding='utf-8'))
    build=json.loads((OUT/'native-build.json').read_text(encoding='utf-8'))
    assert live['status']==wiki['status']=='PASS' and live['gateway_open'] and not live['client_update_required']
    assert wiki['files']==613 and build['shipping']['candidate-zone'].startswith('7bb5bd17')
    names=['references/'+n for n in ('multiclass.md','operations.md','wiki.md','sources.json')]
    before={n:(SKILL/n).read_text(encoding='utf-8') for n in names};after=dict(before)
    note='''## Imitate Death — November 12 deployed for live QA

Owner explicitly requested live deployment. Main PR425/1d763739, source5642fcc1,
E:/EQ_Local_Dev/_worktrees/imitate-death-no-cooldown. Family420 (retained rank1255,
spell5918) has zero authoritative reuse. common/imitate_death.h projects AA load;
zone/aa.cpp retires only this family's saved wait on authorized activation/resend
and passes zero reuse even under negative focus. Earned/class/casting/standing
checks and original spell effects remain; basic Feign Death skill reuse stays.
RoF2 advertises1for Make Hotkey; every family420 timer packet resets(begin0,end
now), including stale resends. Generic detail can show1second; actual reuse is0.
Relog and create the hotkey. No signed client/SQL/rule/cache/quest/layout change.

Shipping zone7bb5bd17 preserves world95fc228a/shared_memoryb60c4dfc, Quick Buff,
augment repair, Last Lantern and newer retained Hate source. Current deployed
zone3eeb72c9 reproduced exactly; one affected TU compiled against2857authenticated
source files,840actual dependencies and146unchanged link inputs. ELF loaded-byte
identity passes. Native AA18/adjacent27tests, pinned RoF2 instructions47checks and
Linux operator9fault tests pass. The proof-only dependency-path normalization
failure was corrected by re-verifying completed artifacts, without replaying live
actions. Transient preflight lock contention preceded any action/receipt.

Guarded immutable image deployment has fresh stopped backup,125secondadmission
drain, clean whole-runtime stop, normal saved-state/one-market-rotation proof,
all12zone and unchanged native/service/content/cache/client verification. Access
is open; no player snapshot restored. Wiki20261112-imitate-death-v1 verifies613
public hashes/headers with610retained and five private denials. Exact release,
one-shot operator, receipts and in-game steps: docs/releases/imitate-death-20261112/.
Never replay terminal actions or kill one production zone. Owner hotkey/aggro and
combined-build balance acceptance remain OPEN; deployment is not acceptance.
'''
    current_heading=('Imitate Death — November 12 source candidate' if '## Imitate Death — November 12 source candidate' in before[names[0]] else 'Imitate Death — November 12 deployed for live QA')
    after[names[0]]=section(before[names[0]],current_heading,note)
    ops=before[names[1]].replace('## Current native baseline — November12 Quick Buff live QA','## Quick Buff — November12 retained predecessor')
    opsnote='''## Current native baseline — November12 Imitate Death live QA

PR425/1d763739; source5642fcc1. Shipping zone7bb5bd17 replaces3eeb72c9 while
world95fc228a/shared_memoryb60c4dfc and all current dependencies remain. Checkout
E:/EQ_Local_Dev/_worktrees/imitate-death-no-cooldown; docs/releases/imitate-death-20261112/deployment/.
Current shipping predecessor reproduced exactly,2857source/840compile dependencies
and146retained link inputs authenticate; one AA TU compile/relink, ELF/runtime
identity and9Linux operator fault tests pass. Current Client layout, Quick Buff
and newer retained Hate mapping/count223 stay; older Git mirrors are not a build
source replacement. No content/rule/schema/cache/quest/client change.

Use this release's one-shot operator and receipts. Zero players, deployment/GM
locks,125secondclosed-admission drain, clean whole-runtime stop, fresh stopped
backup, exact saved-state expiry/one-market-rotation and12workers verify. Access
reopened with DB/web/tunnel identity, native pair, player data, cache and signed
2026111201 unchanged. Wiki publication occurs afterward under its own guarded
content updater; all613HTTPS files/header protections verify with610retained.
Failure holds admissions; never replay actions, kill one zone or restore player
snapshots. Relog for zero-reuse Imitate Death; gameplay/balance acceptance OPEN.
One local activation SSH client stalled after the host action completed. Exact
host receipts and successful open/independent verification were authoritative;
only that local transport was closed. No live action was replayed or interrupted.
'''
    after[names[1]]=section(ops,'Current native baseline — November12 Imitate Death live QA',opsnote)
    wikinote='''## Imitate Death — November12 published for live testing

Wiki20261112-imitate-death-v1 supersedes Quick Buff v2 for public content only.
Authenticated previous613outputs reproduce; Combat, Change Log and search change,
610files retain exact bytes. All42authored sources, Home/Features/commands and
generated item/zone/catalog impacts reviewed. Imitate Death has no ability reuse,
old saved wait retired, earned Monk/casting checks retained; native generic detail
can show1second to support Make Hotkey. Basic Feign Death and Quick Buff stay.
Relog; no client update. Gameplay/balance acceptance remains OPEN.

All613HTTPS hashes/security headers and five private denials pass. Guarded update
rehearses recovery and preserves all five services, channel/config/downloads;
no Nginx reload or global source-ledger advance. Unrelated drift remains REVIEW
REQUIRED. Source and receipts: imitate-death-no-cooldown/docs/releases/imitate-death-20261112/deployment/.
Concurrent main PR426 adds a separately labeled, unpublished DoT candidate to
authoring sources. It is not in this native or public wiki payload. Preserve
both scopes; never infer candidate deployment from the integrated source tree.
'''
    after[names[2]]=section(before[names[2]],'Imitate Death — November12 published for live testing',wikinote)
    manifest=json.loads(before[names[3]])
    authoring=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    revision=f'live main PR425/1d763739 source5642fcc1; authoring {authoring} + reviewed worktree; owner QA OPEN'
    manifest['observed_revisions']['imitate_death_deployed_20261112']=revision
    manifest['observed_revisions'].pop('imitate_death_candidate_20261112',None)
    paths=['server-mods/code/common/imitate_death.h','server-mods/code/zone/aa.cpp',
           'tools/tests/test_aa_cooldown_identity.py','eq-client-dll/tests/aa-reuse-native.cpp',
           'tools/tests/test_imitate_death_rollout.py','tools/build_imitate_death_release.py',
           'docs/releases/imitate-death-20261112/README.md','docs/releases/imitate-death-20261112/wiki-review.json']
    paths+=['docs/releases/imitate-death-20261112/deployment/'+n for n in
            ('README.md','rollout.py','native-build.json','release-checks.json','review.json',
             'production-verification.json','wiki-publication.json','wiki-public-verification.json')]
    paths+=['docs/releases/imitate-death-20261112/deployment/concurrent-source-review.json']
    paths+=['wiki/articles/combat.json','wiki/articles/recent-changes.json']
    paths+=['tools/'+n for n in ('run_imitate_death_release.py','ship_imitate_death_release.py',
             'verify_imitate_death_release.py','test_imitate_death_linux.py','prepare_imitate_death_wiki.py',
             'publish_imitate_death_wiki.py','verify_imitate_death_wiki.py')]
    entries=[dict(root=ROOT.as_posix(),path=p,role='Reviewed Imitate Death implementation/live proof; owner gameplay and balance QA OPEN',
                  revision=revision,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()) for p in paths]
    manifest['topics']['multiclass']=entries+[e for e in manifest['topics']['multiclass'] if e['path'] not in paths]
    for topic in ('operations','wiki'):
        selected=[e for e in entries if '/deployment/' in e['path'] and
                  (topic=='operations' or '/wiki-' in e['path']) or topic=='wiki' and e['path'].startswith('wiki/')]
        scoped={e['path'] for e in selected}
        manifest['topics'][topic]=selected+[e for e in manifest['topics'][topic] if e['path'] not in scoped]
    after[names[3]]=json.dumps(manifest,ensure_ascii=False,indent=2)+'\n'
    patch=''.join(''.join(difflib.unified_diff(before[n].splitlines(True),after[n].splitlines(True),fromfile='a/'+n,tofile='b/'+n)) for n in names)
    (OUT/args.patch_name).write_text(patch,encoding='utf-8',newline='\n')
    if args.write:
        for n,text in after.items():(SKILL/n).write_text(text,encoding='utf-8',newline='\n')
    print('installed' if args.write else 'prepared')

if __name__=='__main__':main()
