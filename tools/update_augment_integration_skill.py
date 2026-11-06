"""Maintain the installed knowledge boundary after source-only dev/test promotion."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = Path('C:/Users/verre/.codex/skills/nightcap-development/references')
OUT = ROOT / 'docs/audits/augments-20261106/skill-update'
TEST = '5257586a329ae238ba054511b8a9270b1b4a163f'
DEV = 'c1c5e09bcd4f84b74e84a16668edcf20c159ebd1'


def replace_once(text, old, new):
    assert text.count(old) == 1, old
    return text.replace(old, new, 1)


def main(apply):
    before = {n: (SKILL / n).read_text(encoding='utf-8') for n in ('items.md', 'wiki.md', 'sources.json')}
    after = {}
    after['items.md'] = replace_once(before['items.md'],
        'This is a linked local candidate, no production content writes, MAIN/OVH promotion,\npublic wiki publication or player acceptance.',
        f'Source is promoted through TEST: dev PR404/{DEV[:8]}, test PR405/{TEST[:8]}.\nBoth fetched remote trees equal the tested integration e1570848 tree. Integration:\n{ROOT.as_posix()}; promotion.json records exact pins.\nAll native/quest source matches the linked release-base candidate. Existing\ncapacity configuration/previews remain unchanged and are NOT activated or part\nof augment-only approval.51integration checks pass; two historical opt-in DB\nfixtures skip (the current full SQL has its separate successful rehearsal).\nThis remains an undeployed candidate: no production content writes, MAIN/OVH,\npublic wiki publication or owner gameplay acceptance. Named guard QA includes\nHigh Keep Guard Heltch6000/Golgon6001 and Qeynos Hills Guard Yalroen4048; verify\nactive QA-zone spawns. Full nine-part QA is in test PR405. Goal continuation is\nnot approval. Context topic augment-integration owns promotion/preview pins.')
    start = before['wiki.md'].index('## Zone augment audit — November6 unpublished preview')
    end = before['wiki.md'].index('\n## ', start + 4)
    section = before['wiki.md'][start:end]
    section = replace_once(section, 'All41authored articles and generated item/zone impacts are assessed in',
        'The release-base review covers41authored articles; integration covers46,\nincluding five historical Hate B previews. Source is through TEST via PR404/405\n(c1c5e09b/5257586a), with remote tree equality verified. It supersedes October29\naugment wording and preserves existing capacity previews and old anchors.\n51integration checks pass (two historical opt-in DB skips);22wiki checks pass.\nNo main/OVH or public publication; all candidate/live labels remain distinct.\nWhole-wiki/generated item/zone impacts are assessed in')
    after['wiki.md'] = before['wiki.md'][:start] + section + before['wiki.md'][end:]
    manifest = json.loads(before['sources.json'])
    manifest['observed_revisions']['augment_audit_dev_20261106'] = DEV
    manifest['observed_revisions']['augment_audit_test_20261106'] = TEST + ' (source only; not deployed or owner accepted)'
    paths = ['docs/audits/augments-20261106/integration.json', 'docs/audits/augments-20261106/promotion.json',
             'docs/audits/augments-20261106/wiki-review.json', 'wiki/catalog.py',
             'wiki/articles/features.json', 'wiki/articles/unreleased.json',
             'wiki/articles/recent-changes.json', 'wiki/articles/zone-hunt.json',
             'tools/record_augment_integration.py', 'tools/resolve_augment_integration.py']
    manifest['topics']['augment-integration'] = [dict(root=ROOT.as_posix(), path=p,
        role='Reviewed augment TEST source promotion/preview; no main/OVH, capacity activation, publication or player acceptance',
        revision=TEST + ' plus reviewed promotion evidence', sha256=hashlib.sha256((ROOT / p).read_bytes()).hexdigest()) for p in paths]
    after['sources.json'] = json.dumps(manifest, indent=2) + '\n'
    patch = ''.join(''.join(difflib.unified_diff(before[n].splitlines(True), after[n].splitlines(True),
        fromfile='a/references/' + n, tofile='b/references/' + n)) for n in after)
    OUT.mkdir(exist_ok=True)
    (OUT / 'test-promotion.patch').write_text(patch, encoding='utf-8')
    if apply:
        for name, content in after.items():
            (SKILL / name).write_text(content, encoding='utf-8', newline='\n')
    print(json.dumps({'status': 'applied' if apply else 'prepared', 'source_test': TEST, 'reviewed_entries': len(paths)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    main(parser.parse_args().apply)
