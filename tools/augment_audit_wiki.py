"""Maintain a public-only, explicitly unreleased augment preview without changing live stats."""
import html
import json
from augment_audit import OUT, ROOT, LABELS


def main():
    summary = json.loads((OUT / 'summary.json').read_text())
    rows = json.loads((OUT / 'item-preimages.json').read_text())
    families = summary['families']
    body = '<p class="notice"><strong>Not released:</strong> this November 6 audit candidate changes augment eligibility, secondary bonuses and icons. Current live catalog values remain below their normal pages. No deployment or player acceptance is claimed.</p>'
    body += '<h2 id="drops">Drops and progression</h2><p>The candidate uses a 1.5% augment roll on any unowned, killable NPC in an enabled reward zone, including guards, named/quest enemies, killable merchants and scripted combat adds. Player-owned pets, mercenaries, restored corpses and protected noncombat actors do not qualify. Corpse ownership and encounter access still apply. The existing equipment allowlist is separate.</p>'
    body += '<p>Base / Polished / Exalted / Ascension weights remain 60% / 30% / 8% / 2%. That is about one augment per 67 kills, or one direct Ascension per 3,333 kills on average; forging offers the other route. Random drops have no guarantee. Chapterhouse and the Ashen Compact move from 0.5% to 1.5% within their managed expeditions. The candidate enables the already accessible Classic Cazic-Thule and newer Hate layout pools. The six other disabled pools remain disabled.</p>'
    body += '<h2 id="secondary">Secondary bonuses</h2><p>Existing primary stats, heroics, required levels and six type-22 armor socket locations remain. Specialty budgets at Ascension are Avoidance +4, Accuracy +5, Shielding +1%, Spell Shielding +2%, Spell Damage or Healing Amount up to +8 per augment (existing higher values retained). Six identical copies therefore add at most 24 Avoidance, 30 Accuracy, 6% Shielding, 12% Spell Shielding or 48 raw damage/healing. Existing item caps, other equipment, AAs and buffs still matter.</p>'
    body += '<p>Shield block is distinct from Shielding: designated families add +1% at Polished/Exalted or +2% at Ascension, with only the strongest Hunt shield-block augment counted. A usable shield is required. Dodge families use Improved Dodge I from Exalted onward; the strongest worn dodge effect applies, rather than adding six copies. Spell haste and mana preservation unlock minor stock focus at Polished and full Spell Haste III / Mana Preservation III at Ascension. Stock limits and strongest-focus behavior apply: haste is 15% at the top with a three-second minimum cast, mana preservation rolls 1–10%, and both use the stock level-60 limit. Four utility families gain Faerune at Ascension (breathing, vision and see invisibility).</p>'
    body += '<h2 id="icons">Recognizable drops</h2><p>All four qualities in a family use a stock gem, crystal or orb icon. The old cloth gloves and default necklace are replaced. No client artwork download is needed; visible loot and inspection checks remain part of release QA.</p>'
    body += '<h2 id="families">Every top-quality augment</h2><p>Ascension is the actual in-game top-quality name; “Ascended augments” refers to these items.</p><div class="table-scroll"><table><thead><tr><th>Augment</th><th>Zone</th><th>Current access</th><th>Candidate specialty</th></tr></thead><tbody>'
    for f in sorted(families, key=lambda f: (not f['enabled'], f['name'])):
        access = 'Enabled' if f['enabled'] else ('Disabled; candidate enables' if f['candidate_enabled'] else 'Disabled')
        if f['zone'] in ('chapterhouse', 'kael'):
            access += '; managed expedition only'
        body += '<tr>' + ''.join('<td>' + html.escape(str(s)) + '</td>' for s in (f['item'], f['name'], access, LABELS[f['specialty']])) + '</tr>'
    body += '</tbody></table></div><h2 id="testing">Release checks</h2><p>Guard drops, scripted adds, expedition corpse recovery, shield/dodge/focus stacking, full loot bags, forging and visible icons require in-game QA before acceptance. Existing live Hunt and encounter balance acceptance remains separate.</p>'
    article = dict(slug='augment-audit', title='Augment audit preview', summary='Every top-quality augment and its zone, plus the unreleased secondary-stat and icon candidate.',
        body=body, category='Equipment', status='Not released', updated='2026-11-06',
        sources=['docs/audits/augments-20261106/README.md', 'docs/audits/augments-20261106/summary.json'])
    (ROOT / 'wiki/articles/augment-audit.json').write_text(json.dumps(article, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    preview = '<p class="notice" id="augment-audit-preview"><strong>Not released:</strong> the <a href="augment-audit.html">November 6 augment audit preview</a> lists all top-quality augments and proposed guard-wide drops, specialty bonuses and exotic icons. Current live behavior remains until a verified release.</p>'
    touched = {'zone-hunt', 'equipment', 'features', 'unreleased', 'camil-vigil', 'ashen-compact'}
    existing = []
    for path in (ROOT / 'wiki/articles').glob('*.json'):
        data = json.loads(path.read_text(encoding='utf-8'))
        if data['slug'] in touched:
            addition = preview
            if data['slug'] == 'features':
                addition = '<h3 id="augment-audit-preview">Zone Hunt augment specialties — Not released</h3><p>Proposed broader NPC drops, secondary bonuses and exotic gem icons. <a href="augment-audit.html">Augment preview and full reward list</a>.</p>'
                data['body'] = data['body'].replace(preview, addition)
            if 'id="augment-audit-preview"' not in data['body']:
                data['body'] += '\n' + addition
            data['updated'] = '2026-11-06'
            if 'docs/audits/augments-20261106/README.md' not in data.setdefault('sources', []):
                data['sources'].append('docs/audits/augments-20261106/README.md')
            path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
            existing.append(data['slug'])
    path = ROOT / 'wiki/articles/recent-changes.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    if 'id="augment-audit-20261106"' not in data['body']:
        data['body'] = '<h2 id="augment-audit-20261106">November 6: augment audit candidate</h2><p><strong>Not released:</strong> <a href="augment-audit.html">review the full augment list</a>, proposed any-NPC drops including guards, balanced secondary choices and gem/crystal icons.</p>\n' + data['body']
    data['updated'] = '2026-11-06'
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    public = dict(status='Not released', families=[{k: f[k] for k in ('zone', 'base', 'specialty', 'icon', 'candidate_enabled')} for f in families])
    (ROOT / 'wiki/augment-candidate.json').write_text(json.dumps(public, indent=2) + '\n')
    articles = []
    for path in sorted((ROOT / 'wiki/articles').glob('*.json')):
        data = json.loads(path.read_text(encoding='utf-8'))
        affected = data['slug'] in set(existing) | {'recent-changes', 'augment-audit'}
        articles.append(dict(slug=data['slug'], decision='candidate preview added' if affected else 'no change',
            reason='Augment acquisition/secondary/icon preview; live labels and values retained' if affected else 'No changes to this guide: commands, access, AA, class, pet, quest and release contracts remain; Home goal paths retained'))
    review = dict(status='local unpublished candidate', articles=articles,
        generated='All existing augment item pages and Hunt zone pages link the candidate; baseline published stats remain. Disabled families are listed only in the preview. No raw capture or operational data published.',
        home='No goal/navigation change; no announcement added', commands='No command/recipe changes',
        source_scope='HEAD plus task working tree; historical global source drift requires separate review')
    (OUT / 'wiki-review.json').write_text(json.dumps(review, indent=2) + '\n')
    print({'authored_articles_reviewed': len(articles), 'preview_guides': existing, 'definitions': len(rows)})


if __name__ == '__main__':
    main()
