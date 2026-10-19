"""Exact boot normalization, compiled description pairing and fail-closed recovery."""
import importlib.util
import os
from pathlib import Path
import sys
import types
import unittest

if os.name=='nt':sys.modules.setdefault('fcntl',types.SimpleNamespace())
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
spec=importlib.util.spec_from_file_location('resume_notes',HERE/'resume_rule_notes.py')
op=importlib.util.module_from_spec(spec);spec.loader.exec_module(op)


class RuleNoteTests(unittest.TestCase):
    def lines(self,after=False):
        return '\n'.join('1\t'+n+'\ttrue\t'+v[int(after)] for n,v in op.NOTES.items())+'\n1\tUnrelated:Rule\t50\tuntouched\n'
    def test_exact_compiled_only_change(self):
        op.exact_normalization(self.lines(),self.lines(True))
    def test_values_extra_missing_and_unreviewed_notes_rejected(self):
        for value in (self.lines(True).replace('\ttrue\t','\tfalse\t',1),
                      self.lines(True).replace('untouched','modified'),
                      self.lines(True)+'1\tExtra:Rule\ttrue\tadded\n',
                      self.lines(True).split('\n',1)[1],
                      self.lines(True).replace('0.1 percent','0.2 percent')):
            with self.subTest(value=value),self.assertRaises(AssertionError):op.exact_normalization(self.lines(),value)
    def test_duplicate_identity_rejected(self):
        with self.assertRaises(AssertionError):op.parse_rules(self.lines()+self.lines().splitlines()[0])
    def test_generated_rules_use_native_catalog_descriptions(self):
        root=HERE.parents[3]
        header=(root/'server-mods/code/common/ruletypes.h').read_text()
        for name,(old,new) in op.NOTES.items():
            category,rule=name.split(':')
            self.assertIn('RULE_BOOL('+category+', '+rule+', false, "'+new+'")',header)
            paths=[root/'docs/releases/wpm-melee-20261018/content'/('heroic-rule-'+m+'.sql') for m in ('forward','disable','enable')] if category=='Combat' else [HERE.parent/'content'/('rules-'+m+'.sql') for m in ('forward','disable','enable')]
            for p in paths:
                self.assertIn(new.encode().hex(),p.read_text());self.assertNotIn(old.encode().hex(),p.read_text())


if __name__=='__main__':unittest.main()
