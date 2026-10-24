'use strict';
(() => {
  const one = selector => document.querySelector(selector);
  const all = selector => [...document.querySelectorAll(selector)];
  const feedback = one('#wiki-feedback');
  let feedbackTimer;
  function announce(message) {
    feedback.textContent = message;
    clearTimeout(feedbackTimer);
    feedbackTimer = setTimeout(() => { feedback.textContent = ''; }, 4000);
  }
  const read = (key, fallback) => {
    try { return JSON.parse(localStorage.getItem(key)) ?? fallback; }
    catch { return fallback; }
  };
  const write = (key, value) => {
    try { localStorage.setItem(key, JSON.stringify(value)); return true; }
    catch { return false; }
  };

  // Treat browser storage as untrusted. Never restore arbitrary URLs or markup.
  const stored = read('nightcap.saved', []);
  let saved = Array.isArray(stored) ? stored.filter(item => item &&
    typeof item.slug === 'string' && /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(item.slug) &&
    typeof item.title === 'string' && item.title.length < 200).slice(0, 100) : [];
  saved = saved.filter((item, index) => saved.findIndex(other => other.slug === item.slug) === index);
  const slug = document.body.dataset.page;
  const saveButton = one('[data-save-page]');
  const title = one('h1').textContent;
  function savedLink(item) {
    const link = document.createElement('a');
    link.href = item.slug + '.html';
    link.textContent = item.title;
    return link;
  }
  function renderSaved() {
    const isSaved = saved.some(item => item.slug === slug);
    saveButton.setAttribute('aria-pressed', String(isSaved));
    saveButton.textContent = isSaved ? '★ Guide saved' : '☆ Save this guide';
    all('[data-saved-count]').forEach(count => { count.textContent = saved.length; });
    const list = one('[data-saved-list]');
    list.replaceChildren();
    if (!saved.length) {
      const empty = document.createElement('p');
      empty.textContent = 'Your field notes are empty. Open a guide and choose “Save this guide” to keep it here.';
      list.append(empty);
    }
    saved.forEach(item => {
      const row = document.createElement('div');
      row.className = 'saved-row';
      const remove = document.createElement('button');
      remove.type = 'button';
      remove.textContent = 'Remove';
      remove.setAttribute('aria-label', 'Remove ' + item.title);
      remove.addEventListener('click', () => {
        const index = saved.indexOf(item);
        saved = saved.filter(other => other.slug !== item.slug);
        const persisted = write('nightcap.saved', saved);
        renderSaved();
        const remaining = all('[data-saved-list] button');
        (remaining[Math.min(index, remaining.length - 1)] || one('#saved-guides [data-close-dialog]')).focus();
        one('#saved-status').textContent = persisted ? item.title + ' removed.' : 'Removed for this visit. Browser storage is unavailable.';
      });
      row.append(savedLink(item), remove);
      list.append(row);
    });
    const home = one('[data-saved-home]');
    if (home) {
      home.hidden = !saved.length;
      one('[data-saved-links]').replaceChildren(...saved.slice(0, 6).map(savedLink));
    }
  }
  saveButton.addEventListener('click', () => {
    const exists = saved.some(item => item.slug === slug);
    if (!exists && saved.length >= 100) { announce('Your field notes are full. Remove a guide to save another.'); return; }
    saved = exists ? saved.filter(item => item.slug !== slug) : [{ slug, title }, ...saved];
    const persisted = write('nightcap.saved', saved);
    renderSaved();
    announce(persisted ? (exists ? 'Guide removed from your field notes.' : 'Saved for your next adventure.') : (exists ? 'Removed for this visit only. Browser storage is unavailable.' : 'Saved for this visit only. Browser storage is unavailable.'));
  });
  renderSaved();
  if (!['index', 'search', '404', 'all-pages'].includes(slug)) one('.article-tools').hidden = false;
  const words = one('article').textContent.trim().split(/\s+/).length;
  one('.reading-time').textContent = Math.max(1, Math.ceil(words / 220)) + ' min read';

  const themeButton = one('[data-theme-toggle]');
  function theme(value) {
    document.documentElement.dataset.theme = value;
    themeButton.textContent = value === 'light' ? '☾ Dark mode' : '☼ Light mode';
    themeButton.setAttribute('aria-pressed', String(value === 'light'));
  }
  theme(read('nightcap.theme', 'dark') === 'light' ? 'light' : 'dark');
  themeButton.addEventListener('click', () => {
    const value = document.documentElement.dataset.theme === 'light' ? 'dark' : 'light';
    theme(value);
    if (!write('nightcap.theme', value)) announce('Theme changed for this visit. Browser storage is unavailable.');
  });
  one('.personal-tools').hidden = false;

  const pickers = all('[data-path]');
  function choosePath() {
    const requested = new URLSearchParams(location.search).get('path');
    const selected = pickers.some(button => button.dataset.path === requested) ? requested : 'begin';
    pickers.forEach(button => {
      const active = button.dataset.path === selected;
      button.setAttribute('aria-pressed', String(active));
      one('#path-' + button.dataset.path).hidden = !active;
    });
  }
  if (pickers.length) {
    one('.path-picker').hidden = false;
    choosePath();
    pickers.forEach(button => button.addEventListener('click', () => {
      if (button.getAttribute('aria-pressed') === 'true') return;
      const url = new URL(location.href);
      url.searchParams.set('path', button.dataset.path);
      history.pushState(null, '', url);
      choosePath();
    }));
    window.addEventListener('popstate', choosePath);
  }

  const mobile = matchMedia('(max-width: 760px)');
  const navigation = one('.navigation');
  navigation.open = !mobile.matches;
  mobile.addEventListener('change', event => { navigation.open = !event.matches; });

  // Deep links open the reference itself as well as any enclosing disclosure.
  function revealAnchor() {
    let id;
    try { id = decodeURIComponent(location.hash.slice(1)); } catch { return; }
    if (!id) return;
    const target = document.getElementById(id);
    if (!target) return;
    let parent = target;
    let revealed = false;
    while (parent) {
      if (parent.tagName === 'DETAILS' && !parent.open) { parent.open = true; revealed = true; }
      parent = parent.parentElement;
    }
    if (revealed) target.scrollIntoView();
  }
  revealAnchor();
  window.addEventListener('hashchange', revealAnchor);

  const progress = one('.reading-progress');
  if (slug !== 'index') {
    progress.hidden = false;
    const headings = all('article h2[id]');
    const contents = all('.contents a');
    let framePending = false;
    function updateReading() {
      framePending = false;
      const distance = document.documentElement.scrollHeight - innerHeight;
      progress.value = distance > 0 ? Math.min(100, Math.max(0, scrollY / distance * 100)) : 100;
      const current = headings.filter(heading => heading.getClientRects().length && heading.getBoundingClientRect().top <= 160).pop();
      contents.forEach(link => {
        if (current && link.hash === '#' + current.id) link.setAttribute('aria-current', 'location');
        else link.removeAttribute('aria-current');
      });
    }
    const schedule = () => { if (!framePending) { framePending = true; requestAnimationFrame(updateReading); } };
    window.addEventListener('scroll', schedule, { passive: true });
    window.addEventListener('resize', schedule);
    updateReading();
  }

  const searchDialog = one('#quick-search');
  const savedDialog = one('#saved-guides');
  if (typeof searchDialog.showModal !== 'function') return;
  const queryInput = one('#quick-query');
  const searchStatus = one('#quick-status');
  const results = one('#quick-results');
  let indexPromise, searchGeneration = 0, queryTimer;
  const normalize = text => text.normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  function loadIndex() {
    if (!indexPromise) indexPromise = fetch('search-index.json').then(response => {
      if (!response.ok) throw new Error('Search unavailable');
      return response.json();
    }).catch(error => { indexPromise = null; throw error; });
    return indexPromise;
  }
  async function quickSearch() {
    const generation = ++searchGeneration;
    const query = queryInput.value.trim().slice(0, 160);
    results.replaceChildren();
    if (!query) { searchStatus.textContent = 'Try a class, a destination, an item, or a command.'; return; }
    searchStatus.textContent = 'Searching the handbook…';
    try {
      const articles = await loadIndex();
      if (generation !== searchGeneration) return;
      const normalized = normalize(query), terms = normalized.split(/\s+/).filter(Boolean);
      const matches = articles.map(article => {
        const title = normalize(article.title), keywords = (article.keywords || []).map(normalize);
        const text = normalize(article.title + ' ' + article.summary + ' ' + article.text + ' ' + keywords.join(' '));
        const score = terms.every(term => text.includes(term)) ? terms.reduce((total, term) => total + (title.includes(term) ? 10 : 1), 0)
          + (title === normalized ? 100 : 0) + (keywords.includes(normalized) ? 50 : 0) + (/^(item-|zone-)/.test(article.slug) ? 0 : 3) : 0;
        return { article, score };
      }).filter(match => match.score).sort((a, b) => b.score - a.score || a.article.title.localeCompare(b.article.title));
      searchStatus.textContent = matches.length ? `${matches.length} results · ${Math.min(8, matches.length)} best matches below` : `No results for “${query}”. Try fewer words or browse Guides.`;
      for (const { article } of matches.slice(0, 8)) {
        const li = document.createElement('li'), link = document.createElement('a');
        link.href = article.slug + '.html';
        const name = document.createElement('strong'), meta = document.createElement('small');
        name.textContent = article.title;
        meta.textContent = article.category + ' · ' + article.status + ' — ' + article.summary;
        link.append(name, meta);
        li.append(link);
        results.append(li);
      }
    } catch {
      if (generation === searchGeneration) {
        searchStatus.textContent = 'Search could not load. Type again to retry, or browse Guides.';
        const link = document.createElement('a');
        link.href = 'all-pages.html'; link.textContent = 'Browse guides →';
        const li = document.createElement('li'); li.append(link); results.append(li);
      }
    }
  }
  function openSearch() {
    queryInput.value = one('#wiki-search').value;
    searchDialog.showModal(); queryInput.focus(); quickSearch();
  }
  all('[data-open-search]').forEach(button => { button.hidden = false; button.addEventListener('click', openSearch); });
  all('[data-open-saved]').forEach(button => button.addEventListener('click', () => { renderSaved(); savedDialog.showModal(); }));
  all('[data-close-dialog]').forEach(button => button.addEventListener('click', () => button.closest('dialog').close()));
  all('dialog').forEach(dialog => dialog.addEventListener('click', event => {
    const bounds = dialog.getBoundingClientRect();
    if (event.target === dialog && (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom)) dialog.close();
  }));
  queryInput.addEventListener('input', () => {
    ++searchGeneration;
    clearTimeout(queryTimer);
    queryTimer = setTimeout(quickSearch, 150);
  });
  document.addEventListener('keydown', event => {
    if (event.isComposing || one('dialog[open]') || event.target.closest('input, textarea, select, [contenteditable]')) return;
    if ((event.key === '/' && !event.ctrlKey && !event.metaKey && !event.altKey) || (event.key.toLowerCase() === 'k' && (event.ctrlKey || event.metaKey))) {
      event.preventDefault(); openSearch();
    }
  });
})();
