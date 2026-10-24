'use strict';
(() => {
  const input = document.querySelector('#wiki-search');
  const results = document.querySelector('#search-results');
  if (!results) return;
  const status = document.querySelector('#search-status');
  const query = (new URLSearchParams(location.search).get('q') || '').trim().slice(0, 160);
  input.value = query;
  if (!query) return;
  status.textContent = 'Searching…';
  const normalize = text => text.normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  const words = normalize(query).split(/\s+/).filter(Boolean);
  fetch('search-index.json').then(response => {
    if (!response.ok) throw new Error('Search index unavailable');
    return response.json();
  }).then(articles => {
    const matches = articles.map(a => {
      const title = normalize(a.title);
      const keywords = (a.keywords || []).map(normalize);
      const text = normalize(a.title + ' ' + a.summary + ' ' + a.text + ' ' + keywords.join(' '));
      const guideBonus = /^(item-|zone-)/.test(a.slug) ? 0 : 3;
      return {a, score: words.every(w => text.includes(w)) ? words.reduce((n, w) => n + (title.includes(w) ? 10 : 1), 0) + (title === normalize(query) ? 100 : 0) + (keywords.includes(normalize(query)) ? 50 : 0) + guideBonus : 0};
    }).filter(r => r.score).sort((a, b) => b.score - a.score || a.a.title.localeCompare(b.a.title));
    status.textContent = matches.length ? `${matches.length} result${matches.length === 1 ? '' : 's'} for “${query}”${matches.length > 100 ? ' · Showing the first 100. Add another word to narrow your search.' : ''}` : `No results for “${query}”. Try a zone, item name, or a command such as #zoneforge.`;
    for (const {a} of matches.slice(0, 100)) {
      const li = document.createElement('li');
      const anchor = document.createElement('a');
      anchor.href = a.slug + '.html';
      anchor.textContent = a.title;
      const small = document.createElement('small');
      small.textContent = a.summary;
      const type = document.createElement('span');
      type.className = 'result-category';
      type.textContent = `${a.category} · ${a.status}`;
      li.append(anchor, type, small);
      results.append(li);
    }
  }).catch(() => {
    status.textContent = 'Search could not load. Please try again or open Guides in the navigation.';
  });
})();
