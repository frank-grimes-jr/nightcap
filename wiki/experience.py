"""Presentation-only helpers for the handbook. Article prose remains authoritative."""
import html


PATHS = [
    ('begin', 'Start here', 'Your first evening in Nightcap', 'A little preparation. A whole world ahead.',
     ['getting-started', 'launcher', 'features', 'tunnel']),
    ('build', 'Build a character', 'Make the adventure your own', 'Explore the choices behind your next character.',
     ['build-lab', 'multiclass', 'combat', 'pets']),
    ('gear', 'Find better gear', 'Something worth the next fight', 'Find a reward, understand its quality, then plan your upgrade.',
     ['items', 'equipment', 'item-upgrades', 'tradeskills']),
    ('explore', 'Go adventuring', 'Take the long way home', 'Find a destination and learn what is waiting there.',
     ['dungeon-modes', 'zones', 'waypoints', 'travel']),
]


def home(body, articles):
    """Move existing release notices below the discovery tools without losing text."""
    notices, original = body.split('<div class="welcome">', 1)
    welcome, handbook = ('<div class="welcome">' + original).split('<p class="feature-entry">', 1)
    buttons, panels = [], []
    for key, label, title, description, slugs in PATHS:
        buttons.append(f'<button type="button" data-path="{key}" aria-controls="path-{key}" aria-pressed="false">{label}</button>')
        entries = []
        for number, slug in enumerate(slugs, 1):
            article = articles[slug]
            entries.append(f'<a class="journey-link" href="{slug}.html"><span class="step-number">0{number}</span>'
                           f'<span><strong>{html.escape(article["title"])}</strong><small>{html.escape(article["summary"])}</small></span>'
                           '<span class="arrow" aria-hidden="true">↗</span></a>')
        panels.append(f'<section class="journey-panel" id="path-{key}" aria-labelledby="heading-{key}">'
                      f'<div class="journey-intro"><p class="eyebrow">YOUR NEXT CHAPTER</p><h3 id="heading-{key}">{title}</h3><p>{description}</p>'
                      '<span class="compass" aria-hidden="true">✧</span></div><div class="journey-links">' + ''.join(entries) + '</div></section>')
    return welcome + '''<section class="explorer" aria-labelledby="explore-title">
<div class="section-heading"><div><p class="eyebrow">THE WORLD IS OPEN</p><h2 id="explore-title">Where will tonight take you?</h2></div><a href="all-pages.html">All articles ↗</a></div>
<div class="path-picker" role="group" aria-label="Choose your adventure" hidden>''' + ''.join(buttons) + '</div>' + ''.join(panels) + '''</section>
<section class="saved-home" data-saved-home hidden aria-labelledby="saved-heading"><div class="section-heading"><div><p class="eyebrow">YOUR FIELD NOTES</p><h2 id="saved-heading">Saved for your next adventure</h2></div><button type="button" data-open-saved>Manage saved guides</button></div><div data-saved-links></div></section>
<details class="release-digest"><summary><span><span class="eyebrow">FROM THE CAMPFIRE</span><strong>Release notes &amp; live testing</strong></span><span class="digest-hint">Read the latest updates +</span></summary><div class="release-body">''' + notices + '''<p><a href="recent-changes.html">Browse all recent changes →</a></p></div></details>
<h2 id="handbook">Explore the handbook</h2><p class="feature-entry">''' + handbook


def dialogs():
    return '''<dialog id="quick-search" aria-labelledby="quick-title"><div class="dialog-heading"><h2 id="quick-title">What are you looking for?</h2><button type="button" data-close-dialog aria-label="Close search">✕</button></div>
<form action="search.html" role="search"><label class="sr-only" for="quick-query">Search guides, items and zones</label><input id="quick-query" name="q" type="search" placeholder="Try multiclass, Befallen, or #zoneforge…" maxlength="160" autocomplete="off"><button type="submit">All results ↗</button></form>
<p class="dialog-status" id="quick-status" role="status">Search the handbook. Find your next adventure.</p><ul id="quick-results" class="quick-results"></ul><p class="dialog-foot">Tab to a result · Enter to open · Esc to close</p></dialog>
<dialog id="saved-guides" aria-labelledby="saved-title"><div class="dialog-heading"><h2 id="saved-title">Your saved guides</h2><button type="button" data-close-dialog aria-label="Close saved guides">✕</button></div><p>Keep useful pages close. Saved on this browser, with no account needed.</p><div data-saved-list></div><p id="saved-status" role="status"></p></dialog>
<div class="toast" id="wiki-feedback" role="status" aria-live="polite"></div>'''
