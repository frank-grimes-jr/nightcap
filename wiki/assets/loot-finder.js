(function () {
 'use strict';
 const root=document.getElementById('loot-finder'); if(!root)return;
 const model=window.NightcapLoot, byId=id=>document.getElementById(id);
 const form=byId('loot-filters'), checks=[...form.querySelectorAll('[name=classes]')];
 let data=null, state=model.state(new URLSearchParams(location.search)), generation=0, detailController=null;
 const pageSize=20, controls=['query','match','slot','quality','level','zone','sort'];
 function node(tag,text,className){const el=document.createElement(tag);if(text!==undefined)el.textContent=text;if(className)el.className=className;return el;}
 function url(value){const p=model.params(value).toString();return 'loot-finder.html'+(p?'?'+p:'');}
 function navigate(next,push=true){state=next;history[push?'pushState':'replaceState']({},'',url(state));sync();render();if(push&&!state.item){const heading=byId('loot-result-title');heading.tabIndex=-1;heading.focus();}}
 function sync(){checks.forEach(c=>{c.checked=state.classes.includes(Number(c.value));});controls.forEach(key=>byId('loot-'+key).value=state[key==='query'?'q':key]);}
 function showError(message){const box=byId('loot-error');box.hidden=false;box.querySelector('p').textContent=message;}
 function clearError(){byId('loot-error').hidden=true;}
 function readFilters(){return {...state,classes:checks.filter(c=>c.checked).map(c=>Number(c.value)),q:byId('loot-query').value,match:byId('loot-match').value,slot:byId('loot-slot').value,quality:byId('loot-quality').value,level:Number(byId('loot-level').value)||50,zone:byId('loot-zone').value,sort:byId('loot-sort').value,page:1,item:0};}
 function select(event){
  if(event.target.name==='classes'&&checks.filter(c=>c.checked).length>3){event.target.checked=false;byId('loot-selection').textContent='Choose up to three held classes.';return;}
  if(!form.checkValidity())return;
  navigate(model.state(model.params(readFilters())),false);
 }
 form.addEventListener('submit',event=>{event.preventDefault();select(event);});
 form.addEventListener('input',select);
 byId('loot-reset').addEventListener('click',()=>navigate(model.state(new URLSearchParams())));
 byId('loot-prev').addEventListener('click',()=>navigate({...state,page:state.page-1}));
 byId('loot-next').addEventListener('click',()=>navigate({...state,page:state.page+1}));
 byId('loot-back').addEventListener('click',event=>{event.preventDefault();navigate({...state,item:0});});
 window.addEventListener('popstate',()=>{state=model.state(new URLSearchParams(location.search));sync();render();});
 byId('loot-retry').addEventListener('click',()=>load());
 function render(){
  if(!data)return;
  clearError();
  byId('loot-selection').textContent=state.classes.length?state.classes.map(n=>model.classes[n-1]).join(' · '):'All classes';
  byId('loot-search-panel').hidden=!!state.item;byId('loot-detail').hidden=!state.item;
  if(state.item){renderDetail();return;}
  ++generation;if(detailController)detailController.abort();
  const rows=model.filter(data.items,state),pages=Math.max(1,Math.ceil(rows.length/pageSize));
  if(state.page>pages){state.page=pages;history.replaceState({},'',url(state));}
  byId('loot-count').textContent=`${rows.length.toLocaleString()} matching ${rows.length===1?'item':'items'}`;
  byId('loot-page').textContent=`Page ${state.page} of ${pages}`;
  byId('loot-prev').disabled=state.page<=1;byId('loot-next').disabled=state.page>=pages;
  const target=byId('loot-results');target.replaceChildren();target.setAttribute('aria-busy','false');
  if(!rows.length){target.append(node('p','No items match these filters. Try another slot or zone, raise the required level, or reset the filters.','notice'));return;}
  const table=node('table',undefined,'loot-results-table'),thead=node('thead'),head=node('tr');
  ['Item / slot','Stats','Sources','Best chance'].forEach(label=>{const th=node('th',label);th.scope='col';head.append(th);});thead.append(head);table.append(thead);
  const body=node('tbody');
  rows.slice((state.page-1)*pageSize,state.page*pageSize).forEach(item=>{
   const tr=node('tr'),name=node('td'),link=node('a',item.name);link.href=url({...state,item:item.id});
   link.addEventListener('click',event=>{if(event.ctrlKey||event.metaKey||event.shiftKey||event.altKey)return;event.preventDefault();navigate({...state,item:item.id});});
   name.append(link,node('small',model.slotNames(item)),node('small',`Required ${item.reqlevel||1} · #${item.id}`));
   const stats=node('td');stats.append(node('span',`${item.ac} AC · ${item.hp} HP`),node('small',`${item.mana} mana${item.damage?' · '+item.damage+'/'+item.delay+' damage/delay':''}`));
   const sources=node('td',`${item.sources} ${item.sources===1?'mob':'mobs'}`);sources.append(node('small',`${item.zones.length} ${item.zones.length===1?'zone':'zones'}`));
   tr.append(name,stats,sources,node('td',model.percent(item.best_rate),'loot-number'));body.append(tr);
  });table.append(body);target.append(table);
 }
 async function json(url,signal){const response=await fetch(url,{signal,credentials:'omit',cache:'no-cache'});if(!response.ok)throw new Error('unavailable');return response.json();}
 async function load(){
  clearError();byId('loot-freshness').textContent='Loading production loot data…';
  try{
   const fresh=await json(root.dataset.index);
   if(fresh.schema!==1||!Array.isArray(fresh.items)||!fresh.items.length||!/^\/[a-z-]+\/[a-f0-9]{16}\/$/.test(fresh.base_url)||!Number.isFinite(Date.parse(fresh.captured_at)))throw new Error('invalid');
   data=fresh;const age=(Date.now()-Date.parse(data.captured_at))/60000;
   byId('loot-freshness').textContent=`${data.era_name} · ${data.items.length.toLocaleString()} items · Captured ${new Date(data.captured_at).toLocaleString()} · Refreshes every ${data.refresh_minutes} minutes${age>45?' · Refresh delayed; showing the last successful capture.':''}`;
   const era=byId('loot-era');era.replaceChildren(new Option(`${data.era_name} — active production era`,'current'));
   const zone=byId('loot-zone');zone.replaceChildren(new Option('Any zone',''));
   Object.entries(data.zones).sort((a,b)=>a[1].localeCompare(b[1])).forEach(([key,title])=>zone.add(new Option(title,key)));
   if(state.zone&&!Object.hasOwn(data.zones,state.zone))state.zone='';
   sync();render();
  }catch(error){byId('loot-freshness').textContent='Production loot data is unavailable.';showError('The loot data could not be loaded. Your filters are preserved. Try again in a moment.');byId('loot-results').setAttribute('aria-busy','false');}
 }
 function statList(item){
  const fields={ac:'AC',hp:'HP',mana:'Mana',endur:'Endurance',damage:'Damage',delay:'Delay',haste:'Haste',regen:'HP regen',manaregen:'Mana regen',spelldmg:'Spell damage',healamt:'Heal amount',attack:'Attack',accuracy:'Accuracy',astr:'STR',asta:'STA',aagi:'AGI',adex:'DEX',awis:'WIS',aint:'INT',acha:'CHA',mr:'Magic resist',fr:'Fire resist',cr:'Cold resist',dr:'Disease resist',pr:'Poison resist',heroic_str:'Heroic STR',heroic_sta:'Heroic STA',heroic_agi:'Heroic AGI',heroic_dex:'Heroic DEX',heroic_wis:'Heroic WIS',heroic_int:'Heroic INT',heroic_cha:'Heroic CHA'};
  const dl=node('dl',undefined,'loot-stats');Object.entries(fields).filter(([key])=>item[key]).forEach(([key,label])=>{const cell=node('div');cell.append(node('dt',label),node('dd',String(item[key])));dl.append(cell);});return dl;
 }
 async function renderDetail(){
  const token=++generation;if(detailController)detailController.abort();detailController=new AbortController();
  const target=byId('loot-item');target.replaceChildren(node('p','Loading item and drop locations…'));target.setAttribute('aria-busy','true');
  byId('loot-back').href=url({...state,item:0});
  try{
   const item=await json(data.base_url+`item-${state.item}.json`,detailController.signal);
   if(token!==generation)return;if(item.id!==state.item||!Array.isArray(item.sources))throw new Error('invalid');
   target.replaceChildren();const title=node('h2',item.name);title.tabIndex=-1;target.append(title);
   target.append(node('p',`${model.slotNames(item)} · Required level ${item.reqlevel||1} · Recommended ${item.reclevel||1} · Item #${item.id}`));
   target.append(node('p',`Classes: ${model.classNames(item.classes)}`));
   if(item.deity)target.append(node('p',`Deity restriction mask: ${item.deity}. Check your deity in game; class matching alone does not remove this restriction.`,'notice'));
   target.append(statList(item),node('h3','Where it drops'));
   target.append(node('p','Chance of at least one copy from a newly generated NPC’s database loot. Includes the zone’s loot multiplier and this quality’s upgrade roll. Spawn selection is separate. Level ranges can change the chance.','loot-conditions'));
   let visible=0;const more=node('button','Show more mobs');more.type='button';
   const appendSources=()=>{const next=item.sources.slice(visible,visible+25);next.forEach(source=>target.insertBefore(sourceNode(source),more));visible+=next.length;more.hidden=visible>=item.sources.length;more.textContent=`Show more mobs (${item.sources.length-visible} remaining)`;};
   target.append(more);more.addEventListener('click',appendSources);appendSources();title.focus();
  }catch(error){if(error.name==='AbortError'||token!==generation)return;target.replaceChildren(node('p','This item’s captured data is unavailable. It may have changed or the capture may have expired.','notice'));showError('Refresh the production data and try this item again.');}
  finally{if(token===generation)target.setAttribute('aria-busy','false');}
 }
 function sourceNode(source){
  const section=node('section',undefined,'loot-source');section.append(node('h3',`${source.npc} — ${source.zone_name}`));
  const rates=source.rate[0]===source.rate[1]?model.percent(source.rate[0]):`${model.percent(source.rate[0])}–${model.percent(source.rate[1])}`;
  section.append(node('p',rates+' per kill','loot-rate'),node('p',`Level ${source.level[0]===source.level[1]?source.level[0]:source.level.join('–')} · ${source.zone} · NPC #${source.npc_id}`));
  if(source.looter_levels.length)section.append(node('p',`Loot eligibility has level gates: ${source.looter_levels.map(r=>`${r[0]||'no minimum'} to ${r[1]||'no maximum'}`).join('; ')}. The rate above describes generation, not a guarantee that your character can loot it.`,'loot-conditions'));
  const details=node('details'),summary=node('summary',`${source.locations.length} spawn ${source.locations.length===1?'location':'locations'} and conditions`),list=node('ul');
  source.locations.forEach(point=>{const li=node('li'),loc=node('code',`/loc ${point.y}, ${point.x}, ${point.z}`);li.append(loc,document.createTextNode(` · Respawn ${(point.respawn/60).toFixed(1)} min${point.variance?' ± '+(point.variance/60).toFixed(1)+' min':''} · Spawn weight ${point.spawn_weight}`));
   const conditions=[];if(point.condition)conditions.push(`spawn condition ${point.condition}=${point.condition_value}`);if(point.entry_filter)conditions.push(`entry filter ${point.entry_filter}`);if(point.min_time&&point.max_time)conditions.push(`game hours ${point.min_time}–${point.max_time}`);if(point.path)conditions.push('roaming path; coordinates are its starting point');
   if(conditions.length)li.append(node('small',' · '+conditions.join(' · ')));list.append(li);});
  details.append(summary,list);section.append(details);return section;
 }
 sync();load();
})();
