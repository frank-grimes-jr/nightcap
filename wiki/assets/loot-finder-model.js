(function (root) {
 'use strict';
 const classes=['Warrior','Cleric','Paladin','Ranger','Shadow Knight','Druid','Monk','Bard','Rogue','Shaman','Necromancer','Wizard','Magician','Enchanter','Beastlord','Berserker'];
 const slots={0:'Charm',1:'Ear',2:'Head',3:'Face',4:'Ear',5:'Neck',6:'Shoulders',7:'Arms',8:'Back',9:'Wrist',10:'Wrist',11:'Range',12:'Hands',13:'Primary',14:'Secondary',15:'Finger',16:'Finger',17:'Chest',18:'Legs',19:'Feet',20:'Waist',21:'Power source',22:'Ammo'};
 function state(params) {
  const unique=[...new Set((params.get('classes')||'').split(',').map(Number).filter(n=>Number.isInteger(n)&&n>=1&&n<=16))].slice(0,3);
  const level=Number(params.get('level')||50), page=Number(params.get('page')||1), item=Number(params.get('item')||0);
  return {classes:unique,match:params.get('match')==='all'?'all':'any',q:(params.get('q')||'').slice(0,100),
   slot:params.get('slot')==='bag'?'bag':Object.hasOwn(slots,params.get('slot'))?params.get('slot'):'',
   quality:['0','1','2','3'].includes(params.get('quality'))?params.get('quality'):'',
   level:Number.isInteger(level)&&level>=1&&level<=125?level:50,zone:params.get('zone')||'',
   sort:['name','hp','mana','ac','ratio','rate'].includes(params.get('sort'))?params.get('sort'):'name',
   page:Number.isInteger(page)&&page>0?Math.min(page,100000):1,item:Number.isInteger(item)&&item>0&&item<=1048575?item:0};
 }
 function params(s) {
  const p=new URLSearchParams();
  if(s.classes.length)p.set('classes',s.classes.join(','));
  for(const [key,value] of Object.entries(s))if(!['classes','item','page'].includes(key)&&value!==''&&!(key==='match'&&value==='any')&&!(key==='sort'&&value==='name')&&!(key==='level'&&value===50))p.set(key,String(value));
  if(s.page>1)p.set('page',s.page); if(s.item)p.set('item',s.item); return p;
 }
 function quality(i) { return i.id<800000?Math.floor(i.id/200000):null; }
 function slotMask(slot) { if(slot==='')return 0; const n=Number(slot); return (1<<n)|(n===1?1<<4:n===9?1<<10:n===15?1<<16:0); }
 function filter(items,s) {
  const mask=s.classes.reduce((v,n)=>v|(1<<(n-1)),0),q=s.q.trim().toLowerCase(),slot=slotMask(s.slot);
  const rows=items.filter(i=>(!mask||(s.match==='all'?(i.classes&mask)===mask:!!(i.classes&mask)))&&
   (!q||i.name.toLowerCase().includes(q)||String(i.id)===q)&&i.reqlevel<=s.level&&
   (s.slot==='bag'?i.bagslots>0:!slot||!!(i.slots&slot))&&(!s.zone||i.zones.includes(s.zone))&&
   (s.quality===''||quality(i)===Number(s.quality)));
  const metric=i=>s.sort==='ratio'?(i.delay>0?i.damage/i.delay:0):s.sort==='rate'?i.best_rate:i[s.sort]||0;
  rows.sort((a,b)=>(s.sort==='name'?0:metric(b)-metric(a))||a.name.localeCompare(b.name)||a.id-b.id);
  return rows;
 }
 function slotNames(i){return i.bagslots?`${i.bagslots}-slot bag`:[...new Set(Object.entries(slots).filter(([bit])=>i.slots&(1<<Number(bit))).map(([,name])=>name))].join(', ')||'No equipment slot';}
 function classNames(mask){return classes.filter((_,i)=>mask&(1<<i)).join(', ')||'No listed class';}
 function percent(value){return value>0&&value<.01?'<0.01%':`${value.toFixed(2).replace(/\.00$/,'')}%`;}
 const api={classes,slots,state,params,filter,quality,slotNames,classNames,percent};
 if(typeof module==='object'&&module.exports)module.exports=api; else root.NightcapLoot=api;
})(typeof window==='undefined'?globalThis:window);
