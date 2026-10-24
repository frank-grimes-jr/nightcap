"""Compile the real saved-spawn restoration path against small native fakes.

This is a return-home regression, not an assertion about live hate lists. The
fixture preserves the NPC constructor's audited AI_Start contract (initial
guard point is its construction position). Database, loot and entity publishing
are boundaries; state selection, spawn location selection and state application
are extracted verbatim from the source under test.
"""
from pathlib import Path
import unittest

import test_free_trade as native

ROOT = Path(__file__).resolve().parents[2]


class ZoneStateHomeTests(unittest.TestCase):
    def test_saved_pull_location_does_not_become_stationary_home(self):
        state = (ROOT / 'server-mods/code/zone/zone_save_state.cpp').read_text(encoding='utf-8')
        spawn = (ROOT / 'server-mods/code/zone/spawn2.cpp').read_text(encoding='utf-8')
        load = native.body(state, 'bool Zone::LoadZoneState(')
        spawn_loop = load[load.index('\t// spawn2\n'):load.index('\t// compare state spawns')]
        dynamic_loop = load[load.index('\t// dynamic spawns'):load.index('\n\treturn !spawn_states.empty();')]
        process = native.body(spawn, 'bool Spawn2::Process(')
        location = process[process.index('\t\tglm::vec4 loc('):process.index('\n\t\t/**\n\t\t * Roambox init')]
        fixture = (Path(__file__).parent / 'zone_state_home_fixture.cpp').read_text(encoding='utf-8')
        position = (Path(__file__).parent / 'zone_state_position_upstream_fixture.cpp').read_text(encoding='utf-8')
        # Keep native double literals unchanged (their float conversion matters
        # to the regression); silence only MSVC's warnings for those two legacy
        # conversions, scoped strictly to the pinned upstream helper bodies.
        position = ('#ifdef _MSC_VER\n#pragma warning(push)\n#pragma warning(disable:4305)\n#endif\n'
                    + position + '\n#ifdef _MSC_VER\n#pragma warning(pop)\n#endif\n')
        fixture = fixture.replace('// ACTUAL_POSITION_METHODS', position)
        fixture = fixture.replace('// ACTUAL_STATE_APPLICATION', native.body(state, 'inline void LoadNPCState('))
        fixture = fixture.replace('// ACTUAL_SPAWN_LOCATION', location)
        fixture = fixture.replace('// ACTUAL_SPAWN_RESTORE', spawn_loop)
        fixture = fixture.replace('// ACTUAL_DYNAMIC_RESTORE', dynamic_loop)
        native.FreeTradeTests.compile_run(self, fixture)


if __name__ == '__main__':
    unittest.main()
