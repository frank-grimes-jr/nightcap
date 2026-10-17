# Knowledge maintenance

The installed `nightcap-development` skill was updated with the six-skill
behavior, server/client implementation, tests, pairing/reload requirements and
the explicit candidate/deployment/QA boundary. Multiclass, client, balance and
wiki references were updated; reviewed source fingerprints point to source
commit `b81fd66011155da7beec6c284a3e9755e46f3fd0` and the maintained wiki's local
candidate notices. `skill-update.patch` and `skill-install.json` retain the exact
change and guarded installation receipt.

The passing full Go suite was recorded afterward in `skill-go-update.patch`
and `skill-go-install.json`, replacing the earlier toolchain limitation and
refreshing the affected evidence fingerprints. The runtime implementation did
not change during this documentation follow-up.

The skill validator passes. Source checks pass for multiclass (111 files),
client (117 files) and wiki (50 files). Balance's 68-file check reports one
unrelated pre-existing changed `zone/effects.cpp` in the merchant-sell-all
checkout. This task did not change that source or accept its new hash. All
Monk-related fingerprints match. Full results are in `skill-check.json`.

Wiki maintenance is installed locally with the original unrelated candidate
notes preserved. It is not published. The wiki's broad historical source drift
remains explicitly open, and its global content-review revision was not changed.
