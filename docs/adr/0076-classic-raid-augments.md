# 0076: Classic raid trophies share a chest socket

Accepted candidate design, November 12, 2026.

Use the existing chest-only type-22 socket for dragon, planar and capstone trophies. Their combat budget includes the Hunt augment displaced from the chest. Preserve standard per-item LORE for precisely the sixteen allocated IDs in the shared loader. A shared LORE group would prevent collecting different trophies. One timer per character covers all three capstone effects across swaps and reconnects. Record the timer before granting a benefit. Round the persisted whole-second deadline upward to preserve the 90-second minimum across zone changes. Keep loot separate from ordinary quality, gear and personal final-reward rolls. Validate managed Raid eligibility before staging a shared item for the existing corpse receipt.
