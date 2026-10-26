const assert=require('node:assert/strict');
const model=require('./assets/loot-finder-model.js');
const state=q=>model.state(new URLSearchParams(q));
const items=[
 {id:1,name:'Warrior sword',classes:1,slots:8192,reqlevel:1,hp:1,ac:1,mana:0,damage:10,delay:20,bagslots:0,zones:['qeynos'],best_rate:1},
 {id:2,name:'Cleric hammer',classes:2,slots:8192,reqlevel:5,hp:2,ac:2,mana:3,damage:8,delay:20,bagslots:0,zones:['qeynos'],best_rate:90},
 {id:200003,name:'Polished shared ring',classes:3,slots:65536,reqlevel:20,hp:50,ac:5,mana:5,damage:0,delay:0,bagslots:0,zones:['gukbottom'],best_rate:30},
];
assert.deepEqual(model.filter(items,state('classes=1,2')).map(i=>i.id),[2,200003,1]);
assert.deepEqual(model.filter(items,state('classes=1,2&match=all')).map(i=>i.id),[200003]);
assert.deepEqual(model.filter(items,state('slot=15')).map(i=>i.id),[200003]);
assert.deepEqual(model.filter(items,state('quality=1')).map(i=>i.id),[200003]);
assert.deepEqual(model.filter(items,state('level=4')).map(i=>i.id),[1]);
assert.deepEqual(model.filter(items,state('q=200003')).map(i=>i.id),[200003]);
assert.deepEqual(model.filter(items,state('zone=qeynos&sort=rate')).map(i=>i.id),[2,1]);
assert.deepEqual(model.filter(items,state('q=<script>')).map(i=>i.id),[]);
assert.deepEqual(state('classes=1,1,2,3,4,100').classes,[1,2,3]);
assert.equal(state('item=../secret').item,0);
assert.equal(state('level=-1').level,50);
const original=state('classes=1,2&match=all&q=shared&slot=15&quality=1&level=22&zone=gukbottom&sort=hp&page=3&item=200003');
assert.deepEqual(model.state(model.params(original)),original);
assert.equal(model.percent(.00001),'<0.01%');
assert.equal(model.slotNames(items[2]),'Finger');
console.log('14 loot finder filter, class, safety and URL checks passed');
