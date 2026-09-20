# Production acceptance — not yet signed off

Automated checks prove components only. Record dates, versions, image hashes,
release ID and results for each manual case. Hosting has not been provisioned.

- [ ] Native crypto self-test passes with the actual shipped loginserver. Correct
  password accepted; wrong/empty hash rejected. Mode14 account provision/reset
  agrees with the native verifier. Duplicate usernames do not replace accounts.
- [ ] Isolated DB restore contains the accepted gameplay/schema and account
  namespace. Auto signup, token login, public EQEmu fallback and login web API off.
- [ ] Private world registration succeeds and only Nightcap appears. No external
  EQEmu connection occurs. All advertised endpoints are127.77.0.1 with fixed ports.
- [ ] External scan shows no native UDP, DB or admin port. Only owner SSH allowed.
  Forged CF-Connecting-IP from outside the isolated proxy network is rejected.
- [ ] Denied/non-allowed IP cannot download/connect. Allowed friend can. Revoke
  an established session by restarting gateway; reconnect stays blocked.
- [ ] Fresh Windows machine: WebView2 present, complete supported RoF2 copied,
  ZIP extracted, folder selected, signed update installed, Play works without
  VPN installation, elevated rights, manual eqhost edits or slash commands.
- [ ] Real login → character select → East Commonlands tunnel hub → another zone
  → camp → relog. Chat/mail work with mail-key IP verification still enabled.
- [ ] Inventory displays all three selected classes; AA list has class labels and
  resolved names; each owned pet has at most8equip/remove/inspect armor slots.
- [ ] Class selectors/merchants are at the accepted EC hub positions with exotic
  models. Beneficial buffs/AA/disciplines have no timers and disappear on death;
  DoTs cast instantly; melee continues through casting. Compare the existing
  gameplay QA document for exact NPC/AA cases; infrastructure is not that sign-off.
- [ ] Two different machines can play/zoning simultaneously without crossed
  sessions. Expand to ten players in ten different zones; measure memory/CPU,
  connection latency and zoning time against the local/direct baseline.
- [ ] A long session with over128total flow creations can reuse expired entries;
  no socket growth beyond limits. Check bursty zone entry and large asset downloads.
- [ ] Network loss, Cloudflare edge/tunnel restart, gateway restart and unavailable
  native UDP destination result in a clear disconnect, no silent stuck reader,
  and successful fresh Play. Test packet loss before accepting UDP-over-TCP latency.
- [ ] Normal exit restores exact original eqhost.txt. Crash/relaunch recovers its
  saved original. Conflicting user edits are preserved and reported.
- [ ] Update cancellation and corrupt signature/hash leave a recoverable client.
  Older signed metadata is rejected; publishing assets before channel is atomic.
- [ ] Manifest/key expiry behavior and renewal alarms tested. Current launcher
  rejects a release requiring a newer launcher version and gives an actionable error.
- [ ] Private backup and configuration restored into an isolated environment;
  account login and a saved character work. Previous image rollback rehearsed.
- [ ] Owner signs off before final friend distribution or gameplay promotion.
