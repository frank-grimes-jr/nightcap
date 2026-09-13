"""Exercise the export query against a small relational fixture, not string matches."""
import sqlite3
import unittest

from snapshot import DROP_SOURCES


class DropQueryTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        flags = "min_expansion INTEGER DEFAULT -1, max_expansion INTEGER DEFAULT -1, content_flags TEXT, content_flags_disabled TEXT"
        for definition in (
            'zone(short_name TEXT, version INTEGER, expansion INTEGER)',
            f'spawn2(id INTEGER, spawngroupID INTEGER, zone TEXT, version INTEGER, _condition INTEGER, {flags})',
            f'spawnentry(spawngroupID INTEGER, npcID INTEGER, chance INTEGER, {flags})',
            'npc_types(id INTEGER, name TEXT, level INTEGER, loottable_id INTEGER)',
            f'loottable(id INTEGER, {flags})',
            'loottable_entries(loottable_id INTEGER, lootdrop_id INTEGER, probability INTEGER, multiplier INTEGER)',
            f'lootdrop(id INTEGER, {flags})',
            f'lootdrop_entries(lootdrop_id INTEGER, item_id INTEGER, chance INTEGER, multiplier INTEGER, npc_min_level INTEGER, npc_max_level INTEGER, {flags})',
            'spawn2_disabled(spawn2_id INTEGER, instance_id INTEGER, disabled INTEGER)',
        ):
            self.db.execute('CREATE TABLE ' + definition)
        self.db.executescript("""
            INSERT INTO zone VALUES ('testzone',0,0);
            INSERT INTO spawn2(id,spawngroupID,zone,version,_condition) VALUES (1,2,'testzone',0,0);
            INSERT INTO spawnentry(spawngroupID,npcID,chance) VALUES (2,3,100);
            INSERT INTO npc_types VALUES (3,'Test_Named',50,4);
            INSERT INTO loottable(id) VALUES (4);
            INSERT INTO loottable_entries VALUES (4,5,100,1);
            INSERT INTO lootdrop(id) VALUES (5);
            INSERT INTO lootdrop_entries(lootdrop_id,item_id,chance,multiplier,npc_min_level,npc_max_level)
                VALUES (5,6,100,1,0,0);
        """)

    def tearDown(self):
        self.db.close()

    def rows(self):
        return self.db.execute(DROP_SOURCES).fetchall()

    def test_valid_chain_preserves_provenance(self):
        self.assertEqual(self.rows(), [(6, 'testzone', 3, 'Test_Named', 50)])

    def test_each_parent_expansion_gate_can_remove_drop(self):
        for table in ('spawn2', 'spawnentry', 'loottable', 'lootdrop', 'lootdrop_entries'):
            self.db.execute(f'UPDATE {table} SET min_expansion=1')
            self.assertEqual(self.rows(), [], table)
            self.db.execute(f'UPDATE {table} SET min_expansion=-1')

    def test_instance_override_does_not_disable_openworld(self):
        self.db.execute('INSERT INTO spawn2_disabled VALUES (1,10,1)')
        self.assertEqual(len(self.rows()), 1)
        self.db.execute('INSERT INTO spawn2_disabled VALUES (1,0,1)')
        self.assertEqual(self.rows(), [])

    def test_wrong_npc_level_cannot_supply_item(self):
        self.db.execute('UPDATE lootdrop_entries SET npc_min_level=51')
        self.assertEqual(self.rows(), [])

    def test_zero_drop_probability_cannot_supply_item(self):
        self.db.execute('UPDATE loottable_entries SET probability=0')
        self.assertEqual(self.rows(), [])

    def test_flagged_content_is_outside_unflagged_pool(self):
        self.db.execute("UPDATE lootdrop SET content_flags='event_required'")
        self.assertEqual(self.rows(), [])
