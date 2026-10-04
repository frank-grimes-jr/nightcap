# 0054: Use local client outlines for NPC placement maps

Date: 2026-10-04
Status: implemented

## Intent and decision

Make configured NPC locations understandable in their zone without requiring a
3D renderer. NPC Admin reads the owner's existing client map text files from an
explicit local folder. A read-only endpoint returns validated line/label records
for a zone and optional layers 1–3. No client asset or credential enters Git.
Missing maps retain a coordinate view; version-specific aliases are explicit.

The view preserves equal X/Y scale and converts world coordinates to client map
coordinates as `(-X, -Y)`. `/loc` remains `Y, X, Z`. One zone/version is shown at
a time, with current circles and staged diamonds. Only drafts belonging to the
browsed target contribute overlays. Pan/zoom and Z clipping are presentation
controls; editing continues through the existing draft/review/apply path.

## Alternatives and limits

1. Coordinate-only plotting is small but lacks room and landmark context.
2. Local client outlines (chosen) are available now and inexpensive to render.
3. Collision mesh or textured 3D rendering offers vertical context but requires
   separate decoding, camera and asset-version work.

Client labels can be stale; layers are not floors. Map files do not prove ground
clearance or pathing and do not show roaming NPC positions or quest-only actors.
The user must match maps to the actual client/era. The reader validates names,
confines real paths, bounds reads/record counts, and retains at most four maps.

Acceptance: parser/security and coordinate tests, production build, browser
checks for maps/markers, staged moves, zoom/pan, height filtering, missing-map
fallback and narrow layouts. Live access is read-only; no gameplay deployment.
