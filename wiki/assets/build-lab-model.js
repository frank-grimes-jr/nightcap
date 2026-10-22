/* Deterministic diagnostic model. Pure functions shared by browser and Node tests. */
(function (root) {
  'use strict';
  const VERSION = 1;
  const ranges = {sd:[0,5000],ha:[0,5000],hint:[0,2000],hwis:[0,2000],hp:[1,100000],mana:[0,100000],regen:[0,10000],passive:[0,10000],reserve:[0,100000]};
  function number(value, min, max, label) {
    if (typeof value !== 'number' || !Number.isFinite(value) || value < min || value > max) throw new Error(`${label} must be between ${min} and ${max}.`);
    return value;
  }
  function label(value, fallback) { return typeof value === 'string' ? value.slice(0,80) : fallback; }
  function validateBuild(raw) {
    if (!raw || typeof raw !== 'object') throw new Error('A build is required.');
    const b = {name:label(raw.name,'My build'), classes:raw.classes, stats:{}, actions:[]};
    if (!Array.isArray(b.classes) || b.classes.length !== 3 || new Set(b.classes).size !== 3 || b.classes.some(x=>!Number.isInteger(x)||x<1||x>16)) throw new Error('Choose three different classes.');
    b.classes = b.classes.slice();
    for (const [key,[min,max]] of Object.entries(ranges)) b.stats[key]=number(raw.stats?.[key],min,max,key);
    if (b.stats.reserve>b.stats.mana) throw new Error('Mana reserve cannot exceed starting mana.');
    if (!Array.isArray(raw.actions) || raw.actions.length>7) throw new Error('Use at most six damage actions and one heal.');
    const ids = new Set();
    b.actions = raw.actions.map((a,i)=>{
      if (!a || !['damage','dot','heal'].includes(a.kind)) throw new Error('Unknown action type.');
      const id=label(a.id,String(i));
      if (!/^[a-zA-Z0-9_-]{1,40}$/.test(id)||ids.has(id)||id==='passive') throw new Error('Actions need unique, non-reserved IDs.');
      ids.add(id);
      const out={id,name:label(a.name,'Action'),kind:a.kind,enabled:a.enabled!==false,
        scaling:a.scaling==='spell'?'spell':'resolved',group:label(a.group,''),spell:label(a.spell,''),
        base:number(a.base,0,1000000,'Effect'),mana:number(a.mana,0,100000,'Mana cost'),
        cast:number(a.cast,0.1,60,'Cast time'),recovery:number(a.recovery,0,60,'Recovery'),
        cooldown:number(a.cooldown,0,900,'Reuse'),ticks:number(a.ticks,0,100,'Ticks')};
      if (!Number.isInteger(out.ticks)||(out.kind==='dot'&&out.ticks<1)) throw new Error('DoTs need a whole number of ticks (1–100).');
      return out;
    });
    if (b.actions.filter(a=>a.kind==='heal').length>1 || b.actions.filter(a=>a.kind!=='heal').length>6) throw new Error('Use at most six damage actions and one heal.');
    return b;
  }
  function validateEncounter(raw) {
    return {duration:number(raw?.duration,1,600,'Fight duration'),incoming:number(raw?.incoming,0,10000,'Incoming DPS'),landed:number(raw?.landed,0,100,'Landed damage'),healAt:number(raw?.healAt,1,99,'Heal threshold')};
  }
  function spellValue(action, stats, primary) {
    if(action.scaling!=='spell') return action.base;
    const sd=Math.min(750,Math.floor(stats.sd)), ha=Math.min(750,Math.floor(stats.ha));
    if(action.kind==='dot') return action.base+Math.floor(sd/2);
    const base=action.kind==='heal' ? action.base+Math.floor(action.base*ha/100)+(primary===2?Math.floor(action.base*5/100):0) : action.base+sd;
    return base+Math.floor(base*Math.floor(action.kind==='heal'?stats.hwis:stats.hint)/1000);
  }
  function fromSpell(spell) {
    return {id:'s'+spell.id,name:spell.name,spell:spell.id,kind:spell.kind,base:spell.base,cast:spell.cast,recovery:spell.recovery,cooldown:spell.cooldown,mana:spell.mana,ticks:spell.ticks,group:spell.group,scaling:'spell',enabled:true};
  }
  function available(spell, classes) { return spell.classes.some(c=>classes.includes(c)); }
  function checkLibrary(build, spells) {
    const seen=new Set();
    for(const a of build.actions.filter(a=>a.scaling==='spell')) {
      const s=spells.find(s=>s.id===a.spell);
      if(!s || !available(s,build.classes)) throw new Error(`${a.name} is unavailable to these classes in the level-50 library.`);
      const canonical=fromSpell(s);
      if(seen.has(a.spell)||a.id!==canonical.id) throw new Error('Each library spell can appear only once with its canonical identity.');
      seen.add(a.spell);
      for(const key of ['base','kind','cast','recovery','cooldown','mana','ticks','group']) if(a[key]!==canonical[key]) throw new Error('Library actions must retain their source values; use a resolved action for custom effects.');
    }
  }
  const step = seconds => Math.ceil(seconds*10-1e-8);
  function simulate(rawBuild, rawEncounter, options={}) {
    const build=validateBuild(rawBuild), e=validateEncounter(rawEncounter), s=build.stats;
    const actions=build.actions.filter(a=>a.enabled).map(a=>({...a,value:spellValue(a,s,build.classes[0]),ready:0}));
    const heals=actions.filter(a=>a.kind==='heal'), attacks=actions.filter(a=>a.kind!=='heal');
    const total=step(e.duration), trace=[], timeline=[], dots=[], groups=new Map(), breakdown=Object.create(null);
    let mana=s.mana,hp=s.hp,damage=0,healing=0,overheal=0,burst=0,spent=0,busy=0,casting=null,death=null,firstStarved=null;
    for (const a of actions) breakdown[a.id]={name:a.name,kind:a.kind,damage:0,healing:0,casts:0};
    if(s.passive) breakdown.passive={name:'Resolved melee / pet DPS',kind:'damage',damage:0,healing:0,casts:0};
    function hit(amount,id,t) { damage+=amount;breakdown[id].damage+=amount;if(t<=100)burst+=amount; }
    for(let t=0;t<=total;t++) {
      const seconds=Math.min(t/10,e.duration);
      if(t>0) {
        const dt=Math.min(.1,e.duration-(t-1)/10);
        if(s.passive)hit(s.passive*dt,'passive',t);
        hp-=e.incoming*dt;
        if(hp<=0) {
          hp=0;death=seconds;
          if(casting&&timeline.length){timeline.at(-1).end=seconds;timeline.at(-1).cancelled=true;}
          if(options.trace!==false)trace.push({time:seconds,mana,hp,damage});
          break;
        }
      }
      if(t>0&&t%60===0) {
        mana=Math.min(s.mana,mana+s.regen);
        for(const dot of dots) if(dot.left>0) {hit(dot.value*e.landed/100,dot.id,t);dot.left--;}
      }
      if(casting&&casting.end===t) {
        const a=casting.action;
        if(a.kind==='heal') {const effective=Math.min(s.hp-hp,a.value);hp+=effective;healing+=effective;overheal+=a.value-effective;breakdown[a.id].healing+=effective;}
        else if(a.kind==='dot') dots.push({id:a.id,group:a.group,value:a.value,left:a.ticks});
        else hit(a.value*e.landed/100,a.id,t);
        a.ready=t+step(a.cooldown);if(a.group)groups.set(a.group,a.ready);
        busy=t+step(a.recovery);casting=null;
      }
      const record=()=>{if(options.trace!==false&&(t%10===0||t===total))trace.push({time:seconds,mana,hp,damage});};
      if(t===total||casting||t<busy) {record();continue;}
      const ready=a=>t>=a.ready&&t>=(groups.get(a.group)||0)&&t+step(a.cast)<=total && !(a.kind==='dot'&&dots.some(d=>d.left>0&&(d.id===a.id||(a.group&&d.group===a.group))));
      let a=hp/s.hp<=e.healAt/100 ? heals.find(a=>ready(a)&&a.mana<=mana) : null;
      if(!a) a=attacks.find(a=>ready(a)&&a.mana<=mana-s.reserve);
      if(!a) {if(firstStarved===null&&attacks.some(a=>ready(a)&&a.mana>mana-s.reserve))firstStarved=seconds;record();continue;}
      mana-=a.mana;spent+=a.mana;breakdown[a.id].casts++;
      casting={action:a,end:t+step(a.cast)};
      if(options.trace!==false)timeline.push({id:a.id,name:a.name,kind:a.kind,start:seconds,end:casting.end/10});
      record();
    }
    const elapsed=death??e.duration;
    return {damage,dps:damage/e.duration,burst:burst/Math.min(10,e.duration),healing,overheal,spent,mana,hp,elapsed,death,firstStarved,breakdown,trace,timeline};
  }
  function* permutations(list) {
    if(!list.length){yield [];return;}
    for(let i=0;i<list.length;i++)for(const rest of permutations(list.filter((_,j)=>j!==i)))yield [list[i],...rest];
  }
  async function optimize(build, encounter, {progress=()=>{},cancelled=()=>false}={}) {
    build=validateBuild(build);encounter=validateEncounter(encounter);
    const attacks=build.actions.filter(a=>a.kind!=='heal'&&a.enabled);
    const rest=build.actions.filter(a=>a.kind==='heal'||!a.enabled);
    let best={build:structuredClone(build),result:simulate(build,encounter,{trace:false})},tested=0;
    for(const order of permutations(attacks)) {
      if(cancelled())return null;
      const candidate={...build,actions:[...rest,...order]},result=simulate(candidate,encounter,{trace:false});
      // Preserve survival first; among equivalent survival outcomes maximize damage.
      if(result.elapsed>best.result.elapsed+1e-8||(Math.abs(result.elapsed-best.result.elapsed)<1e-8&&result.damage>best.result.damage+1e-8))best={build:structuredClone(candidate),result};
      tested++;
      if(tested%6===0){progress(tested);await new Promise(resolve=>setTimeout(resolve,0));}
    }
    return {...best,tested};
  }
  function decode(text,spells) {
    if(typeof text!=='string'||text.length>40000)throw new Error('Build data is too large.');
    const d=JSON.parse(text);
    if(d.version!==VERSION||!Array.isArray(d.builds)||d.builds.length!==2)throw new Error('Unsupported Build Lab save.');
    const builds=d.builds.map(validateBuild);builds.forEach(b=>checkLibrary(b,spells));
    return {version:VERSION,builds,encounter:validateEncounter(d.encounter)};
  }
  const api={VERSION,validateBuild,validateEncounter,spellValue,fromSpell,available,checkLibrary,simulate,optimize,decode};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
  else root.NightcapBuildLab=api;
})(typeof window!=='undefined'?window:globalThis);
