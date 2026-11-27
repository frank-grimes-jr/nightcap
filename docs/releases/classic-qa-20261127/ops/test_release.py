import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import package
import release


class QuestOverlay(unittest.TestCase):
    def test_active_extra_lines_and_line_endings_survive_both_changes(self):
        base=b'one\ntwo\nthree\nfour\nfive\nsix\nseven\neight\nnine\nten\neleven\ntwelve\n'
        new=base.replace(b'two\n',b'two-A\ntwo-B\n').replace(b'eleven\n',b'eleven-B\n')
        active=b'active-only\r\n'+base.replace(b'\n',b'\r\n')
        output=package.merge_quest(base,new,active)
        self.assertEqual(output,b'active-only\r\n'+new.replace(b'\n',b'\r\n'))

    def test_absent_and_ambiguous_hunks_are_refused(self):
        for active in (b'b\n',b'a\na\n'):
            with self.subTest(active=active), self.assertRaises(ValueError):
                package.merge_quest(b'a\n',b'c\n',active)


class ReleaseGuards(unittest.TestCase):
    def test_pointer_preserves_unrelated_environment_bytes_and_rejects_drift(self):
        for local, prefix in ((True,b'    image: '),(False,b'NIGHTCAP_GAME_IMAGE=')):
            with tempfile.TemporaryDirectory() as root, self.subTest(local=local):
                path=Path(root)/'selector'
                content=b'other=x\r\n'+prefix+b'base\r\nlast=42\r\n'
                path.write_bytes(content)
                with patch.object(release,'LOCAL',local), patch.object(release,'PTR',path), patch.object(os,'fchown',create=True):
                    if os.name=='nt' and not local:
                        continue
                    release.atomic_pointer('base','next')
                    self.assertEqual(path.read_bytes(),content.replace(prefix+b'base',prefix+b'next'))
                    with self.assertRaises(RuntimeError):
                        release.atomic_pointer('base','different')
                    release.atomic_pointer('next','base')
                    self.assertEqual(path.read_bytes(),content)

    def test_partial_content_aborts_without_writes(self):
        with patch.object(release,'content_check',return_value='SELECT preview'), patch.object(release,'db',return_value='1\t0') as execute:
            with self.assertRaises(AssertionError):
                release.switch_db({},True)
            self.assertTrue(all(args.args==('SELECT preview',) for args in execute.call_args_list))


if __name__=='__main__':
    unittest.main()

