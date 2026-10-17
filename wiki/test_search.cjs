const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const code = fs.readFileSync(path.join(__dirname, 'assets/search.js'), 'utf8');
const articles = JSON.parse(fs.readFileSync(path.join(__dirname, 'dist/search-index.json'), 'utf8'));
class Node {
  constructor(tag) { this.tag = tag; this.children = []; this.textContent = ''; }
  append(...nodes) { this.children.push(...nodes); }
}
async function search(q, fail = false) {
  const results = new Node('ol'), status = new Node('p'), input = {};
  vm.runInNewContext(code, {
    document: {querySelector: id => ({'#wiki-search':input, '#search-results':results, '#search-status':status})[id], createElement: tag => new Node(tag)},
    location: {search:'?'+new URLSearchParams({q})}, URLSearchParams,
    fetch: async () => ({ok: !fail, json: async () => articles})
  });
  await new Promise(setImmediate);
  return {results:results.children, status:status.textContent, input:input.value};
}
(async () => {
  let result = await search('#zoneforge');
  assert.equal(result.results[0].children[0].textContent, 'Zone hunt & forging');
  result = await search('Hillside Dewstone');
  assert.equal(result.results[0].children[0].href, 'item-940024.html');
  assert.equal(result.results.length, 6);
  result = await search('hillside ascension');
  assert.equal(result.results[0].children[0].href, 'item-940027.html');
  result = await search('<script>alert(1)</script>');
  assert.equal(result.results.length, 0);
  assert.match(result.status, /No results/);
  result = await search('   ');
  assert.equal(result.results.length, 0);
  result = await search('pets', true);
  assert.match(result.status, /could not load/);
  console.log('PASS: command ranking, exact items, multiword queries, unsafe text, empty query, load failure');
})().catch(error => {console.error(error); process.exitCode = 1;});
