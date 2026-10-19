# 0064: Observed THJ item and spell parity

Date:2026-10-18. Status: implemented candidate; owner gameplay QA pending.

The owner requested THJ Legendary-equivalent Ascension gear and close spell
scaling, including reductions and coordinated pet/WPM changes. The152-page forum
and linked workbooks contain per-item variation and conflicting transcriptions;
the old universal multiplier and flat20 SD/HA cannot represent them accurately.

Use a reviewed per-identity numeric catalog for131 observed Ascended definitions.
Clean screenshots override conflicting workbook cells; defer unresolved fields,
ambiguous identities and below-Normal inversions. Preserve unobserved fields and
effect identities. Normal ordinary gear stays native; intermediate stats only
cap at the supported top. The separate209-family starter exception preserves
small earned steps below Normal dungeon rewards. Compiler and migration share
the reviewed policy; destructive bootstrap is never the live update path.

Add effective SD to direct player/permanent-pet damage; add half SD to each
ordinary DoT tick. Keep percentage HA/HoT behavior until evidence resolves it.
Use a separate0.1% heroic INT/WIS direct-value modifier; no periodic or owner
heroic transfer. Apply it after existing modifiers and before caps, honor item
opt-outs and preserve Throw Stone's single additive path. Critical DoT ordering,
Bard area-DoT dispatch and unobserved proc/rune tuning remain explicit limits.

One full-row guarded transaction owns existing item changes across pet, WPM,
parity and starter/dungeon systems. Recovery preserves new effects/sockets and
earned state. Separate new-content migrations remain independently retryable;
they do not wrap the entire bundle in one transaction. Both new spell rules
default false and are independently enabled by reviewed SQL.

This changes relative build power: larger direct spells can lose damage while
small spells/DoTs gain; selected weapon damage rises and oversized pools fall.
Validate actual combined encounters and resources rather than raising NPC HP
as the only compensating lever. Source, native fixtures, build/cache/client
pairing, recovery and owner checks: `docs/releases/thj-parity-20261018/`.
