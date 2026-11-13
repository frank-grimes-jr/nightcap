"""Prepare the exact installed-skill patch; --write installs after authorized access."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
SKILL = Path('C:/Users/verre/.codex/skills/nightcap-development')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    names = ['references/multiclass.md', 'references/sources.json']
    before = {n: (SKILL/n).read_text(encoding='utf-8') for n in names}
    after = dict(before)
    note = '''## Imitate Death — November 12 source candidate

Owner requests no cooldown. Family 420 (retained rank 1255/spell 5918) projects
zero reuse in common/imitate_death.h on AA load. zone/aa.cpp retires only its
saved wait on authorized activation/resend and forces zero cast reuse even with
negative focus. Ownership, held-class/casting/standing checks and spell effects
remain; basic Feign Death skill reuse is unchanged. RoF2 catalog advertises 1 for
Make Hotkey; every family 420 timer packet resets (begin 0/end now), so no actual
reuse. Generic details can show nominal 1 second. No Client layout, SQL, rule,
cache, quest, world/shared-memory or signed client change required by this patch.
Zone binary deployment still needs the current retained native baseline and
guarded whole-runtime procedure; AA reload alone is insufficient.

Source: E:/EQ_Local_Dev/_worktrees/imitate-death-no-cooldown, based on main
423f9c3b. tools/tests/test_aa_cooldown_identity.py tests actual native methods,
stale waits, repeated use, focus and guards. Adjacent cooldown regressions pass;
eq-client-dll/tests/aa-reuse-native.cpp executes 47 pinned client checks.
docs/releases/imitate-death-20261112/ owns proof, wiki impact and exact QA.
Source candidate only: full Linux zone build, deployment, public wiki publication
and owner gameplay/balance acceptance remain pending. No standing release approval.

'''
    text = before[names[0]]
    heading = '## Imitate Death — November 12 source candidate'
    if heading in text:
        start = text.index(heading)
        end = text.find('\n## ', start+3)
        text = text[:start]+text[end+1:] if end >= 0 else text[:start]
    pos = text.index('\n## ')+1
    after[names[0]] = text[:pos]+note+text[pos:]
    manifest = json.loads(before[names[1]])
    paths = ['server-mods/code/common/imitate_death.h', 'server-mods/code/zone/aa.cpp',
             'tools/tests/test_aa_cooldown_identity.py', 'eq-client-dll/tests/aa-reuse-native.cpp',
             'docs/releases/imitate-death-20261112/README.md',
             'docs/releases/imitate-death-20261112/wiki-review.json']
    entries = [dict(root=ROOT.as_posix(), path=p,
                    revision='feature/imitate-death-no-cooldown; main 423f9c3b + reviewed candidate',
                    role='Reviewed no-reuse Imitate Death source/test evidence; not deployed or player accepted',
                    sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()) for p in paths]
    manifest['topics']['multiclass'] = entries+[
        e for e in manifest['topics']['multiclass'] if e['path'] not in paths]
    manifest['observed_revisions']['imitate_death_candidate_20261112'] = entries[0]['revision']
    after[names[1]] = json.dumps(manifest, ensure_ascii=False, indent=2)+'\n'
    patch = ''.join(''.join(difflib.unified_diff(before[n].splitlines(True), after[n].splitlines(True),
                    fromfile='a/'+n, tofile='b/'+n)) for n in names)
    (OUT/'installed-skill.patch').write_text(patch, encoding='utf-8', newline='\n')
    if args.write:
        for n, text in after.items():
            (SKILL/n).write_text(text, encoding='utf-8', newline='\n')
    print('installed' if args.write else 'prepared')

if __name__ == '__main__':
    main()
