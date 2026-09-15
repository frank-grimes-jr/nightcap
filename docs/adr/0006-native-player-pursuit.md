# ADR 0006: model player pursuit through client position packets

Date: 2026-09-12. Status: accepted for the isolated balance diagnostic.

## Context

The candidate AA encounter matrix produced a 900-second Vox timeout after the
boss retreated at low HP and the simulated player remained stationary. Treating
this as insufficient player damage or sustain would misdirect balance changes.
Native NPC navigation ignores actors that are not AI-controlled; forcing a player
into AI mode would also alter its casting and combat behavior.

## Decision

Add an explicit `return_to_melee` encounter option. Use the native navigation mesh
to plan routes and submit bounded `OP_ClientUpdate` packets through the normal
client handler. Do not toggle player AI, teleport, cross disabled/zone-line/portal
polygons, accept partial/stuck routes, or skip geometry checks. Stop voluntary
movement for crowd control, zero native run speed, casting, ready healing below
55% HP, or restored melee range and line of sight.

Bound each 50-ms step by native resolved run speed multiplied by the existing
NPC ground-motion conversion (0.4 * 1.45). This is a declared conservative
movement policy, not a claim of full RoF2 client physics parity. Record requested
and applied positions and independently check the bounds and restored range.

Supply position history through `OP_FloatListThing` while sending position
updates, using the engine's non-exempting history type 5. These are synthetic
history samples, not captured client packets. No warp, teleport or zone-line
exemption is granted. Keep native anti-cheat processing enabled.

The diagnostic has no world connection. A linker guard makes unmodeled outbound
world notifications fail explicitly instead of dereferencing a missing connection.
It never connects to the live world. Provide a real opcode-manager object for
the diagnostic packet sink so packet inspection does not dereference null.

## Consequences and validation

With the option absent, all 52 previous encounters reproduce byte for byte.
With it enabled, the former Vox timeout becomes a 271.30-second kill with the
same build, allocation, seed and boss settings. The 52-case pursuit matrix has
954 bounded, applied position updates across three cases and no failed paths.
See `docs/balance/native-player-pursuit.md` for evidence and remaining limits.

Mesh-following approximates deliberate player navigation. Jumping, strafing,
client collision hulls, actual client acceleration and recovery latency still
require in-game QA. Preparation, activated AAs, final BiS selection, timestep
sensitivity and full-source/runtime parity remain separate work.
