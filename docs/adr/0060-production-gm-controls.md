# 0060: Owner-local GM controls for production

Date: 2026-10-10. Status: production GM activated after owner approval; the separate
credential gateway rollout remains pending.

## Intent

The owner explicitly requested a graphical alternative to server commands for
issuing/revoking player access codes, password resets and the full existing GM
feature set. Keep local development and OVH production clearly distinguishable.
The earlier IP-independent launcher/gateway candidate remains part of the release;
this extends its operator experience rather than changing player authentication.

## Architecture and boundaries

Run the GM UI/API on the owner's computer, bound only to loopback. Serve the built
UI from that origin; development uses a fixed loopback Vite proxy. Validate Host,
Origin and fetch metadata and require a per-process owner-session token on API
calls, held only in browser memory. Untrusted web pages cannot acquire that token
through CORS or DNS rebinding. No public admin or database port is introduced.

Every request names an allowlisted environment; routers and database connections
capture it independently. Never switch a global database pool. On target changes,
clear selections and discard stale responses; prevent switching during mutations.
Production labels and action confirmations show the affected account/character.

Use the owner's saved OpenSSH identity and pinned known host for SSH. Database
streams travel over SSH, without publishing MariaDB. Read production credentials
only into backend memory; they never reach the browser, logs or command arguments.
A bounded, fixed-operation helper handles private registry operations, password
mode inspection, backups and runtime state. The owner-local backend creates the
compatible scrypt hash even while the game is stopped. No browser-provided SQL,
shell command or file path.

## Compatibility corrections required before writes

- Replace MD5 resets with the production mode14/libsodium scrypt format and
  source-qualified, exactly-one-account updates. Never expose existing hashes.
- Back up affected data before destructive operations and use transactions for
  multi-row updates. Preserve mutation identity across retries; ambiguous outcomes
  require inspection, never blind replay of currency/AA grants. A private, stable
  HMAC key preserves receipt identity across backend restarts. Browser Web Locks
  serialize mutations across tabs; nonsecret pending IDs survive reload.
- Live native saves overwrite offline character edits. Require authoritative
  maintenance/offline protection for DB-based character mutations; a checkbox or
  stale timestamp is insufficient. Persist maintenance ownership and fence SQL
  connections against runtime resume; lease loss destroys the writer connection.
  Surface this requirement in the UI. Production
  supervision restarts the whole game when any zone exits: no zone-kill shortcuts.
- Select canonical zoneidnumber/version0 and clear instance state when teleporting.
- Scope typed rules to the active ruleset and a supported allowlist. Exclude
  declarative era-owned rules; distinguish saved state from runtime reload.
- Use held multiclass eligibility and preserve existing higher valid skill values.
- Reject account deletion while it owns characters; qualify the login namespace,
  preserve ownership and apply related deletes atomically.
- Capture one immutable character/environment for progression batches and apply
  each batch atomically; do not swallow failures or claim partial success as success.
- Do not create schemas merely by opening the application or selecting production.
  Any required support schema uses an explicit versioned setup operation.
- Era changes continue through committed era.json and catalog/activation guards.
  Existing direct-SQL era apply is unsafe and must be replaced by the declarative
  plan/apply workflow. Unsupported catalogs remain a real policy gate, not a
  successful no-op. Local client settings must use a permitted client copy, never
  modify Client_RoF2_Dev, and must never imply changing other players' clients.
- The retired vendor refresh must report its actual status and use the reviewed
  canonical restock workflow; do not resurrect the old delete/rebuild algorithm.

## Delivery and evidence plan

1. Build/test the SSH and local browser boundaries and prove production read access
   without mutating live data. Handle unavailable SSH/DB with actionable UI errors.
2. Add access-code lifecycle and account reset UI; test against disposable registry
   and DB fixtures, including rejection, namespace targeting and secret handling.
3. Complete existing character/rule/progression/era/client capabilities with the
   corrected semantics above. Test wrong target, stale selections, duplicate
   submissions, partial failures, backup failure and authoritative offline guards.
4. Browser-test and inspect local/production views, empty/error states and keyboard
   workflows. Independently review the security-sensitive implementation.
5. Package a one-click owner entry point. Follow feature → dev → test promotion,
   retain main/production sign-off and Cloudflare gates, and provide exact QA and
   rollback. No real player's password, currency, level or location changes during
   verification unless specifically requested.

The independent legacy-tool review identified all-interface listening, permissive
CORS, incompatible password hashing, unsafe era apply, online-save races, unsafe
account deletion, incorrect teleport identifiers and mutable frontend batch targets.
These findings are regression requirements, not reasons to narrow the requested
feature set to read-only inspection or access-code management alone.

Implementation and observed verification are recorded in
[the production GM guide](../ops/production-gm-20261010.md), including the exact
owner acceptance steps, current activation gates and rollback.
