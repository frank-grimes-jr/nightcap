'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const M = require('./assets/build-lab-model.js');
const data=JSON.parse(fs.readFileSync(__dirname+'/build-lab-data.json','utf8'));
const stats={sd:0,ha:0,hint:0,hwis:0,hp:1000,mana:1000,regen:0,reserve:0,passive:0};
const action=(overrides={})=>({id:'test',name:'Test',kind:'damage',enabled:true,scaling:'resolved',base:100,mana:10,cast:1,recovery:0,cooldown:0,ticks:0,group:'',...overrides});
const build=(actions,more={})=>({name:'Test',classes:[11,2,12],stats:{...stats,...more},actions});
const encounter=(more={})=>({duration:10,incoming:0,landed:100,healAt:60,...more});
let count=0;const check=(name,fn)=>{fn();count++;console.log('PASS '+name);};
check('12 native landed spell-value controls',()=>{
  for(const c of data.controls){const a=M.fromSpell(data.spells.find(s=>s.id===c.spell));assert.ok(c.landed.includes(M.spellValue(a,{...stats,...c},11)),JSON.stringify(c));}
});
check('SD and HA caps, integer half-SD and direct-only heroics',()=>{
  assert.equal(M.spellValue(action({scaling:'spell',base:14}),{...stats,sd:1000,hint:100},11),840);
  assert.equal(M.spellValue(action({scaling:'spell',kind:'dot',base:43}),{...stats,sd:39,hint:1000},11),62);
  assert.equal(M.spellValue(action({scaling:'spell',kind:'heal',base:65}),{...stats,ha:1000},11),552);
  assert.equal(M.spellValue(action({scaling:'spell',kind:'heal',base:65}),stats,2),68);
});
check('cast completion, horizon, recovery and cooldown',()=>{
  assert.equal(M.simulate(build([action()]),encounter()).damage,1000);
  assert.equal(M.simulate(build([action({recovery:1})]),encounter()).damage,500);
  assert.equal(M.simulate(build([action({cooldown:4})]),encounter()).damage,200);
  assert.equal(M.simulate(build([action({cast:11})]),encounter()).damage,0);
  assert.equal(M.simulate(build([action()]),encounter()).trace[0].mana,990);
});
check('reserve, six-second regen, starvation and no negative mana',()=>{
  const r=M.simulate(build([action({mana:30})],{mana:50,reserve:20,regen:30}),encounter());
  assert.equal(r.damage,200);assert.equal(r.mana,20);assert.equal(r.firstStarved,1);
});
check('DoTs tick globally, expire and never tick beyond the horizon',()=>{
  const r=M.simulate(build([action({kind:'dot',ticks:2})]),encounter({duration:13}));
  assert.equal(r.damage,200);assert.equal(r.breakdown.test.casts,2);
  assert.equal(M.simulate(build([action({kind:'dot',ticks:2})]),encounter({duration:5})).damage,0);
});
check('same-family DoTs and shared reuse do not stack',()=>{
  const a=action({kind:'dot',ticks:3,group:'family'}), b=action({id:'other',kind:'dot',ticks:3,group:'family'});
  assert.equal(M.simulate(build([a,b]),encounter({duration:12})).damage,200);
  const r=M.simulate(build([action({group:'shared',cooldown:10}),action({id:'b',group:'shared',cooldown:10})]),encounter());
  assert.equal(r.damage,100);
});
check('healing can spend reserve, overheal excluded, death stops actions',()=>{
  const r=M.simulate(build([action({kind:'heal',base:700,mana:30})],{mana:100,reserve:100}),encounter({incoming:100}));
  assert.ok(r.healing>0);assert.ok(r.overheal>0);assert.equal(r.death,null);
  const dead=M.simulate(build([action()],{hp:100}),encounter({incoming:100}));
  assert.equal(dead.death,1);assert.equal(dead.damage,0);assert.equal(dead.dps,0);
  assert.equal(dead.timeline[0].cancelled,true);assert.equal(dead.timeline[0].end,1);
});
check('resolved actions are never scaled again',()=>assert.equal(M.spellValue(action(),{...stats,sd:750,hint:200},12),100));
check('input bounds, duplicate classes, invalid/forged library and oversized saves',()=>{
  assert.throws(()=>M.validateBuild(build([action()],{mana:NaN})));
  assert.throws(()=>M.validateBuild({...build([]),classes:[1,1,2]}));
  assert.throws(()=>M.validateBuild(build([action({kind:'dot',ticks:1.5})])));
  const bolt=M.fromSpell(data.spells.find(s=>s.id==='54'));
  assert.throws(()=>M.checkLibrary({...build([bolt]),classes:[1,2,3]},data.spells));
  assert.throws(()=>M.checkLibrary(build([{...bolt,base:999}]),data.spells));
  assert.throws(()=>M.checkLibrary(build([bolt,{...bolt,id:'extra'}]),data.spells));
  assert.throws(()=>M.validateBuild(build([action({id:'passive'})])));
  assert.throws(()=>M.decode('x'.repeat(40001),data.spells));
  const b=build([bolt]);assert.deepEqual(M.decode(JSON.stringify({version:1,builds:[b,b],encounter:encounter()}),data.spells).builds[0],M.validateBuild(b));
});
(async()=>{
  const b=build([action({id:'weak',base:10}),action({id:'strong',base:100})]);
  const r=await M.optimize(b,encounter());assert.equal(r.tested,2);assert.equal(r.result.damage,1000);assert.equal(r.build.actions[0].id,'strong');
  assert.equal(await M.optimize(b,encounter(),{cancelled:()=>true}),null);
  const raw=build([action({id:'x',enabled:undefined}),action({id:'y',enabled:undefined})]);
  assert.equal((await M.optimize(raw,encounter())).tested,2);
  console.log(`PASS priority search and cancellation; ${count+1} scenario groups, including ${data.controls.length} native controls`);
})().catch(e=>{console.error(e);process.exitCode=1;});
