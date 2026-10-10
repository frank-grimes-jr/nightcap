'use strict';
(() => {
  const normalize = text => text.normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  function selectFamilies(rows, filters, requestedPage = 1) {
    const words = normalize(filters.q || '').trim().split(/\s+/).filter(Boolean);
    const matches = rows.filter(row =>
      (!filters.kind || row.kind === filters.kind) &&
      (!filters.slot || row.slots.split('|').includes(filters.slot)) &&
      (!filters.level || Number(row.level) <= Number(filters.level)) &&
      (!filters.zone || row.zone === filters.zone) &&
      words.every(word => normalize(row.search || row.name).includes(word))
    ).sort((a, b) => (filters.sort === 'level' ? Number(a.level) - Number(b.level) : 0) || a.name.localeCompare(b.name));
    const pages = Math.max(1, Math.ceil(matches.length / 12));
    const page = Math.min(pages, Math.max(1, Math.floor(Number(requestedPage)) || 1));
    return {matches, page, pages, visible: matches.slice((page - 1) * 12, page * 12)};
  }
  if (typeof module !== 'undefined') module.exports = {selectFamilies};
  if (typeof document === 'undefined' || !document.querySelector('[data-equipment-browser]')) return;

  const byId = id => document.getElementById('equipment-' + id);
  const rows = [...document.querySelectorAll('[data-equipment-row]')].map(element => ({...element.dataset, element}));
  const types = [...document.querySelectorAll('button[data-kind]')];
  const controls = {q: byId('query'), slot: byId('slot'), level: byId('level'), zone: byId('zone'), sort: byId('sort')};
  const params = new URLSearchParams(location.search);
  let kind = ['Gear', 'Augment'].includes(params.get('kind')) ? params.get('kind') : '';
  let page = params.get('page') || 1;
  for (const [key, control] of Object.entries(controls)) {
    const value = (params.get(key) || '').slice(0, 160);
    if (key === 'q' || [...control.options].some(option => option.value === value)) control.value = value;
  }
  function render() {
    const filters = {kind, ...Object.fromEntries(Object.entries(controls).map(([key, control]) => [key, control.value]))};
    const result = selectFamilies(rows, filters, page);
    page = result.page;
    const visible = new Set(result.visible);
    // Reordering preserves the static links and table semantics; queries never become HTML.
    for (const row of result.matches) byId('rows').append(row.element);
    for (const row of rows) row.element.hidden = !visible.has(row);
    for (const button of types) button.setAttribute('aria-pressed', String(button.dataset.kind === kind));
    const count = result.matches.length;
    byId('status').textContent = count ? `${count} item ${count === 1 ? 'family' : 'families'} · Showing ${(page - 1) * 12 + 1}–${Math.min(page * 12, count)} · Choose a quality to view its stats` : '0 item families';
    byId('empty').hidden = count !== 0;
    byId('page').textContent = `Page ${page} of ${result.pages}`;
    byId('prev').disabled = page === 1;
    byId('next').disabled = page === result.pages;
    byId('pagination').hidden = result.pages === 1;
    const url = new URL(location.href);
    url.search = '';
    for (const [key, value] of Object.entries(filters)) if (value && !(key === 'sort' && value === 'name')) url.searchParams.set(key, value);
    if (page > 1) url.searchParams.set('page', page);
    history.replaceState(null, '', url);
  }
  for (const [key, control] of Object.entries(controls)) control.addEventListener(key === 'q' ? 'input' : 'change', () => {page = 1; render();});
  for (const button of types) button.addEventListener('click', () => {kind = button.dataset.kind; page = 1; render();});
  byId('reset').addEventListener('click', () => {
    kind = ''; page = 1;
    for (const [key, control] of Object.entries(controls)) control.value = key === 'sort' ? 'name' : '';
    render();
  });
  for (const [id, delta] of [['prev', -1], ['next', 1]]) byId(id).addEventListener('click', () => {
    page += delta; render();
    byId('status').scrollIntoView({block: 'start'});
  });
  render();
  byId('controls').hidden = false;
})();
