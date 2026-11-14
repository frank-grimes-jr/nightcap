# Earned titles

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
