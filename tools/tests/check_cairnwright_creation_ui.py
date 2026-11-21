"""Check a generated layout against the real RoF2 creation-screen source."""

import argparse
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cairnwright_creation_ui import CONTROL, build


def rect(node):
    x, y, width, height = (
        int(node.findtext(field)) for field in ("Location/X", "Location/Y", "Size/CX", "Size/CY")
    )
    return x, y, x + width, y + height


def verify(stock, candidate):
    assert build(stock) == candidate, "The staged file differs from the generated asset"
    before, after = ET.fromstring(stock), ET.fromstring(candidate)
    screen = after.find("Screen[@item='CC_ClassScreen']")
    assert screen is not None
    button = after.find(f"Button[@item='{CONTROL}']")
    assert button is not None and button.findtext("Text") == "Cairnwright"
    assert button.findtext("ScreenID") == CONTROL and button.findtext("RadioGroup") == "Class"
    pieces = [item.text for item in screen.findall("Pieces")]
    assert len(pieces) == len(set(pieces))
    buttons = [node for node in after.findall("Button") if node.findtext("RadioGroup") == "Class"]
    assert len(buttons) == 17 and all(node.get("item") in pieces for node in buttons)
    left, top, right, bottom = rect(button)
    for name in pieces:
        if name == CONTROL:
            continue
        node = after.find(f"*[@item='{name}']")
        x, y, x2, y2 = rect(node)
        assert right <= x or left >= x2 or bottom <= y or top >= y2, f"Overlaps {name}"

    # Remove the three intentional changes and compare every stock element.
    after.remove(button)
    piece = next(item for item in screen.findall("Pieces") if item.text == CONTROL)
    screen.remove(piece)
    field = "StaticAnimation[@item='CC_ClassAnim']/Location/X"
    after.find(field).text = before.findtext(field)
    assert ET.canonicalize(ET.tostring(after), strip_text=True) == ET.canonicalize(
        ET.tostring(before), strip_text=True
    )
    for unsupported in (candidate, stock + b" "):
        try:
            build(unsupported)
        except ValueError:
            continue
        raise AssertionError("Accepted an unsupported input")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stock", type=Path)
    parser.add_argument("candidate", type=Path)
    args = parser.parse_args()
    verify(args.stock.read_bytes(), args.candidate.read_bytes())
    print("PASS: 17 controls; original controls retained; no overlapping bounds; stock hash enforced.")
