# Owner authorization — November 21, 2026

After reviewing the built candidate and PR515, the owner instructed:

> Push to main and server

This authorizes this AA purchase latency fix's main promotion and production
server deployment for live testing, including the supported brief admission
drain and whole-game runtime restart. It is specific to this fix and does not
record that the visible freeze or gameplay QA has passed. Preserve other current
server content, native binaries, caches, client delivery and player progress.
The normal dev/test route has older cooldown dependencies; this explicit main
instruction approves promotion of the reviewed current-main-based candidate.
Wiki release notes are maintained as part of the deployment; player acceptance
remains OPEN until the owner reports the result of the in-game retest.
