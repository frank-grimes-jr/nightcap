# Owner authorization — October 29, 2026

The owner first requested: "Remove all key requirements for locked doors."
They explicitly approved reading and saving production door definitions locally.
After the full production capture and inverse rehearsal passed and source was
merged through test PR369, the assistant asked:

> Approve promoting this door-only change to main, applying it to OVH with a
> brief restart if needed, and publishing the matching wiki update?

The owner replied: "Merge to prod an server".

This authorizes the scoped door release on main and OVH and its matching wiki
publication. It does not authorize sweeping other dev/test candidates into main
or claiming owner gameplay acceptance. No client change is required.

The selected activation preserves running services: take a fresh full backup,
verify all door preimages, briefly hold ordinary entry into empty Paineel using
the supported native zone lock, allow 125 seconds for pending authorizations to
expire, then apply the guarded SQL and reload that worker's static door data.
Other affected zones read the new values on their next normal load. Preserve
other native zone locks and remove only the Paineel hold after verification.
Any uncertain write/reload/unlock requires inspecting receipts before continuing.
