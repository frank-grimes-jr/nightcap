"""Record deployment/publication only after their independent proof files exist."""
import json
from pathlib import Path
from control import ROOT,HERE

live=json.loads((HERE/'production-verified.json').read_bytes())
wiki=json.loads((HERE/'wiki-public-verification.json').read_bytes())
repair=json.loads((HERE/'palwar-correction.json').read_bytes())
assert live['result']==wiki['result']==repair['result']=='PASS'
assert live['gateway_open'] and live['workers']==12 and live['title_catalog_enabled']
assert wiki['release']=='20261114-titles-active-v1' and wiki['files']==631


def replace(name,old,new):
    p=ROOT/name;text=p.read_text(encoding='utf8');assert text.count(old)==1,(name,old)
    p.write_text(text.replace(old,new),encoding='utf8',newline='\n')


replace('docs/titles/deployment-20261114/README.md','**Prepared; production\nactivation pending.**',
    '**Active on production; all twelve open workers verified.**\n[Runtime verification](production-verified.json) · [Activation proof](activation-summary.json) ·\n[Published guide checks](wiki-public-verification.json). Native visible player QA remains OPEN.')
replace('docs/titles/deployment-20261114/README.md',"The linked shipping candidate `f35b4e3d` reproduces the running fixed-AA `82d5e2d2`",
    'The linked shipping zone `f35b4e3d` reproduces the previous fixed-AA `82d5e2d2`')
replace('CHANGES.md','## November 14, 2026 · Titles live activation package\n\nPrepared the 77-title native release over the reproduced current production binary, with strict additive storage and a public `#titles` command. Batched kill credit bounds ordinary group/raid work to four SQL statements. Tested stopped-backup activation and data-preserving recovery; live activation and native player acceptance are recorded separately in [release evidence](docs/titles/deployment-20261114/README.md).',
    '## November 14, 2026 · Earned titles active\n\nActivated 77 permanent cosmetic titles and public `#titles` on all twelve production zone workers. Qualifying kills, skill mastery, personal dungeon clears and campaign completion earn titles; new general kill totals start at activation. Restored only Palwar’s independently logged Nagafen victory for Flamebreaker. The public wiki now documents availability and requirements. The initial pre-SQL stopped-world RPC hold was resolved with a reviewed bounded continuation and fresh backup; no player snapshot restore. [Runtime, wiki proof and open native player QA](docs/titles/deployment-20261114/README.md).')
replace('docs/status.md','Owner-authorized live package is built and reviewed; production activation pending. It preserves the current fixed-AA native build and completed prismatic data release. [Evidence and exact in-game QA](titles/deployment-20261114/README.md). Main/wiki preview publication did not previously activate title counting.',
    'Active and verified on all twelve open production workers, main PR475/b824e0d2. Catalog1 is enabled and `#titles` is public. Signed client2026111301 and the completed prismatic baseline are preserved. Palwar’s logged Nagafen victory received named-only credit; opening Titles/#titles reconciles Flamebreaker. The current public guide is published and verified. Native visible picker/nameplate/notification acceptance remains OPEN. [Evidence, incident resolution and exact player QA](titles/deployment-20261114/README.md).')
replace('docs/titles/SPEC.md','This implementation is a disabled candidate, not a live\nrelease or a record of player acceptance.',
    'This contract was implemented on November12 and activated on production on\nNovember14. [Current release evidence](deployment-20261114/README.md) records\nruntime/wiki verification separately from open native player acceptance.')
replace('docs/titles/QA.md','Status: OPEN. Use an ordinary account with status0/GM off in the test environment.',
    'Status: OPEN. Live checks use an ordinary account with status0/GM off on the\n[verified November14 release](deployment-20261114/README.md). Control-row toggles,\nsynthetic data and failure simulations belong only in an isolated test environment.')
replace('docs/titles/QA.md','1. Enable the reviewed candidate in the isolated environment. Open the native',
    '1. Use the already enabled live catalog for normal-player checks; isolate\n   enable/disable and failure controls. Open the native')
replace('docs/titles/QA.md','9. Disable the control row:', '9. In isolated QA only, disable the control row:')
readme='''# Earned titles

The 77 cosmetic titles are active on production as of November 14, 2026. Main
PR475/b824e0d2 deploys zone f35b4e3d with catalog 1 enabled and public `#titles`.
All twelve workers, backup/native saved-state preservation, existing content,
caches and signed client 2026111301 pairing verify with open access. Native
RoF2 picker/nameplate/notification acceptance remains OPEN.

[Release, verification and incident resolution](deployment-20261114/README.md) ·
[Player guide](https://wiki.nightcapgame.org/titles.html) · [Exact player QA](QA.md) ·
[Contract](SPEC.md). The current wiki release is 20261114-titles-active-v1,
verified across all 631 HTTPS files. The November 12 main/wiki preview did not
activate titles; its historical evidence remains in wiki-release/.

New general slayer totals start at activation. Existing personal clear, story,
level and skill goals reconcile when opening Titles or using `#titles`. Nagafen
earns Flamebreaker; Nagafen and Vox together earn Dragonslayer. Palwar's earlier
kill is independently logged; the scoped repair restores only named counter100.
He should open Titles/#titles for native award reconciliation. No direct award,
generic kill totals or worn-title profile was changed by that repair.

Reproduce local checks from this checkout:

```powershell
python -B tools/earned_titles.py --check
python -B -m unittest discover -s tools/tests -p test_earned_titles.py -v
python -B docs/titles/deployment-20261114/test_release.py -v
python -B docs/titles/deployment-20261114/test_resume.py -v
python -B docs/titles/deployment-20261114/test_wiki_publication.py -v
```

Use the title-only shipping delta/build proof over the authenticated current
binary; newest main's full native files can contain unshipped work. No quest,
rule, cache, Client layout or client update is required for titles. Never kill
one production zone worker. Preserve every award/counter and stable ID during
forward recovery. Never replay terminal rollout/publication actions or restore
an old player snapshot. See the current release README before any operation.
'''
(ROOT/'docs/titles/README.md').write_text(readme,encoding='utf8',newline='\n')
replace('docs/README.md','# Nightcap documentation\n',
    '# Nightcap documentation\n\n- [Earned titles: live activation, published guide, incident resolution and open player QA](titles/deployment-20261114/README.md)\n')
path=ROOT/'docs/titles/wiki-impact.md';text=path.read_text(encoding='utf8')
path.write_text('''# Current title wiki impact · November14

The631-file public archery/Backstab source reproduced exactly. Title availability,
command use, combat counting date, campaign reconciliation and Change Log/search
were updated in six outputs;625files retain exact bytes. All631HTTPS hashes and
headers and five private denials verify. Current source, publication, rollback
and service/config/client guards: [deployment evidence](deployment-20261114/README.md).

Whole-wiki review: Titles owns77exact requirements; existing Features and owning
dungeon/skill/craft links already describe the same catalog. Home's published
goal paths need no release notice. In development preserves its old anchor.
No item/zone/catalog/acquisition values, generated reward pages, Build Lab or
Loot Finder behavior change. Current-main authored context is aligned without
republishing that stale mirror. Global historical source drift remains REVIEW
REQUIRED; no ledger advance. Native picker/nameplate/notification QA stays OPEN.

## Historical November12 source/publication review

'''+text,encoding='utf8',newline='\n')
path=ROOT/'docs/ops/nightcap-wiki.md';text=path.read_text(encoding='utf8')
text=text.replace('Updated November 13, 2026.','Updated November 14, 2026.',1)
start=text.index('The official wiki serves');end=text.index('\n## Retained hosting snapshots',start)
text=text[:start]+'''The official wiki serves `20261114-titles-active-v1` over `20261113-archery-backstab-v2`.
Titles, commands, Combat, Adventure Journal, Change Log and search describe active
earned titles. Six outputs change and625retain exact bytes after current-source
reproduction. All631public HTTPS hashes/headers and five private denials verify.
The publisher rechecks live title enablement under the shared deployment lock,
rehearses rollback and preserves all services/config/client. Native player QA
remains open. [Current source and recovery](../titles/deployment-20261114/README.md) ·
[Public verification](../titles/deployment-20261114/wiki-public-verification.json).
'''+text[end:]
path.write_text(text,encoding='utf8',newline='\n')
print('Runtime, repair, wiki, QA and operational documentation updated from real proof')
