# Installed Nightcap knowledge update

Applied October 22 to the installed `nightcap-development` skill after reviewing
candidate d107f901fbf637933f40c86b1ddd0ff819438bce. The guarded installer required
all three exact preimages before writing items.md, wiki.md and sources.json.
`installed-skill.patch` retains the exact change; `prepared.json` records verified
before/after hashes and final installed status.

The update replaces the blanket repeatable-quest exclusion with the owner's
clarification, describes the 37-reward candidate and Kurron dependency, records
native/reload/cache/owned-state boundaries, and preserves unpublished/unaccepted
labels. Thirty-two newly reviewed source/evidence fingerprints match.

The creator's quick validator passed. The complete items topic has no drift.
The wiki topic's eight new entries match; four entries belonging to the concurrent
waypoint work correctly report drift and were not silently re-approved. Exact
results are in `items-validation.json` and `wiki-validation.json`.
