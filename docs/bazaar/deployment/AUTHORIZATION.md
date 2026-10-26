# Live QA authorization

On October26,2026 the owner answered **Approve main and live QA deployment**
to the explicit question asking to promote the tested candidate to main and deploy
it with a brief full game-runtime restart. The question stated that native RoF2
search and buying still require player verification.

This authorizes this bazaar release and its required schema/native pairing,
backup, controlled restart and related wiki maintenance. It is not evidence of
completed player QA or blanket permission for unrelated gameplay changes.

Feature PR335 and test PR336 are merged; test6a910a35 matches the final reviewed
feature source. Deployment tooling followed via PR337/338; main PR339/29e4e84b and production
activation are now verified. The owner will perform native player QA later.
The full zone binary84b6b9ff,22 database tests,2 native groups and19 wiki tests pass.
The guarded release operator has28 failure/recovery tests; mutable production
configuration and player data remain in ignored private evidence only.
