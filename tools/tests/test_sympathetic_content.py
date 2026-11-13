import sys
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import sympathetic_content as content


class ContentTests(unittest.TestCase):
    def test_player_descriptions_match_native_amounts_and_ids(self):
        header = (ROOT/"server-mods/code/zone/nightcap_sympathetic.h").read_text()
        divisor = int(re.search(r"\bShareDivisor\s*=\s*(\d+)", header).group(1))
        for key, text in (("Strike", "damage"), ("Healing", "health")):
            amount = int(re.search(rf"\b{key}Amount\s*=\s*(\d+)", header).group(1))
            sid = int(re.search(rf"\b{key}Buff\s*=\s*(\d+)", header).group(1))
            name, description = content.SPELLS[sid]
            self.assertEqual(name, f"Sympathetic {key} I")
            self.assertIn(f"{100/divisor:g}% of its largest direct", description)
            self.assertIn(f"rounded down to a maximum of {amount} {text}", description)
        self.assertIn("before overheal", content.SPELLS[44380][1])

    def test_item_scope_and_stock_focus(self):
        items = [(a[0], b[0]) for t, _, a, b in content.groups() if t == "items"]
        changed = [(old, new) for old, new in items if old != new]
        self.assertEqual(len(items), 8)
        self.assertEqual({(r["id"], r["clickeffect"]) for _,r in changed}, {(610338,44379),(610150,44380)})
        for old, new in changed:
            self.assertEqual((new["clicktype"], new["maxcharges"], new["classes"]), (4,-1,65535))
            self.assertEqual((new["casttime"], new["casttime_"]), (2000,2000))
            self.assertEqual(new["focuseffect"], old["focuseffect"])
        self.assertEqual([r["focuseffect"] for _,r in changed if r["id"] == 610150], [2349])

    def test_distinct_native_marker_buffs(self):
        rows = content.spell_rows()
        self.assertEqual(len({s["spellgroup"] for s in rows}), 2)
        self.assertEqual(len({s["new_icon"] for s in rows}), 2)
        for s in rows:
            self.assertEqual((s["goodEffect"], s["targettype"], s["buffdurationformula"], s["short_buff_box"]), (1,6,50,0))
            self.assertEqual((s["can_mgb"], s["persistdeath"], s["RecourseLink"], s["mana"]), (0,0,0,0))
            self.assertTrue(s["player_1"])
            self.assertTrue(all(s[f"classes{i}"] == 255 for i in range(1,17)))
            self.assertTrue(all(s[f"effectid{i}"] == 254 for i in range(1,13)))
            self.assertEqual(s["descnum"], s["id"])

    def test_byte_preserving_export_and_collision_rejection(self):
        for name, old in (("dbstr_us.txt", b"44379^4^Keep this other type.^0\r\n77^6^Ke\xe9p^0"),
                          ("spells_us.txt", b"12^" + b"^".join([b"0"]*236) + b"\n")):
            after = content.overlay(old, name)
            self.assertTrue(after.startswith(old))
            self.assertEqual(content.overlay(after, name), after)
            added = after[len(old):].strip().splitlines()
            self.assertEqual(len(added), 2)
            with self.assertRaisesRegex(ValueError, "Occupied or duplicate"):
                content.overlay(after + added[0] + b"\n", name)
            with self.assertRaisesRegex(ValueError, "Occupied or duplicate"):
                content.overlay(after.replace(b"44380^", b"44379^"), name)
            if name == "spells_us.txt":
                self.assertTrue(all(len(r.split(b"^")) == 237 for r in added))
        with self.assertRaisesRegex(ValueError, "237"):
            content.overlay(b"12^Malformed\n","spells_us.txt")


if __name__ == "__main__":
    unittest.main()
