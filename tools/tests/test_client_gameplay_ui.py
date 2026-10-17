import unittest
import xml.etree.ElementTree as ET
from client_gameplay_assets import ui_xml


def aa_fixture():
    root = ET.Element('XML')
    for name in ('General', 'Arch', 'Class', 'Special'):
        node = ET.SubElement(root, 'Listbox', item=f'AAW_{name}List')
        for heading, width in [('Title', 225), ('Cur/Max', 60), ('Cost', 40), ('Category', 135)]:
            column = ET.SubElement(node, 'Columns')
            ET.SubElement(column, 'Heading').text = heading
            ET.SubElement(column, 'Width').text = str(width)
    for tag, name, width in [
        ('Screen', 'AAWindow', 640), ('TabBox', 'AAW_Subwindows', 480),
        ('STMLbox', 'AAW_Description', 478),
        *[('Page', f'AAW_{name}Page', 472) for name in ('General', 'Archetype', 'Class', 'Special')]
    ]:
        node = ET.SubElement(root, tag, item=name)
        ET.SubElement(ET.SubElement(node, 'Size'), 'CX').text = str(width)
    button = ET.SubElement(root, 'Button', item='AAW_TrainButton')
    ET.SubElement(ET.SubElement(button, 'Location'), 'X').text = '530'
    ET.SubElement(root.find("Screen[@item='AAWindow']/Size"), 'CY').text = '496'
    for item,x in [('AAW_TrainFilter',5),('AAW_PassiveFilter',95),('AAW_ExpansionFilter',195),('AAW_CatigoryFilter',325),('AAW_ResetFilter',425)]:
        node=ET.SubElement(root, 'Button', item=item)
        for tag,value in [('ScreenID',item),('Text','Can Purchase'),('TooltipReference','Filter')]:
            ET.SubElement(node,tag).text=value
        loc=ET.SubElement(node,'Location'); ET.SubElement(loc,'X').text=str(x);ET.SubElement(loc,'Y').text='442'
        size=ET.SubElement(node,'Size'); ET.SubElement(size,'CX').text='85';ET.SubElement(size,'CY').text='24'
        ET.SubElement(node,'Style_Checkbox').text='true'
    return ET.tostring(root)


class UIAssets(unittest.TestCase):
    def test_three_class_label_uses_reserved_type_only(self):
        source = b'<XML><Label item="IW_Class"><EQType>3</EQType><Text>Class</Text></Label><Label item="Other"><EQType>3</EQType></Label><TabBox item="IW_Subwindows"/></XML>'
        result = ET.fromstring(ui_xml(source, 'inventory'))
        self.assertEqual(result.findtext("Label[@item='IW_Class']/EQType"), '10001')
        self.assertEqual(result.findtext("Label[@item='Other']/EQType"), '3')
        self.assertEqual(len(result.findall("Page[@item='NCPA_Page']")), 1)
        ids = [n.findtext('ScreenID') for n in result if (n.get('item') or '').startswith('NCPA_')]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertNotIn(None, ids)
        for action in ('Equip','Remove','Inspect'):
            self.assertEqual(len([v for v in ids if v.startswith('NCPA_'+action)]), 8)
        labels = [int(n.findtext('EQType')) for n in result.findall('Label') if (n.get('item') or '').startswith('NCPA_Item')]
        self.assertEqual(labels, list(range(10021,10029)))
        with self.assertRaises(ValueError):
            ui_xml(ui_xml(source, 'inventory'), 'inventory')

    def test_aa_column_fits_each_actual_page(self):
        result = ET.fromstring(ui_xml(aa_fixture(), 'aa'))
        for name, page in [('General', 'General'), ('Arch', 'Archetype'), ('Class', 'Class'), ('Special', 'Special')]:
            node = result.find(f"Listbox[@item='AAW_{name}List']")
            self.assertEqual([c.findtext('Heading') for c in node.findall('Columns')], ['Title', 'Cur/Max', 'Cost', 'Category', 'Class', 'Recommended'])
            columns_width = sum(int(c.findtext('Width')) for c in node.findall('Columns'))
            self.assertLessEqual(columns_width, int(result.findtext(f"Page[@item='AAW_{page}Page']/Size/CX")))
        self.assertEqual(result.findtext("TabBox[@item='AAW_Subwindows']/Size/CX"), '860')
        self.assertEqual(result.findtext("Screen[@item='AAWindow']/Size/CX"), '1020')
        self.assertEqual(result.findtext("Button[@item='AAW_TrainButton']/Location/X"), '910')

    def test_recommended_filter_and_status_are_separate_from_purchase(self):
        result=ET.fromstring(ui_xml(aa_fixture(),'aa'))
        self.assertEqual(result.findtext("Button[@item='NC_AARecommended']/Text"),'Recommended AA')
        self.assertEqual(result.findtext("Button[@item='NC_AARecommended']/Style_Checkbox"),'true')
        self.assertEqual(result.findtext("Button[@item='AAW_PassiveFilter']/Location/X"),'240')
        self.assertEqual(result.findtext("Screen[@item='AAWindow']/Size/CY"),'524')
        pieces=[x.text for x in result.findall("Screen[@item='AAWindow']/Pieces")]
        self.assertIn('NC_AARecommended',pieces)
        self.assertIn('NC_AARecommendationStatus',pieces)

    def test_preserves_native_schema_declaration_without_generated_prefix(self):
        # RoF2's XML reader rejected the valid-but-rewritten ns0:Schema form.
        schema = b'<Schema xmlns="EverQuestData" xmlns:dt="EverQuestDataTypes" />'
        source = aa_fixture().replace(b'<XML>', b'<XML ID="EQInterfaceDefinitionLanguage">' + schema)
        output = ui_xml(source, 'aa')
        self.assertIn(schema, output)
        self.assertNotIn(b'ns0:', output)
        self.assertNotIn(b'xmlns:ns0', output)
        parsed = ET.fromstring(output)
        self.assertEqual(parsed.tag, 'XML')
        self.assertEqual(len(parsed.findall('{EverQuestData}Schema')), 1)
        self.assertEqual(len(parsed.findall('Listbox')), 4)

    def test_unknown_or_partial_layout_refused(self):
        for raw in [aa_fixture().replace(b'Category', b'Timer'), aa_fixture().replace(b'AAW_Subwindows', b'Unknown')]:
            with self.assertRaises(ValueError):
                ui_xml(raw, 'aa')


if __name__ == '__main__':
    unittest.main()
