# =============================================================================
# INTENTIONALLY INERT — this file does NOT run.
#
# The zone loads ONE global_player script, chosen by _load_precedence
# (main.cpp registers Lua before Perl), so when global_player.lua exists it
# ALWAYS wins and this .pl is never parsed. Everything that used to live here
# is already handled in global_player.lua:
#   - veteran AA + PoK "Ancient Attunement" recall grant  -> event_connect
#   - "mysterious voice" Wayfarer message                 -> event_enter_zone
#   - epic 1.5/2.0 combine rewards                         -> event_combine_success
#   - level milestone popups                               -> event_level_up
#
# Native skill unlocks are owned by Client::ReconcileMulticlassSkills in C++.
#
# Waypoint discovery (#32) moved OFF global_player entirely to the marker NPC's
# own proximity script: quests/global/999240.pl (loads regardless of the
# global_player language). The old Perl timer here never ran — that is why
# waypoints "didn't register".
#
# DO NOT add live logic to this file. Put global-player behaviour in
# global_player.lua, or delete that file first if you truly need Perl here.
# =============================================================================

1;
