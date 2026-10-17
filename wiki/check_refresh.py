"""Fail when player-facing source changed since the wiki's recorded review.

This detects review work; it cannot decide whether deployed behavior changed.
It never edits content or advances the reviewed revision.
"""
import argparse
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args], text=True).strip()


def changed_sources(repo, review, ref, working_tree=False):
    base = git(repo, 'rev-parse', '--verify', '--end-of-options', review['reviewed_revision']+'^{commit}')
    target = git(repo, 'rev-parse', '--verify', '--end-of-options', ref+'^{commit}')
    scopes = review['source_paths']
    changed = set(git(repo, 'diff', '--name-only', base, target, '--', *scopes).splitlines())
    if working_tree:
        changed.update(git(repo, 'diff', '--cached', '--name-only', target, '--', *scopes).splitlines())
        changed.update(git(repo, 'diff', '--name-only', target, '--', *scopes).splitlines())
        changed.update(git(repo, 'ls-files', '--others', '--exclude-standard', '--', *scopes).splitlines())
    return sorted(changed)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=ROOT.parent)
    parser.add_argument('--ref', default='origin/main', help='Current source authority, not necessarily this wiki branch')
    parser.add_argument('--include-worktree', action='store_true', help='Also inspect staged, unstaged and untracked source in --repo')
    args = parser.parse_args()
    review = json.loads((ROOT/'content-review.json').read_text(encoding='utf-8'))
    try:
        changed = changed_sources(args.repo, review, args.ref, args.include_worktree)
    except (OSError, subprocess.CalledProcessError) as error:
        parser.exit(2, 'Unable to compare source revisions; wiki review is not verified.\n')
    print(json.dumps({'result':'REVIEW REQUIRED' if changed else 'NO SOURCE DRIFT',
                      'reviewed':review['reviewed_at'], 'source_ref':args.ref,
                      'changed_sources':changed,
                      'note':'Also inspect current deployment/owner evidence and changes outside Git. No automatic approval or publication.'}, indent=2))
    return 1 if changed else 0


if __name__ == '__main__':
    raise SystemExit(main())
