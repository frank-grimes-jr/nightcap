# Phase 26 — Silent UI synchronization

The owner's login report showed our automatic UI requests as visible Say lines.
The proxy now submits class/AA refresh and pet armor requests through the verified
native packet sender, avoiding the interpreter and local echo/history. Server
validation and item transactions are unchanged. No gameplay scope was added.

Native ABI/ASLR review, exact-client guards, x86 build, transport and existing
runtime tests pass. Both Go suite configurations and the Windows launcher build
pass. Signed release 2026091906 uses proxy 0.4.2 and the repaired 1905 skin assets.
[Delivery, remaining manual QA and rollback](../releases/client-silent-ui-20260919.md)
are recorded in the release guide. Automated initialization cannot establish
character-level visual acceptance; that remains explicitly pending.
