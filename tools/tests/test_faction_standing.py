"""Native faction window contracts; no database or game-state writes."""
from pathlib import Path
import unittest
import test_free_trade as native

ROOT = Path(__file__).resolve().parents[2]


class FactionStandingTests(unittest.TestCase):
    def test_actual_command_and_native_total(self):
        source = (ROOT / 'server-mods/code/zone/client.cpp').read_text()
        total = native.body(source, 'int32 Client::GetModCharacterFactionLevel(')
        fixture = (ROOT / 'tools/tests/faction_standing_command_fixture.cpp').read_text()
        native.FreeTradeTests.compile_run(self, fixture.replace('// ACTUAL_GET_MOD', total))

    def test_native_view(self):
        native.FreeTradeTests.compile_run(self, (ROOT / 'tools/tests/faction_standing_fixture.cpp').read_text())

    def test_player_registration_and_existing_gm_gate(self):
        source = (ROOT / 'server-mods/code/zone/command.cpp').read_text()
        self.assertIn('AccountStatus::Player, command_factions)', source)
        self.assertIn('AccountStatus::QuestTroupe, command_faction)', source)
        self.assertIn('#include "faction_standing.inc"', source)


if __name__ == '__main__':
    unittest.main()
