"""Annotate affected catalog pages without replacing their published stats or labels."""
import json
from pathlib import Path


def annotate(articles):
    preview = json.loads((Path(__file__).parent / 'augment-candidate.json').read_text(encoding='utf-8'))
    if preview['status'] != 'Not released':
        return articles
    ids = {f'item-{f["base"] + tier}' for f in preview['families'] for tier in range(4)}
    zones = {'zone-' + f['zone'] for f in preview['families']}
    body = '<p class="notice" id="augment-audit-preview"><strong>Not released:</strong> the <a href="augment-audit.html">augment audit preview</a> proposes broader NPC drops, secondary bonuses and gem/crystal icons. Published values and current acquisition above remain live until a verified release.</p>'
    for article in articles:
        if article['slug'] in ids | zones:
            article['body'] += '\n' + body
    return articles
