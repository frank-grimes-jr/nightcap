"""Generate the actual stock RoF2 recipe window and verify native control layout.

Use --stock PATH to select a retained EQUI_TradeskillWnd.xml. The installed
client is read-only; generated XML exists only in memory. This checks generator
output structure, not actual RoF2 rendering or native font/anchor interpretation.
"""
import argparse
from collections import Counter
import copy
from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from client_gameplay_assets import ui_xml

STOCK = Path("E:/EQ_Local_Dev/Client_RoF2_Dev/everquest_rof2/uifiles/default/EQUI_TradeskillWnd.xml")


class TradeskillUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = STOCK.read_bytes()
        cls.stock = ET.fromstring(cls.raw)
        cls.generated = ui_xml(cls.raw, "tradeskill")
        cls.output = ET.fromstring(cls.generated)

    def test_stock_names_and_native_lookup_ids_remain_unique(self):
        before = {node.get("item"): node for node in self.stock if node.get("item")}
        after = {node.get("item"): node for node in self.output if node.get("item")}
        self.assertEqual(set(after) - set(before), {"NC_CraftAll", "NC_CraftStop"})
        self.assertFalse(set(before) - set(after))
        counts = Counter(node.get("item") for node in self.output if node.get("item"))
        self.assertTrue(all(count == 1 for count in counts.values()))
        for name, old in before.items():
            with self.subTest(control=name):
                self.assertEqual(after[name].tag, old.tag)
                self.assertEqual(after[name].findtext("ScreenID"), old.findtext("ScreenID"))
        screens = Counter(node.findtext("ScreenID") for node in self.output if node.findtext("ScreenID"))
        for name in ("CombineButton", "AutoInvButton", "NC_CraftAll", "NC_CraftStop"):
            self.assertEqual(screens[name], 1)

    def test_four_buttons_fit_combine_area_without_overlaps(self):
        area = self.output.find("Screen[@item='COMBW_CombineArea']")
        names = ("COMBW_CombineButton", "NC_CraftAll", "NC_CraftStop", "COMBW_AutoInvButton")
        pieces = [piece.text for piece in area.findall("Pieces")]
        height = int(area.findtext("BottomAnchorOffset")) - int(area.findtext("TopAnchorOffset"))
        previous_bottom = 0
        for name in names:
            with self.subTest(button=name):
                self.assertEqual(pieces.count(name), 1)
                button = self.output.find(f"Button[@item='{name}']")
                self.assertEqual(button.findtext("TopAnchorToTop"), "true")
                self.assertEqual(button.findtext("BottomAnchorToTop"), "true")
                top = int(button.findtext("TopAnchorOffset"))
                bottom = int(button.findtext("BottomAnchorOffset"))
                self.assertGreaterEqual(top, previous_bottom)
                self.assertGreaterEqual(bottom - top, 24)
                self.assertLessEqual(bottom, height)
                self.assertEqual(button.findtext("Template"), "BDT_SmallNormal")
                previous_bottom = bottom
        flags = self.output.find("Screen[@item='COMBW_FlagsArea']")
        self.assertGreater(int(flags.findtext("TopAnchorOffset")), int(area.findtext("BottomAnchorOffset")))
        before = int(self.stock.findtext("Screen[@item='TradeskillWnd']/Size/CY"))
        after = int(self.output.findtext("Screen[@item='TradeskillWnd']/Size/CY"))
        self.assertEqual(after - before, 66)

    def test_unrelated_native_controls_and_piece_references_are_preserved(self):
        owned = {"COMBW_CombineButton", "COMBW_AutoInvButton", "COMBW_CombineArea", "COMBW_FlagsArea", "TradeskillWnd"}
        def structure(node):
            return node.tag, node.attrib, (node.text or "").strip(), [structure(child) for child in node]
        for old in self.stock:
            name = old.get("item")
            if name and name not in owned:
                with self.subTest(control=name):
                    self.assertEqual(structure(old), structure(self.output.find(f"{old.tag}[@item='{name}']")))
        for screen in self.output.findall("Screen"):
            pieces = [piece.text for piece in screen.findall("Pieces")]
            self.assertEqual(len(pieces), len(set(pieces)), screen.get("item"))

    def test_native_schema_declaration_preserved(self):
        self.assertIn(b'<Schema xmlns="EverQuestData" xmlns:dt="EverQuestDataTypes"', self.generated)
        self.assertNotIn(b"ns0:", self.generated)
        self.assertEqual(self.output.findtext("Button[@item='COMBW_CombineButton']/Text"), "Craft One")
        self.assertEqual(self.output.findtext("Button[@item='NC_CraftAll']/Text"), "Craft All")
        self.assertEqual(self.output.findtext("Button[@item='NC_CraftStop']/Text"), "Stop")

    def test_rejects_duplicate_and_unsupported_stock_controls(self):
        with self.assertRaises(ValueError):
            ui_xml(self.generated, "tradeskill")
        for mutation in ("missing", "duplicate", "screen_id", "no_size"):
            root = copy.deepcopy(self.stock)
            button = root.find("Button[@item='COMBW_CombineButton']")
            if mutation == "missing":
                root.remove(button)
            elif mutation == "duplicate":
                root.append(copy.deepcopy(button))
            elif mutation == "screen_id":
                button.find("ScreenID").text = "UnknownNativeControl"
            else:
                window = root.find("Screen[@item='TradeskillWnd']")
                window.remove(window.find("Size"))
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                ui_xml(ET.tostring(root), "tradeskill")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--stock", type=Path)
    args, remaining = parser.parse_known_args()
    if args.stock:
        STOCK = args.stock
    unittest.main(argv=[sys.argv[0], *remaining], verbosity=2)
