import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dungeon_classic import literal_rows

class ClassicParserTests(unittest.TestCase):
    def test_literals_and_escaped_strings(self):
        self.assertEqual(list(literal_rows("(1,'Vox\\'s bag',NULL,-2.5),(2,'a\\nb',0,1e2);")),
                         [[1,"Vox's bag",None,-2.5],[2,'a\nb',0,100.]])
    def test_expressions_and_extra_statements_are_rejected(self):
        for text in ["(1,LOAD_FILE('/etc/passwd'))",'(1); DROP TABLE x;',
                     '(1,@@global.x)','(1,2',"(1,'unterminated)"]:
            with self.subTest(text=text), self.assertRaises(ValueError):
                list(literal_rows(text))

if __name__=='__main__': unittest.main()
