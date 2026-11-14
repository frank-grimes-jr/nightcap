"""Exercise the shipping SQL against session-local tables on the dev MariaDB."""
from pathlib import Path
import secrets
import subprocess
import unittest

HERE = Path(__file__).resolve().parent
FORWARD = (HERE / "forward.sql").read_text()
ROLLBACK = (HERE / "rollback.sql").read_text()

# Use the actual merchantlist defaults, indices and constraints. Other tables
# model the deployed content read on Nov 14, absent in the older local PEQ.
SETUP = """
CREATE TEMPORARY TABLE merchantlist LIKE peq.merchantlist;
INSERT INTO merchantlist (merchantid, slot, item, min_expansion)
VALUES (999609,104,135564,0), (41,105,52023,0);
CREATE TEMPORARY TABLE npc_types (id INT, merchant_id INT, name VARCHAR(64), class INT, alt_currency_id INT);
INSERT INTO npc_types VALUES (999609,999609,'Della',41,0);
CREATE TEMPORARY TABLE spawnentry (npcID INT, spawngroupID INT);
INSERT INTO spawnentry VALUES (999609,999609);
CREATE TEMPORARY TABLE spawn2 (spawngroupID INT, zone VARCHAR(32), version INT);
INSERT INTO spawn2 VALUES (999609,'ecommons',0);
CREATE TEMPORARY TABLE zone (short_name VARCHAR(32), version INT, ruleset INT);
INSERT INTO zone VALUES ('ecommons',0,1);
CREATE TEMPORARY TABLE rule_values (ruleset_id INT, rule_name VARCHAR(64), rule_value VARCHAR(16));
INSERT INTO rule_values VALUES (1,'Items:FreeTrade','true');
CREATE TEMPORARY TABLE items AS
SELECT id, Name, itemtype, stackable, minstatus, nodrop, price, sellrate FROM peq.items WHERE id=52023;
"""
STOCK = "SELECT merchantid,slot,item,probability FROM merchantlist ORDER BY merchantid,slot;\n"
BEFORE = ["41\t105\t52023\t100", "999609\t104\t135564\t100"]
ADDED = "999609\t105\t52023\t100"


class TunnelStock(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = "nightcap_distiller_test_" + secrets.token_hex(8)
        cls.client = ["docker", "exec", "-i", "akk-stack-mariadb-1", "sh", "-c",
                      'MYSQL_PWD="${MARIADB_ROOT_PASSWORD:-$MYSQL_ROOT_PASSWORD}" '
                      'exec mariadb -uroot --batch --skip-column-names "$@"', "distiller-test"]
        subprocess.run(cls.client, input=f"CREATE DATABASE {cls.schema};", text=True, check=True)
        cls.addClassCleanup(subprocess.run, cls.client, input=f"DROP DATABASE {cls.schema};",
                            text=True, check=True)

    def run_sql(self, statements, expected_errors=()):
        # --force lets the test inspect state after an expected SIGNAL. Each
        # test starts its own session; all fixture tables disappear on exit.
        proc = subprocess.run(self.client + ["--force", self.schema], input=SETUP + statements,
                              text=True, capture_output=True, timeout=90)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        errors = [line for line in proc.stderr.splitlines() if line.startswith("ERROR ")]
        self.assertEqual(len(errors), len(expected_errors), proc.stderr)
        for error, message in zip(errors, expected_errors):
            self.assertIn("45000", error)
            self.assertIn(message, error)
        return proc.stdout.splitlines()

    def test_stock_replay_and_withdrawal(self):
        rows = self.run_sql(FORWARD + FORWARD + STOCK + ROLLBACK + ROLLBACK + STOCK)
        self.assertEqual(rows, BEFORE + [ADDED] + BEFORE)

    def test_occupied_slot_or_item_sold_elsewhere_on_page(self):
        for slot, item in ((105, 4000), (106, 52023)):
            with self.subTest(slot=slot, item=item):
                collision = f"INSERT INTO merchantlist (merchantid,slot,item) VALUES (999609,{slot},{item});\n"
                rows = self.run_sql(collision + FORWARD + STOCK, ["conflicts"])
                self.assertEqual(rows, BEFORE + [f"999609\t{slot}\t{item}\t100"])

    def test_changed_stock_survives_replay_and_rollback(self):
        change = "UPDATE merchantlist SET probability=85 WHERE merchantid=999609 AND slot=105;\n"
        rows = self.run_sql(FORWARD + change + FORWARD + ROLLBACK + STOCK,
                            ["conflicts", "Review changed"])
        self.assertEqual(rows, BEFORE + ["999609\t105\t52023\t85"])

    def test_wrong_item_inactive_price_or_wrong_shop(self):
        for change, error in (
            ("UPDATE items SET itemtype=55", "priced"),
            ("UPDATE rule_values SET rule_value='false'", "priced"),
            ("UPDATE npc_types SET class=1", "jeweler"),
            ("INSERT INTO npc_types VALUES (1,999609,'Other',41,0)", "jeweler"),
            ("UPDATE spawn2 SET zone='commons'", "jeweler"),
        ):
            with self.subTest(change=change):
                self.assertEqual(self.run_sql(change + ";\n" + FORWARD + STOCK, [error]), BEFORE)


if __name__ == "__main__":
    unittest.main()
