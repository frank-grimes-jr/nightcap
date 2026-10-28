# SoulFire swing report — October 28

Owner clarified: Palwar selected 1H and the item window showed 1H Slashing,
but the visible attack still looked two-handed. This is an unresolved visual
report, not acceptance of the unpublished grip/client repair.

Local regression executes production ItemInstance::RefreshPaladinWeaponGrip and
Mob::AttackAnimation together for all10 IDs, both grips, four repeats (80 checks).
1HS selects Skill1HSlashing/anim1HWeapon5; 2HS selects Skill2HSlashing/anim2HSlashing3.
Both test groups pass. Source checks confirm attacks use the owned inventory
instance, OP_Animation preserves action and DoAnim includes the attacking client.
These checks do not reproduce a rendered RoF2 swing or observe live packets.
No speculative animation remapping or gameplay change was made.

The local reference WearChange path deduplicates unchanged material/model/color;
a same-model grip toggle is not itself proof of a visual equipment refresh.
This is a hypothesis to investigate, not an established cause or a deployed patch.

The initial private-inventory read was blocked by automatic approval review.
The owner then explicitly approved it. The follow-up controlled October28 14:48:28UTC capture confirms SoulFire is
equipped in primary with nightcap_paladin_grip^1^ (1H), and the offhand is empty.
The owner reports the two-handed swing in this setup. This excludes a second
equipped weapon as the explanation; no live animation packets were captured.
The running zone hash ac6656e2a692d3170bcde12ceebbec2c9cec45b7b97f5ef29455d5239dd4e5a4
matches the deployed October26 build, not the new progression candidate. See
production-check.json; raw character equipment capture stays private outside Git.

The owner now also reports the message says1H while SoulFire is stuck as2H. Saved
grip and client behavior disagree. This matches the already reproduced same-ID
client-cache defect; the local repair has not been deployed. No production writes,
forced equipment changes or speculative animation remapping were performed.
The separate rendered swing report remains unaccepted until paired release QA.

Next proof: after an authorized paired release, observe primary attack animation
action plus client rendering/stance, then fix the proven layer and add its native
regression. Test owner and observer views, shield/no shield and both toggle
directions without zoning. Do not label the cache or model refresh as proven cause.
