# Nightcap documentation

Start with [current status](status.md), not a dated candidate report.

- [Start here: OVH + Cloudflare setup](../deploy/production/QUICKSTART.md)
- [Hosted owner-test activation and recovery](releases/ovh-activation-20260920.md)
- [Coordinated main/server/client update](releases/hosted-main-update-20260920.md)
- [Private production launcher and hosting kit](../deploy/production/README.md)
- [Production acceptance matrix](../deploy/production/QA.md)

## Players and testers

- [Classic zone augments, new gear and forge: live deployment and exact QA](releases/zone-loot-20261009/README.md)

- [Throw Stone Spell Damage: live deployment and exact QA](releases/throw-stone-20261009.md)

- [40% passive AA tuning: activation, evidence and QA](ops/passive-aa-forty-20261009/README.md)
- [Earlier 20% passive AA activation record](ops/passive-aa-tuning-20261009/README.md)
- [Passive AA while leveling: release behavior, verification and exact QA](releases/passive-aa-20261004.md)

- [Nightcap loading artwork: live release, update instructions and visual checks](releases/loading-screens-20261004.md)

- [Universal item trading: live deployment, resale and exact QA](releases/free-trade-20261004/README.md)

- [Winged Paladin helmet: live release and exact in-game QA](helmets/winged-paladin.md)

- [Blessing reconnect repair: live deployment and exact QA](releases/blessing-relogin-20261002/README.md)

- [Compact tunnel services: layout, complete roster and exact QA](releases/tunnel-compact-20261002/README.md)

- [Advanced loot direct Always/Never controls and empty-window close: deployment and QA](releases/advanced-loot/ROW-CONTROLS.md)
- [Advanced loot Loot All/Ignore action repair: deployment and owner QA](releases/advanced-loot/ACTION-REPAIR.md)

- [Spell selection menu: cached level-255 correction and exact QA](releases/spell-menu-20261002.md)
- [Adventure Journal and archetype Epic 0.5: candidate, routes and exact QA](adventure-journal/README.md)

- [October 1 character-selection crash: deployed material repair and exact login/world QA](releases/character-select-crash-20261001/README.md)

- [Spell inspection: deployed correction, full catalog audit and exact QA](releases/spell-inspection-20261001.md)

- [October 1 Play incident: deployed archive repair and exact startup QA](releases/launcher-play-20261001/README.md)

- [Tunnel class courts and Khaleid: live deployment, layout and owner QA](releases/tunnel-class-courts/PRODUCTION.md)

- [Advanced loot: live deployment, recovery and owner QA](releases/advanced-loot/PRODUCTION.md)
- [Classic model defaults: live release, opt-in and graphical QA](releases/classic-models-20260930/PRODUCTION.md)
- [Enchanter animation commands: live deployment, recovery and QA](releases/enchanter-animation-pet-commands-20260930/PRODUCTION.md)

- [Combat and tier-item repair candidate: evidence and owner QA](releases/combat-item-fixes-20260922/README.md)

- [Three-pet management: live release, evidence and exact owner QA](releases/pet-management-20260922/README.md)

- [Tunnel travel alcove deployed: production evidence and exact owner QA](releases/tunnel-travel-alcove/README.md)

- [Tunnel services and starters deployed: scope, evidence, exact QA and rollback](releases/tunnel-services-starters/README.md)

- [Immediate inventory class refresh: deployment and exact QA](releases/inventory-class-refresh-20260921.md)

- [Permanent patcher: one-time transition and release evidence](releases/permanent-patcher-20260920.md)

- [Production spell/NPC repair: status, evidence and exact QA](releases/production-bugfixes-20260920.md)

- [September 20 main source promotion and remaining QA](releases/main-promotion-20260920.md)
- [Finite merchant finds and EC traders: exact QA](economy/QA.md)
- [Living economy activation, recovery and remaining gates](economy/ACTIVATION.md)
- [Six named tunnel residents and druid-ring QA](economy/residents/README.md)

- [Three class pets: evidence and exact QA](releases/multiclass-pets-20260919/README.md)
- [East Commonlands tunnel proposal](pok/ecommons-tunnel-proposal.md)
- [Silent UI synchronization and release 1906](releases/client-silent-ui-20260919.md)

- [September 19 client/gameplay release and exact QA](releases/client-gameplay-20260919.md)
- [September 19 live activation and recovery](releases/client-gameplay-live-20260919.md)
- [September 19 skin rejection repair and release 1905](releases/client-skin-repair-20260919.md)
- [Phase 24: automatic UI and live activation](milestones/phase-24-report.md)

- [Usable local QA launcher package](releases/launcher-qa-20260915.md)

- [Consolidated test release and exact QA](releases/test-consolidation-20260915.md)

- [Player website](https://frank-grimes-jr.github.io/nightcap/)
- [Project overview and player guide](../README.md)
- [Complete live QA checklist](releases/live-qa-20260915/QA.md)
- [PoK hub layout and merchant counts](pok/hub-layout.md)
- [Bag price ladder and purchase checks](ops/bag-vendor-pricing.md)
- [Current queue](next-steps.md)

## Operators

- [Permanent patcher: packaging, compatibility, recovery and rollback](ops/permanent-patcher.md)

- [Combined deployment, hashes and rollback](releases/live-qa-20260915/README.md)
- [PoK activation and saved-state requirements](pok/QA.md)
- [Public website publishing](ops/player-website.md)
- [Read-only AA title/ownership audit](ops/aa-client-title-audit.md)
- [Docker disk migration and recovery](ops/docker-data-migration-20260913.md)
- [Workspace conventions](../AGENTS.md)
- [Change history](../CHANGES.md)

## Evidence and design

- [Living economy design and pricing policy](economy/SPEC.md)
- [Atomic finite market decision](adr/0041-finite-living-economy.md)

- [Client/gameplay candidate verification](milestones/phase-23-report.md)

- [Signed offline QA launcher evidence](milestones/phase-22-report.md)

- [Test branch consolidation evidence](milestones/phase-21-report.md)

- [Launcher Play/Stop integration evidence](milestones/phase-20-report.md)

- [Go session ownership and health integration](milestones/phase-19-report.md)

- [Native helper protocol and session evidence](milestones/phase-18-report.md)

- [Validated bootstrap PE metadata](milestones/phase-17-report.md)

- [Verified launch file lease evidence](milestones/phase-16-report.md)

- [Pre-entrypoint bootstrap evidence](milestones/phase-15-report.md)
- [Proxy runtime activation and health evidence](milestones/phase-14-report.md)
- [Client delivery development plan](ops/client-delivery-plan.md)
- [Shared patch/configuration preflight evidence](milestones/phase-13-report.md)
- [Windows launcher build and UI evidence](milestones/phase-12-report.md)
- [Guarded client install/recovery evidence](milestones/phase-11-report.md)

- [September 15 live deployment milestone](milestones/phase-5-report.md)
- [Original issue-review snapshot](audits/github-issues-20260914.md)
- [Live AA title findings](audits/aa-titles-20260915/README.md)
- [AA atomic-release evidence](balance/native-aa-class-release-candidate.md)
- [Five-server-fix evidence](releases/server-fixes-20260913/README.md)
- [Dated project/balance assessment](project-understanding.md)
- [Production multiclass spec](superpowers/specs/2026-07-28-true-multiclass-production-spec.md)

Historical documents describe their capture date. A passed offline/native test
is not an in-game sign-off; a deployed candidate is not accepted main gameplay.

- [East Commonlands tunnel hub QA](releases/ecommons-hub-20260920/README.md)

- [Social tunnel revision: complete roster, placement map and exact QA](releases/tunnel-social-20261001/README.md).

- [Resident campfire correction and exact visual QA](releases/tunnel-campfire-20261002/README.md).

- [Blessing lifetime follow-up: native tick evidence and live QA](releases/blessing-lifetime-20261004/README.md)
