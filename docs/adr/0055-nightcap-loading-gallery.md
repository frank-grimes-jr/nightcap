# 0055: Replace RoF2's native loading gallery through signed assets

Accepted October 4, 2026 for the owner's requested main/server publication.

RoF2 reads a resource fallback and enumerates 55 stock JPEG loading images in
the default UI tree regardless of the active skin. Replacing only a Nightcap
skin asset would leave the stock artwork visible. A runtime hook would introduce
unnecessary binary/version dependencies for an asset-only behavior.

Replace all 56 known paths with the ten approved paintings, cyclically assigned,
preserving their full frames as baseline RGB JPEGs. Admit only those exact paths
through the existing signed asset protocol. Require desktop 0.4.0, delivered
through the existing stable starter, before installing this expanded inventory.
Keep the legacy recovery inventory and all user settings protected.

New artwork and launcher bytes are uploaded; the prior 48 client files are
reused on OVH after verifying their signed hashes. Publish immutable files before
the launcher and game channels, retain preimages, and use higher signed release
counters for rollback. No database or game-service change is required.

Verification and native visual-check scope:
[release record](../releases/loading-screens-20261004.md).
