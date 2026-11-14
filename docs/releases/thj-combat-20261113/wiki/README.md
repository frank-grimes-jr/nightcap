# Archery and Backstab on the official wiki

**Published and verified.** The owner approved `20261113-archery-backstab-v2` for the official Nightcap wiki. All 631 files matched the approved manifest over public HTTPS on November 13 at 10:08 p.m. Eastern. Both versioned assets passed, and all five private paths returned 404. The publisher rehearsed rollback and preserved the running services. [Origin publication](publication.json) · [Public verification](public-verification.json).

The Combat guide explains ordinary bow shots, the Heroic Dexterity curve, the two mastery AAs and the Ranger level gate. It also explains which one-handed piercing weapon Backstab selects, how dual wield affects the secondary hand, and what happens when both weapons give equal expected damage. Features and Change Log link directly to each section.

The authenticated public predecessor is `20261113-sympathetic-clicks-v1`, which already includes the simplified wiki layout and language. The build starts from its retained public source and reproduces all 631 files before applying the two changes. Correct publication changes four files. Combat, Features, Change Log and the search index carry the new text. The other 627 files retain their bytes. See [review scope](source-review.json), [public predecessor checks](predecessor-https.json) and [candidate hashes](candidate.json).

The [builder](prepare.py) uses the reviewed article sections in this checkout. During integration, `--articles-from PATH_TO_WIKI` can build them from the matching feature checkout. The retained public source for a later release is in `artifacts/thj-combat-wiki/wiki-source` under this release checkout. The package includes the public HTML and assets. QA records and source metadata remain private.

The final candidate `20261113-archery-backstab-v2` passed all 38 applicable Windows Python checks. Linux passed all 10 loot refresh tests, including the eight symlink and recovery cases skipped on Windows. The Node search, equipment, loot finder and handbook checks passed. Version 1 was an unpublished draft. The release changes page content only.

After the game deployment verifies an open gateway, [publish.py](publish.py) checks the actual running image, game receipt, signed client channel and prior wiki manifest. The content updater verifies every origin file and rehearses rollback under the shared lock. [verify_public.py](verify_public.py) checks the canonical HTTPS root, every versioned asset, other public files and five private paths. Player gameplay QA remains separate from wiki publication.
