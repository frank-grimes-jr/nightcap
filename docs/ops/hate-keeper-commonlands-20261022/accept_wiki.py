"""Update the reviewed public wiki wording after scoped owner acceptance."""
import json
import subprocess
from pathlib import Path

WIKI = Path('E:/EQ_Local_Dev/_worktrees/hate-keeper-wiki')
ARTICLES = ['dungeon-modes', 'tunnel', 'travel', 'features', 'index', 'unreleased', 'recent-changes']
OLD_NOTICE = 'In-game visibility, travel and gameplay acceptance remain open.'
NEW_NOTICE = ('The owner confirmed the relocation, Commonlands visibility and Hate travel. '
              'Broader dungeon balance and full-clear QA remain separate.')
OLD_SOURCE = 'main PR299 and live server verified; owner gameplay acceptance open'
NEW_SOURCE = ('main PR299 and live server verified; owner confirmed relocation, '
              'Commonlands visibility and Hate travel; broader dungeon balance/full-clear QA separate')
OLD_REVIEW = ('Hate Keeper relocation: owner-authorized main PR299/a736fb0 and paired live server release verified; '
               'all12 workers and39 schema/499 content checks passed. All22 guides/432 generated routes reviewed; '
               'seven guides plus search updated for live placement, level46 and private Keeper continuity.384 Hunt '
               'catalog values, commands, Build Lab and handbook preserved. Owner native QA open. Source/deployment '
               'evidence in hate-keeper-commonlands checkout, docs/ops/hate-keeper-commonlands-20261022/.')
NEW_REVIEW = ('Hate Keeper relocation: owner-authorized main PR299/a736fb0 and paired live server release verified; '
              'all12 workers and39 schema/499 content checks passed. All22 guides/432 generated routes reviewed; '
              'seven guides plus search updated for live placement, level46 and private Keeper continuity.384 Hunt '
              'catalog values, commands, Build Lab and handbook preserved. Owner confirmed relocation, Commonlands '
              'visibility and Hate travel; broader dungeon balance/full-clear QA remains separate. Source/deployment '
              'evidence in hate-keeper-commonlands checkout, docs/ops/hate-keeper-commonlands-20261022/.')


def revision():
    return subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=WIKI, text=True).strip()


def main():
    changed = []
    for slug in ARTICLES:
        path = WIKI / 'wiki' / 'articles' / f'{slug}.json'
        data = json.loads(path.read_text(encoding='utf-8'))
        body = data['body']
        assert body.count(OLD_NOTICE) == 1, (slug, body.count(OLD_NOTICE))
        data['body'] = body.replace(OLD_NOTICE, NEW_NOTICE)
        data['sources'] = [source.replace(OLD_SOURCE, NEW_SOURCE) for source in data['sources']]
        assert any('hate-keeper-commonlands-20261022' in source and 'owner confirmed relocation' in source
                   for source in data['sources']), slug
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        changed.append(str(path.relative_to(WIKI)))

    review_path = WIKI / 'wiki' / 'content-review.json'
    review = json.loads(review_path.read_text(encoding='utf-8'))
    assert OLD_REVIEW in review['supplemental_evidence']
    review['supplemental_evidence'] = [NEW_REVIEW if value == OLD_REVIEW else value
                                       for value in review['supplemental_evidence']]
    review['reviewed_revision'] = revision()
    review_path.write_text(json.dumps(review, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    changed.append(str(review_path.relative_to(WIKI)))

    runbook = WIKI / 'docs' / 'ops' / 'nightcap-wiki.md'
    text = runbook.read_text(encoding='utf-8')
    old = 'native owner visibility/travel/gameplay acceptance remains open.'
    new = ('owner confirmed relocation, Commonlands visibility and Hate travel; '
           'broader dungeon balance/full-clear QA remains separate.')
    assert text.count(old) == 1
    runbook.write_text(text.replace(old, new), encoding='utf-8')
    changed.append(str(runbook.relative_to(WIKI)))
    print(json.dumps({'changed': changed, 'count': len(changed), 'base_revision': revision()}, indent=2))


if __name__ == '__main__':
    main()
