"""Generate the creation-screen asset for the isolated RoF2 selector experiment."""

import argparse
import hashlib
from pathlib import Path
import xml.etree.ElementTree as ET


STOCK_SHA256 = "2da0ea6ecf7eb04a1ca4bd2ec3ba15c8062160df86540ab3ce9809c11398249a"
CONTROL = "CC_Class_Cairnwright_Button"


def build(stock):
    if hashlib.sha256(stock).hexdigest() != STOCK_SHA256:
        raise ValueError("Expected the reviewed stock RoF2 CharacterCreate layout")
    # Preserve the original XML declaration, namespace spelling, and line endings.
    newline = b"\r\n" if b"\r\n" in stock else b"\n"
    xml = stock.decode("ascii").splitlines()
    position = xml.index('\t<Button item="CC_Class_Bard_Button">')
    xml[position:position] = [
        f'\t<Button item="{CONTROL}">',
        f'\t\t<ScreenID>{CONTROL}</ScreenID>',
        '\t\t<RadioGroup>Class</RadioGroup>',
        '\t\t<RelativePosition>true</RelativePosition>',
        '\t\t<Location><X>76</X><Y>7</Y></Location>',
        '\t\t<Size><CX>116</CX><CY>30</CY></Size>',
        '\t\t<Style_Checkbox>true</Style_Checkbox>',
        '\t\t<Text>Cairnwright</Text>',
        '\t\t<TooltipReference>Cairnwright</TooltipReference>',
        '\t\t<Template>BDT_Normal</Template>',
        '\t</Button>',
    ]
    # The heading and button fit side by side above the existing four rows.
    heading = xml.index('\t<StaticAnimation item="CC_ClassAnim">')
    x = xml.index('\t\t\t<X>69</X>', heading, heading + 10)
    xml[x] = '\t\t\t<X>7</X>'
    position = xml.index('\t\t<Pieces>CC_ClassAnim</Pieces>')
    xml.insert(position, f'\t\t<Pieces>{CONTROL}</Pieces>')
    result = newline.join(line.encode("ascii") for line in xml)
    if stock.endswith(newline):
        result += newline
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stock", type=Path)
    parser.add_argument("output", type=Path, help="New QA layout file")
    args = parser.parse_args()
    result = build(args.stock.read_bytes())
    ET.fromstring(result)
    with args.output.open("xb") as output:
        output.write(result)
    print(hashlib.sha256(result).hexdigest(), args.output)


if __name__ == "__main__":
    main()
