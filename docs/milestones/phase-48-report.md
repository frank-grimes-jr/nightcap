# Phase 48 — NPC location maps

Date: 2026-10-04. Local utility enhancement; no gameplay deployment.

## Built

Client-map text reader, bounded cache and read-only local endpoint; configurable
folder and zone/version aliases. Zone outlines, optional labels/layers, clickable
spawn markers and picker, current/staged movement overlay, equal-scale pan/zoom,
fit controls, keyboard pan and height clipping. Missing maps explain the fallback.
Draft overlays are restricted to the browsed source target.

## Verification

Twenty Node tests and the Vite production build pass. Map tests cover known PoK
coordinate alignment, cursor-anchored zoom, crossing-floor segment clipping,
version-scoped staged positions, malformed records, layers, aliases, cache refresh,
missing folders/files, path traversal, size limits and HTTP input validation.
Independent review found no blocking reader/security regression; its floor-fit,
label-only-layer and cross-target overlay findings were addressed.

Browser verification covers the existing local swashbuckler draft without
modifying it: current and staged markers, correct /loc values, zoom, keyboard pan,
height hiding and 320px layout without document overflow. OVH browsing is read-only.
See the current map acceptance checklist in `eq-npc-admin/QA.md`.

## Cut and remaining limits

No 3D renderer, collision/ground validation, live movement feed, all-zone NPC
aggregation or drag-to-write placement. Only the selected NPC's database spawns
are shown. Missing/era-mismatched client maps need owner-supplied files or aliases.
In-game placement acceptance remains separate from this display-only enhancement.
