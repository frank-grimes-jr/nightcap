# Installed Nightcap knowledge update

`refresh.py --apply` updates world/items/wiki and reviewed source fingerprints,
retaining unrelated release and parallel candidate entries. `knowledge.patch`
records the exact installed delta and `receipt.json` records output hashes.

Skill validation passes. Every entry in `scoped-fingerprints.json` is unchanged
in the recorded check. Full items validation passes; world/wiki still flag
separate Classic-dungeon, robe and armor worktree changes. Those sources were
not blindly re-fingerprinted. See the full topic reports for their exact paths.

The reference distinguishes tested source, the compiled candidate, promotion,
production activation, public wiki release and owner in-game acceptance.
