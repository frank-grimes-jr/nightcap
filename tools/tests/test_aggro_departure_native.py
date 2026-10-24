"""Native lifecycle/feign regression with authenticated retained upstream helpers.

Only the entity-cleanup calls are extracted from the large death/destructor
methods. Their helpers and NPC feign-memory replay execute real method bodies.
This isolates cleanup semantics, not sockets, death packets, or ID allocation.
"""
from pathlib import Path
import re
import unittest
import test_free_trade as native

ROOT = Path(__file__).resolve().parents[2]
CODE = ROOT / 'server-mods/code/zone'


def cleanup_calls(body):
    return '\n'.join(re.findall(r'(?:entity_list\.(?:RemoveFromTargets|ClearZoneFeignAggro)\(this[^;]*;|ClearFeignMemoryOnDeparture\(\);)', body))


class AggroDepartureTests(unittest.TestCase):
    def test_cleanup_is_after_death_veto_and_before_entity_id_transfer(self):
        death = native.body((CODE / 'attack.cpp').read_text(encoding='utf-8'), 'bool Client::Death(')
        veto = native.body(death, 'if (parse->PlayerHasQuestSub(EVENT_DEATH))')
        cleanup = death.index('ClearFeignMemoryOnDeparture();')
        self.assertGreater(cleanup, death.index(veto) + len(veto))
        self.assertLess(cleanup, death.index('SetID(0);'))
        destructor = native.body((CODE / 'client.cpp').read_text(encoding='utf-8'), 'Client::~Client()')
        # LeaveGroupXTargets rebuilds personal contributions from hate and feign
        # memory before subtracting them from the shared manager. Preserve that
        # evidence until all derived-client bookkeeping has finished.
        departure_cleanup = destructor.index('ClearFeignMemoryOnDeparture();')
        self.assertGreater(departure_cleanup, destructor.index('LeaveGroup();'))
        self.assertGreater(departure_cleanup, destructor.index('UninitializeBuffSlots();'))
        self.assertEqual(destructor[departure_cleanup:].strip(), 'ClearFeignMemoryOnDeparture();\n}')

    def test_departure_cannot_replay_feign_memory_onto_reused_entity_id(self):
        def source(name):
            return (CODE / name).read_text(encoding='utf-8')
        upstream = (Path(__file__).parent / 'aggro_departure_upstream_fixture.cpp').read_text(encoding='utf-8')
        entity = source('entity.cpp') if (CODE / 'entity.cpp').exists() else upstream
        aggro, mob, attack, client = map(source, (
            'aggro.cpp', 'mob.cpp', 'attack.cpp', 'client.cpp'))
        functions = '\n'.join([
            native.body(entity, 'void EntityList::RemoveFromTargets('),
            native.body(entity, 'void EntityList::ClearZoneFeignAggro('),
            native.body(mob, 'bool Mob::RemoveFromHateList('),
            native.body(aggro, 'void Mob::AddFeignMemory('),
            native.body(aggro, 'void Mob::RemoveFromFeignMemory('),
            native.body(aggro, 'bool Mob::IsOnFeignMemory('),
            # Native compatibility parameter is unused. Annotate only this
            # extracted fixture parameter so Clang -Werror remains meaningful.
            native.body(client, 'void Client::RemoveXTarget(').replace('Client::', 'Mob::')
                .replace('bool OnlyAutoSlots', '[[maybe_unused]] bool OnlyAutoSlots'),
            native.body(upstream, 'void XTargetAutoHaters::decrement_count('),
        ])
        if 'void Client::ClearFeignMemoryOnDeparture()' in client:
            functions += '\n' + native.body(client, 'void Client::ClearFeignMemoryOnDeparture()').replace('Client::', 'Mob::')
        replay = native.body(upstream, 'void Mob::Replay()')
        death = cleanup_calls(native.body(attack, 'bool Client::Death('))
        # Real base-destructor virtual dispatch no longer identifies a Client.
        # Group/raid departure bookkeeping is deliberately outside this fixture.
        departure = cleanup_calls(native.body(client, 'Client::~Client()')) + '\nclient = false;\n' + cleanup_calls(native.body(mob, 'Mob::~Mob()'))
        fixture = (Path(__file__).parent / 'aggro_departure_fixture.cpp').read_text(encoding='utf-8')
        fixture = fixture.replace('// ACTUAL_METHODS', functions).replace('// ACTUAL_REPLAY', replay)
        fixture = fixture.replace('// ACTUAL_DEATH_CLEANUP', death).replace('// ACTUAL_DEPARTURE_CLEANUP', departure)
        native.FreeTradeTests.compile_run(self, fixture)


if __name__ == '__main__':
    unittest.main()
