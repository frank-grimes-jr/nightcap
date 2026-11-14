# Heroic spell damage and healing on the official wiki

**Staged for publication.** Release `20261114-heroic-cast-sources-v1` updates Combat, Equipment, Change Log and search. This package has no public publication authorization. The official site serves `20261113-archery-backstab-v2`. [Candidate and hashes](candidate.json) · [Current public release check](predecessor-https.json).

The guides explain the 0.1% direct damage bonus per heroic INT and direct healing bonus per heroic WIS on spell gem casts and activated AA spells. They distinguish item Spell Damage and Healing Amount from those heroic multipliers. A proc firing during an eligible cast uses its own origin. The Combat guide retains its bow and Backstab sections. The public Equipment guide keeps its existing item and augment values. [Wiki impact](source-review.json) · [Gameplay QA](../../../combat/thj-heroic-casts/QA.md).

## Reproduction

From the integration checkout, run `python -B -X utf8 docs/releases/heroic-cast-sources-20261114/wiki/prepare.py`. For an unmerged candidate, append `--articles-from E:/EQ_Local_Dev/_worktrees/thj-heroic-casts/wiki`. The builder authenticates the preceding official manifest and reproduces every file. It copies the reviewed corrections into the previously published article text. Exactly four files change, and the 627 others retain their bytes. The immutable archive, manifest and next-release source are under `artifacts/heroic-cast-sources-wiki` in this checkout.

All 38 applicable Windows Python checks passed. Linux passed all ten loot-refresh checks, including the eight POSIX-only cases. Five Node suites passed, including the Build Lab test for resolved effects and its twelve landed-spell controls. The calculator takes proc and skill damage as entered. Its spell formula and data files keep their published hashes. Browser rendering and in-game observations are separate from these checks.

The predecessor passed all 631 public HTTPS file checks, the site root, both versioned assets and five private-path denials. Its rollback manifest is `/opt/nightcap/deploy/production/website-history/20261113-archery-backstab-v2/manifest.json`. Any future publication must recheck the live predecessor at that time and use the guarded wiki updater.
