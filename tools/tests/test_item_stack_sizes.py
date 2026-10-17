"""Local planner checks; actual emitted MariaDB SQL is rehearsed separately."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from item_stack_sizes import migration, read_snapshot


class ItemStackSizes(unittest.TestCase):
    def test_preserves_exact_original_limits_and_orders_ids(self):
        self.assertEqual(read_snapshot("9\t1\t75\n2\t1\t20\n1\t1\t1\n"),
                         [(1, 1), (2, 20), (9, 75)])

    def test_rejects_nonstackable_larger_invalid_or_duplicate_data(self):
        for text in ("", "1\t0\t20", "1\t1\t100", "1\t1\t200", "1\t1\t0",
                     "1\t1\t-1", "0\t1\t20", "4294967296\t1\t20",
                     "1\t1\t20\n1\t1\t30", "1\t1", "id\tstackable\tstacksize"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                read_snapshot(text)

    def test_sql_deterministic_with_bounded_inserts(self):
        snapshot = "\n".join(f"{i}\t1\t20" for i in range(1, 1002))
        sql = migration(snapshot)
        self.assertEqual(sql, migration(snapshot))
        self.assertEqual(sql.count("INSERT INTO nightcap_stack_plan"), 3)
        self.assertIn("IF n<>1001", sql)


if __name__ == "__main__":
    unittest.main()
