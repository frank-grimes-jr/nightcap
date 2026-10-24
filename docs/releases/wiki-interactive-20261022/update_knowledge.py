"""Prepare an exact, guarded update of the installed Nightcap wiki knowledge."""
from pathlib import Path
import argparse
import difflib
import hashlib
import json
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SKILL = Path('C:/Users/verre/.codex/skills/nightcap-development')
STAGE = HERE/'knowledge'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare():
    STAGE.mkdir(exist_ok=True)
    revision = subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    wiki = (SKILL/'references/wiki.md').read_text(encoding='utf-8')
    note = '''## Interactive handbook — October 22 published

Current public release is `20261022-interactive-handbook-v1`, following
`20261022-classic-dungeons-v1`. Source: E:/EQ_Local_Dev/_worktrees/wiki-interactive.
`wiki/experience.py` composes four paths from current article titles/summaries and
moves home notices intact into a native disclosure. `assets/experience.css` and
`experience.js` add dark/light reading, quick search (slash/Ctrl/Command+K), local
bookmarks, path URL/Back state, mobile navigation, progress and contents tracking.
The generator bundles them into the existing cache-versioned public CSS/JS files.
No packages, server accounts, client pairing or gameplay reload are needed.

All21 maintained guides/432 generated routes reviewed; gameplay Features, commands,
384 catalog values and native QA labels stay unchanged. About explains local
storage/shortcuts; Recent changes documents the UI. Existing release-note HTML and
anchors remain intact; deep links expand their disclosure. No-JS paths and article
links remain static. Storage accepts only safe local slugs and text; blocked
storage degrades to the page visit. Search loads only when used, retries failures
and rejects stale results. Recheck these contracts when changing the shell.

23 Python checks pass/9 POSIX-only skips locally,16 recovery checks pass on Linux,
6 search/7 equipment checks and the experience scenarios pass. Browser inspection
covered20 layouts at320/768/1024/1440, keyboard/Back/bookmark/theme/search/deep-link
flows with no overflow or console errors. All465 HTTPS hashes/security headers
and five private-route denials verify. The guarded update reproduces the previous
manifest first and rehearses pointer rollback, preserving config/private downloads
and service identities without reload. Evidence: docs/releases/wiki-interactive-20261022/.
Native gameplay/balance acceptance is unchanged. UI source is on its feature
branch; publication is independent of gameplay/main promotion. Future publishers
must preserve this release and reconcile its source before replacing the whole site.

'''
    wiki = wiki.replace('# Official player wiki and Features\n\n', '# Official player wiki and Features\n\n'+note, 1)
    begin = wiki.index('Live public URL: https://wiki.nightcapgame.org/features.html.')
    end = wiki.index('`update.py` holds', begin)
    wiki = wiki[:begin] + '''Live public URL: https://wiki.nightcapgame.org/. Current verified release is
`20261022-interactive-handbook-v1`; previous is `20261022-classic-dungeons-v1`.
The current publication/recovery evidence is in docs/releases/wiki-interactive-20261022/;
older dated sections retain historical scope. Runbook: docs/ops/nightcap-wiki.md;
maintenance: wiki/README.md. Native owner acceptance remains separately recorded.

''' + wiki[end:]
    manifest = json.loads((SKILL/'references/sources.json').read_text(encoding='utf-8'))
    entries = manifest['topics']['wiki']
    # Migrate the reviewed public generator/content surface, removing superseded duplicates.
    reviewed = {e['path'] for e in entries if e['path'].startswith('wiki/')}
    reviewed.update(['wiki/experience.py','wiki/assets/experience.css','wiki/assets/experience.js','wiki/test_experience.cjs',
                     'docs/ops/nightcap-wiki.md','docs/releases/wiki-interactive-20261022/README.md',
                     'docs/releases/wiki-interactive-20261022/verification.json','docs/releases/wiki-interactive-20261022/wiki-review.json',
                     'docs/releases/wiki-interactive-20261022/wiki-publication.json','docs/releases/wiki-interactive-20261022/wiki-public-verification.json'])
    entries[:] = [e for e in entries if e['path'] not in reviewed]
    for relative in sorted(reviewed):
        entries.append({'root':ROOT.as_posix(),'path':relative,'role':'Reviewed interactive wiki source, maintained content or verified release evidence',
                        'revision':revision+' + reviewed publication records','sha256':sha(ROOT/relative)})
    manifest['observed_revisions']['wiki_interactive_20261022'] = revision
    contents = {'wiki.md':wiki,'sources.json':json.dumps(manifest,ensure_ascii=False,indent=2)+'\n'}
    preimages = {}
    patch = []
    for name, text in contents.items():
        target = SKILL/'references'/name
        preimages[name] = sha(target)
        (STAGE/name).write_text(text,encoding='utf-8')
        patch.extend(difflib.unified_diff(target.read_text(encoding='utf-8').splitlines(True),text.splitlines(True),fromfile='a/references/'+name,tofile='b/references/'+name))
    (STAGE/'knowledge.patch').write_text(''.join(patch),encoding='utf-8')
    (STAGE/'preimages.json').write_text(json.dumps(preimages,indent=2)+'\n',encoding='utf-8')
    print('Prepared exact wiki knowledge patch and reviewed fingerprints')


def apply():
    preimages = json.loads((STAGE/'preimages.json').read_text(encoding='utf-8'))
    for name, expected in preimages.items():
        assert sha(SKILL/'references'/name) == expected, 'Concurrent skill edit; regenerate and review'
    for name in preimages:
        (SKILL/'references'/name).write_bytes((STAGE/name).read_bytes())
    (STAGE/'receipt.json').write_text(json.dumps({'result':'APPLIED','files':{name:sha(SKILL/'references'/name) for name in preimages}},indent=2)+'\n',encoding='utf-8')
    print('Installed wiki knowledge and fingerprint update applied')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply',action='store_true')
    args = parser.parse_args()
    apply() if args.apply else prepare()
