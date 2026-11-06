"""Candidate documentation must not claim the item migration is live."""
import json
from pathlib import Path
import unittest
import build


class CandidatePreview(unittest.TestCase):
    def test_every_published_augment_page_keeps_live_values_with_unreleased_link(self):
        data = json.loads((Path(__file__).parent / 'catalog.json').read_text())
        articles = {a['slug']: a for a in build.load_articles()}
        for item in data['items']:
            if item['kind'] == 'Augment':
                article = articles['item-' + str(item['id'])]
                self.assertEqual(article['status'], 'Live testing')
                self.assertIn('Published item values', article['body'])
                self.assertIn('augment-audit.html', article['body'])
                self.assertIn('Not released', article['body'])
        candidate = articles['augment-audit']
        self.assertEqual(candidate['status'], 'Not released')
        for name in ('Understone Heart', 'Blackspire Prism', 'Ember of the First Dawn', 'Cinder of the Ashen Compact'):
            self.assertIn(name, candidate['body'])
        self.assertIn('Disabled; candidate enables', candidate['body'])

    def test_home_and_commands_have_no_unreleased_announcement(self):
        articles = {a['slug']: a for a in build.load_articles()}
        for slug in ('index', 'commands'):
            self.assertNotIn('augment-audit-preview', articles[slug]['body'])
        self.assertNotIn('class="notice"', articles['features']['body'])


if __name__ == '__main__':
    unittest.main()
