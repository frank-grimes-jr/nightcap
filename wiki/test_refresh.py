"""Real Git regressions: new source and uncommitted work must trigger wiki review."""
import subprocess
import tempfile
import unittest
from pathlib import Path
from check_refresh import changed_sources, git


class RefreshTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        git(self.repo, 'init', '-q')
        (self.repo/'server-mods').mkdir()
        (self.repo/'server-mods/rule.txt').write_text('original\n')
        self.commit()
        self.review = {'reviewed_revision':git(self.repo, 'rev-parse', 'HEAD'),
                       'source_paths':['server-mods/', 'docs/releases/']}

    def commit(self):
        git(self.repo, 'add', '.')
        git(self.repo, '-c', 'user.name=Wiki test', '-c', 'user.email=wiki@example.invalid', 'commit', '-qm', 'fixture')

    def test_new_system_and_deleted_source_require_review(self):
        (self.repo/'server-mods/rule.txt').unlink()
        (self.repo/'server-mods/new-feature.txt').write_text('new\n')
        self.commit()
        self.assertEqual(changed_sources(self.repo,self.review,'HEAD'),
                         ['server-mods/new-feature.txt','server-mods/rule.txt'])

    def test_working_tree_tracks_staged_unstaged_and_untracked(self):
        (self.repo/'server-mods/rule.txt').write_text('changed\n')
        git(self.repo,'add','server-mods/rule.txt')
        (self.repo/'server-mods/rule.txt').write_text('changed again\n')
        (self.repo/'server-mods/untracked.txt').write_text('new\n')
        self.assertEqual(changed_sources(self.repo,self.review,'HEAD'),[])
        self.assertEqual(changed_sources(self.repo,self.review,'HEAD',True),
                         ['server-mods/rule.txt','server-mods/untracked.txt'])

    def test_unrelated_files_do_not_require_content_review(self):
        (self.repo/'README.md').write_text('local setup\n')
        self.commit()
        self.assertEqual(changed_sources(self.repo,self.review,'HEAD'),[])

    def test_staged_change_canceled_only_in_working_copy_still_requires_review(self):
        path = self.repo/'server-mods/rule.txt'
        path.write_text('staged change\n')
        git(self.repo,'add','server-mods/rule.txt')
        path.write_text('original\n')
        self.assertEqual(changed_sources(self.repo,self.review,'HEAD',True),['server-mods/rule.txt'])

    def test_missing_revision_cannot_pass(self):
        with self.assertRaises(subprocess.CalledProcessError):
            changed_sources(self.repo,self.review,'missing-reference')


if __name__ == '__main__':
    unittest.main()
