# Current release authorization

The owner requested: "Improve the fast heals without reducing Greater Healing, and test sympathetic healing alongside it. Push to test, then merge to main and deploy once validated."

The validated gameplay passed dev PR495, test PR496 and main PR497. Native results are recorded separately from player acceptance.

Production preflight passed, then reported one player online. Asked whether to wait for logout or send a maintenance notice, the owner replied "Proceed" on November20. This authorizes the current maintenance to proceed with an admission drain. The new explicit `activate-authorized-drain` action closes the gateway and allows the existing125-second connection/save drain; it still requires world player count zero before stopping game, fresh stopped backup, saved-state preservation and all original release checks. It grants no standing permission for future deployments.

The initial v1 stage was never activated. The v2 stage contains the explicit action; the gameplay binary is identical to the validated candidate. No notice was sent or claimed.
