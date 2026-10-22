"""Fail-closed controls for the audited class-armor source-only release."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import quest_armor


class QuestArmorValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="quest-armor-", dir=Path(__file__).resolve().parent)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.catalog_path = self.root / quest_armor.CATALOG.relative_to(quest_armor.ROOT)
        self.reference_path = self.root / quest_armor.REFERENCE.relative_to(quest_armor.ROOT)
        self.catalog = json.loads(quest_armor.CATALOG.read_text())
        self.reference = json.loads(quest_armor.REFERENCE.read_text())
        for path, value in ((self.catalog_path, self.catalog), (self.reference_path, self.reference)):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(value))
        for family in self.catalog["families"]:
            for relative in family["scripts"]:
                path = self.root / "server-mods/quests" / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(quest_armor.ROOT / "server-mods/quests" / relative, path)
        for relative in self.catalog["downstream_compatibility"]:
            path = self.root / "server-mods/quests" / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(quest_armor.ROOT / "server-mods/quests" / relative, path)

    def save_reference(self):
        self.reference_path.write_text(json.dumps(self.reference))

    def item(self, item_id):
        return next(row for row in self.reference["items"] if row["id"] == item_id)

    def change_script(self, old, new):
        path = self.root / "server-mods/quests/southkarana/Shakrn_Meadowgreen.lua"
        text = path.read_text()
        self.assertIn(old, text)
        path.write_text(text.replace(old, new, 1), newline="\n")

    def test_reviewed_37_rewards_in_ten_scripts_validate(self):
        report = quest_armor.validate(self.root)
        self.assertEqual(report["reward_count"], 37)
        self.assertEqual(len(report["scripts"]), 10)
        self.assertEqual([row["path"] for row in report["compatibility_scripts"]], ["overthere/Kurron_Ni.pl"])
        self.assertEqual(report["status"], "candidate; not deployed")

    def test_wrong_target_name_fails(self):
        self.item(604173)["Name"] = "Crafted Helm (Exalted)"
        self.save_reference()
        with self.assertRaisesRegex(ValueError, "Ascended identity"):
            quest_armor.validate(self.root)

    def test_changed_target_eligibility_fails(self):
        for field in ("classes", "races", "slots", "augslot1type", "attuneable"):
            with self.subTest(field=field):
                original = self.item(604173)[field]
                self.item(604173)[field] = original + 1
                self.save_reference()
                with self.assertRaisesRegex(ValueError, "eligibility/socket identity"):
                    quest_armor.validate(self.root)
                self.item(604173)[field] = original

    def test_missing_target_definition_fails(self):
        self.reference["items"] = [row for row in self.reference["items"] if row["id"] != 604173]
        self.save_reference()
        with self.assertRaises(KeyError):
            quest_armor.validate(self.root)

    def test_non_armor_reward_fails_even_when_variant_matches(self):
        self.item(4173)["itemtype"] = self.item(604173)["itemtype"] = 0
        self.save_reference()
        with self.assertRaisesRegex(ValueError, "not ordinary armor"):
            quest_armor.validate(self.root)

    def test_wrong_class_family_fails_even_when_variant_matches(self):
        self.item(4173)["classes"] = self.item(604173)["classes"] = 8
        self.save_reference()
        with self.assertRaisesRegex(ValueError, "class family"):
            quest_armor.validate(self.root)

    def test_changed_handin_input_fails(self):
        self.change_script("item1 = 13743", "item1 = 999")
        with self.assertRaisesRegex(ValueError, "Unexpected source delta"):
            quest_armor.validate(self.root)

    def test_removed_item_return_fails(self):
        self.change_script("item_lib.return_items(e.self, e.other, e.trade)", "-- omitted return")
        with self.assertRaisesRegex(ValueError, "Unexpected source delta"):
            quest_armor.validate(self.root)

    def test_changed_xp_fails(self):
        self.change_script("AddEXP(25000)", "AddEXP(25001)")
        with self.assertRaisesRegex(ValueError, "Unexpected source delta"):
            quest_armor.validate(self.root)

    def test_wrong_reward_tier_fails(self):
        self.change_script("SummonItem(604173)", "SummonItem(404173)")
        with self.assertRaisesRegex(ValueError, "Unexpected source delta"):
            quest_armor.validate(self.root)

    def test_altered_captured_source_hash_fails(self):
        self.reference["scripts"]["southkarana/Shakrn_Meadowgreen.lua"]["source"] += "\n"
        self.save_reference()
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            quest_armor.validate(self.root)

    def test_alternative_quest_precedence_fails(self):
        path = "southkarana/Shakrn_Meadowgreen.lua"
        self.reference["precedence"][path].append("southkarana/14075.pl")
        self.save_reference()
        with self.assertRaisesRegex(ValueError, "Ambiguous quest precedence"):
            quest_armor.validate(self.root)

    def test_duplicate_reward_membership_fails(self):
        self.catalog["families"][0]["scripts"]["southkarana/Shakrn_Meadowgreen.lua"].append(4173)
        self.catalog_path.write_text(json.dumps(self.catalog))
        with self.assertRaisesRegex(ValueError, "duplicate reward"):
            quest_armor.validate(self.root)

    def test_catalog_path_traversal_fails(self):
        self.catalog["families"][0]["scripts"] = {"../other.lua": [4173]}
        self.catalog_path.write_text(json.dumps(self.catalog))
        with self.assertRaisesRegex(ValueError, "Unsafe quest path"):
            quest_armor.validate(self.root)

    def test_grant_rewriter_preserves_same_id_inputs_comments_and_returns(self):
        source = ('-- item 4173 is also an input\n'
                  'if check(4173) then e.other:SummonItem(4173) end\n'
                  'return_items(4173)\n')
        self.assertEqual(quest_armor.reward_source(source, [4173]),
                         source.replace("SummonItem(4173)", "SummonItem(604173)"))

    def test_absent_or_duplicate_terminal_grants_require_review(self):
        for source in ("return_items(4173)", "quest::summonitem(4173);quest::summonitem(4173)"):
            with self.subTest(source=source), self.assertRaisesRegex(ValueError, "Expected one terminal grant"):
                quest_armor.reward_source(source, [4173])

    def test_downstream_threshold_and_letter_changes_fail(self):
        path = self.root / "server-mods/quests/overthere/Kurron_Ni.pl"
        source = path.read_text()
        for before, after in (("$platinum >= 900", "$platinum >= 899"),
                              ("AddItem(18099, 1)", "AddItem(18099, 2)"),
                              ("if ($letter == 0)", "if (1)")):
            with self.subTest(change=before):
                self.assertIn(before, source)
                path.write_text(source.replace(before, after, 1), newline="\n")
                with self.assertRaisesRegex(ValueError, "Downstream compatibility drift"):
                    quest_armor.validate(self.root)

    def test_missing_downstream_script_fails(self):
        (self.root / "server-mods/quests/overthere/Kurron_Ni.pl").unlink()
        with self.assertRaises(FileNotFoundError):
            quest_armor.validate(self.root)

    def test_missing_downstream_catalog_entry_fails(self):
        self.catalog["downstream_compatibility"] = {}
        self.catalog_path.write_text(json.dumps(self.catalog))
        with self.assertRaisesRegex(ValueError, "Missing downstream compatibility"):
            quest_armor.validate(self.root)

    def test_unreviewed_downstream_script_fails(self):
        self.catalog["downstream_compatibility"] = {"overthere/Other.pl": {}}
        self.catalog_path.write_text(json.dumps(self.catalog))
        with self.assertRaisesRegex(ValueError, "Unreviewed downstream script"):
            quest_armor.validate(self.root)

    def test_downstream_precedence_drift_fails(self):
        self.reference["precedence"]["overthere/Kurron_Ni.pl"].append("overthere/Kurron_Ni.lua")
        self.save_reference()
        with self.assertRaisesRegex(ValueError, "Downstream compatibility drift"):
            quest_armor.validate(self.root)


if __name__ == "__main__":
    unittest.main()
