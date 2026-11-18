// Exercise browser behaviors with a small DOM adapter; no external dependencies.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const code = fs.readFileSync(path.join(__dirname, 'assets/experience.js'), 'utf8');
const articles = JSON.parse(fs.readFileSync(path.join(__dirname, 'dist/search-index.json'), 'utf8'));
class Element {
  constructor(text = '') { this.textContent = text; this.children = []; this.events = {}; this.attrs = {}; this.dataset = {}; this.hidden = true; this.value = ''; }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this.children = children; }
  setAttribute(name, value) { this.attrs[name] = value; }
  getAttribute(name) { return this.attrs[name]; }
  removeAttribute(name) { delete this.attrs[name]; }
  addEventListener(name, fn) { this.events[name] = fn; }
  click() { this.events.click?.({ target: this }); }
  focus() { this.focused = true; }
  showModal() { this.open = true; }
  close() { this.open = false; }
}
function setup({ stored = [], blocked = false, failFetch = false, fetcher, anchor } = {}) {
  const selectors = ['#wiki-feedback', '[data-save-page]', 'h1', '[data-saved-list]', '[data-saved-home]',
    '[data-saved-links]', '.article-tools', 'article', '.reading-time', '[data-theme-toggle]', '.personal-tools',
    '.path-picker', '.navigation', '.reading-progress', '#quick-search', '#saved-guides', '#quick-query',
    '#quick-status', '#quick-results', '#wiki-search', '#saved-status', '#saved-guides [data-close-dialog]'];
  const elements = Object.fromEntries(selectors.map(key => [key, new Element()]));
  elements.h1.textContent = 'Getting started';
  elements.article.textContent = 'An adventure awaits.';
  const groups = {
    '[data-saved-count]': [new Element()], '[data-path]': ['begin', 'gear'].map(key => {
      const node = new Element(); node.dataset.path = key; elements['#path-' + key] = new Element(); return node;
    }), '[data-open-search]': [new Element()], '[data-open-saved]': [new Element()],
    '[data-close-dialog]': [], 'dialog': [elements['#quick-search'], elements['#saved-guides']],
    'article h2[id]': [], '.contents a': [], '[data-saved-list] button': []
  };
  const storage = new Map([['nightcap.saved', JSON.stringify(stored)]]), events = {}, timeouts = [];
  const location = { search: '?path=gear', href: 'https://wiki.test/index.html?path=gear', hash: anchor?'#reference':'' };
  const document = { body: { dataset: { page: 'getting-started' } }, documentElement: { dataset: {}, scrollHeight: 1200 },
    querySelector: selector => elements[selector] || null, querySelectorAll: selector => groups[selector] || [],
    createElement: () => new Element(), getElementById: () => anchor||null, addEventListener: (name, fn) => { events[name] = fn; } };
  let calls = 0;
  vm.runInNewContext(code, { document, location, URL, URLSearchParams,
    localStorage: { getItem: key => { if (blocked) throw Error(); return storage.get(key); }, setItem: (key, value) => { if (blocked) throw Error(); storage.set(key, value); } },
    matchMedia: () => ({ matches: false, addEventListener() {} }), innerHeight: 800, scrollY: 0,
    window: { addEventListener: (name, fn) => { events[name] = fn; } }, requestAnimationFrame: fn => fn(),
    history: { pushState: (_, __, url) => { location.search = url.search; location.href = url.href; } },
    setTimeout: fn => { timeouts.push(fn); return timeouts.length; }, clearTimeout: id => { if (id) timeouts[id - 1] = null; },
    fetch: () => { calls++; return fetcher ? fetcher() : Promise.resolve({ ok: !failFetch, json: async () => articles }); }
  });
  return { elements, groups, storage, events, location, calls: () => calls,
    async query(value) { elements['#quick-query'].value = value; elements['#quick-query'].events.input(); const task = timeouts.pop(); task?.(); await new Promise(setImmediate); }
  };
}
(async () => {
  const reference={tagName:'DETAILS',open:false,parentElement:null,scrollIntoView(){this.scrolled=true;}};
  setup({anchor:reference});
  assert.equal(reference.open,true,'A deep link to a reference disclosure must open the disclosure itself.');
  assert.equal(reference.scrolled,true);
  let env = setup();
  assert.equal(env.groups['[data-path]'][1].attrs['aria-pressed'], 'true');
  env.groups['[data-path]'][0].click();
  assert.equal(env.location.search, '?path=begin');
  env.location.search = '?path=gear'; env.events.popstate();
  assert.equal(env.elements['#path-begin'].hidden, true);
  env.elements['[data-save-page]'].click();
  assert.equal(JSON.parse(env.storage.get('nightcap.saved'))[0].slug, 'getting-started');
  env = setup({ stored: JSON.parse(env.storage.get('nightcap.saved')) });
  assert.equal(env.elements['[data-save-page]'].attrs['aria-pressed'], 'true');
  env.elements['[data-save-page]'].click();
  assert.equal(JSON.parse(env.storage.get('nightcap.saved')).length, 0);
  env = setup({ stored: [{slug:'javascript:alert(1)',title:'bad'}, {slug:'getting-started',title:'<img onerror=alert(1)>'}] });
  assert.equal(env.groups['[data-saved-count]'][0].textContent, 1);
  assert.equal(env.elements['[data-saved-list]'].children[0].children[0].textContent, '<img onerror=alert(1)>');
  env = setup({ blocked: true });
  env.elements['[data-save-page]'].click();
  assert.match(env.elements['#wiki-feedback'].textContent, /this visit only/);
  assert.equal(env.elements['[data-save-page]'].attrs['aria-pressed'], 'true');
  env.elements['[data-theme-toggle]'].click();
  assert.equal(env.elements['[data-theme-toggle]'].attrs['aria-pressed'], 'true');
  env = setup();
  await env.query('#zoneforge');
  assert.equal(env.elements['#quick-results'].children[0].children[0].href, 'zone-hunt.html');
  await env.query('Hillside Dewstone');
  assert.equal(env.elements['#quick-results'].children[0].children[0].href, 'item-940024.html');
  assert.equal(env.calls(), 1, 'cached search index');
  await env.query('<script>alert(1)</script>');
  assert.equal(env.elements['#quick-results'].children.length, 0);
  assert.match(env.elements['#quick-status'].textContent, /No results/);
  await env.query('');
  assert.equal(env.elements['#quick-results'].children.length, 0);
  env = setup({ failFetch: true });
  await env.query('pet');
  assert.match(env.elements['#quick-status'].textContent, /could not load/);
  assert.equal(env.elements['#quick-results'].children[0].children[0].href, 'all-pages.html');
  await env.query('pets');
  assert.equal(env.calls(), 2, 'failed index requests can retry');
  let resolve;
  env = setup({ fetcher: () => new Promise(done => { resolve = done; }) });
  await env.query('pet');
  await env.query('');
  resolve({ ok: true, json: async () => articles });
  await new Promise(setImmediate);
  assert.equal(env.elements['#quick-results'].children.length, 0, 'stale request cannot overwrite a cleared query');
  console.log('PASS: paths/Back, save/remove/restore, unsafe storage, blocked storage, theme, search relevance/cache/empty/error/retry/race');
})().catch(error => { console.error(error); process.exitCode = 1; });
