const assert = require('node:assert/strict');
const test = require('node:test');
const fs = require('node:fs');
const {selectFamilies} = require('./assets/equipment.js');
const catalog = JSON.parse(fs.readFileSync(__dirname + '/catalog.json', 'utf8'));
const rows = catalog.items.filter(i => i.tier === 0).map(i => ({name:i.name, kind:i.kind, slots:i.slot.toLowerCase().split(',').map(s=>s.trim()).join('|'), level:i.required_level, zone:i.zone}));
for (const row of rows) row.search=catalog.items.filter(i=>i.zone===row.zone&&i.kind===row.kind).map(i=>i.name).join(' | ');
test('every exact published variant name finds its single family', () => {
  for (const item of catalog.items) {
    const matches=selectFamilies(rows,{q:item.name}).matches;
    assert.equal(matches.length,1,item.name);
    assert.equal(matches[0].zone,item.zone);
    assert.equal(matches[0].kind,item.kind);
  }
});
test('catalog pages contain families once, covering all 96 across eight pages', () => {
  let all = [];
  for (let page=1;page<=8;page++) all.push(...selectFamilies(rows,{},page).visible);
  assert.equal(all.length,96); assert.equal(new Set(all).size,96);
  assert.equal(selectFamilies(rows,{},999).page,8);
  assert.equal(selectFamilies(rows,{},'broken').page,1);
});
test('gear slot and level filters combine, without including augments', () => {
  const selected = selectFamilies(rows,{kind:'Gear',slot:'head',level:'10'}).matches;
  assert.deepEqual(selected.map(i=>i.name),['Cliffwatch Cap','Duskroot Cowl']);
});
test('augments match every compatible socket slot, but not jewelry', () => {
  assert.equal(selectFamilies(rows,{kind:'Augment',slot:'hands'}).matches.length,48);
  assert.equal(selectFamilies(rows,{kind:'Augment',slot:'finger'}).matches.length,0);
});
test('zone filter selects its two families; query narrows by words', () => {
  assert.equal(selectFamilies(rows,{zone:'qeytoqrg'}).matches.length,2);
  assert.deepEqual(selectFamilies(rows,{zone:'qeytoqrg',q:'dew HILLSIDE'}).matches.map(i=>i.name),['Hillside Dewstone']);
});
test('required-level sorting is numerical and paging resets safely on narrow results', () => {
  const selected = selectFamilies(rows,{sort:'level'}).matches;
  assert.ok(selected.every((row,n)=>n===0||row.level>=selected[n-1].level));
  assert.equal(selectFamilies(rows,{q:'Hillside'},8).page,1);
});
test('unsafe-looking or unmatched search text returns empty results without markup', () => {
  const result=selectFamilies(rows,{q:'<script>alert(1)</script>'});
  assert.equal(result.matches.length,0);assert.equal(result.pages,1);
});
