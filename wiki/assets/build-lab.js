(function () {
  'use strict';
  const root=document.querySelector('#build-lab[data-lab]');if(!root)return;
  const M=window.NightcapBuildLab, data=JSON.parse(root.dataset.lab), $=id=>root.querySelector('#lab-'+id);
  const escape=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const fmt=(n,d=0)=>Number(n).toLocaleString(undefined,{maximumFractionDigits:d});
  const copy=x=>structuredClone(x), storageKey='nightcap.build-lab.v1';
  const base={sd:39,ha:39,hint:0,hwis:0,hp:1809,mana:1237,regen:0,reserve:100,passive:0};
  const actions=['360','54','732','17'].map(id=>M.fromSpell(data.spells.find(s=>s.id===id)));
  let state={version:1,builds:[{name:'Starter control',classes:[11,2,12],stats:copy(base),actions:copy(actions)},
    {name:'Dungeon control',classes:[11,2,12],stats:{...base,sd:170,ha:170,hp:2643,mana:2142},actions:copy(actions)}],
    encounter:{duration:60,incoming:0,landed:100,healAt:60}};
  let active=0,results=[],searchToken=0,editing=null,sequence=0;
  try {const saved=localStorage.getItem(storageKey);if(saved){state=M.decode(saved,data.spells);$('status').textContent='Your saved builds are restored from this browser.';}}
  catch(e){$('status').textContent='Saved builds could not be loaded. The workbench works for this visit; export to keep a copy.';}
  const current=()=>state.builds[active];
  function error(message='') {$('error').hidden=!message;$('error').textContent=message?message+' Results below show the last valid setup.':'';$('optimize').disabled=!!message;}
  function invalidateSearch() {searchToken++;$('optimize').textContent='Find best priority order';$('optimize').disabled=false;$('search-status').textContent='';}
  function commit(next,message) {
    invalidateSearch();
    try {next.builds=next.builds.map(M.validateBuild);next.builds.forEach(b=>M.checkLibrary(b,data.spells));next.encounter=M.validateEncounter(next.encounter);}
    catch(e){error(e.message);return false;}
    state=next;invalidateSearch();error();if(message)$('status').textContent=message;render();return true;
  }
  function buttons() {
    root.querySelectorAll('[data-build]').forEach(el=>{const i=Number(el.dataset.build);el.textContent=`${i?'B':'A'} · ${state.builds[i].name}`;el.setAttribute('aria-pressed',String(i===active));});
    $('copy').textContent=`Copy ${active?'B → A':'A → B'}`;
  }
  function fillEditor() {
    const b=current();buttons();$('name').value=b.name;
    root.querySelectorAll('[data-class]').forEach(el=>{el.value=b.classes[Number(el.dataset.class)];});
    root.querySelectorAll('[data-stat]').forEach(el=>{el.value=b.stats[el.dataset.stat];});
    root.querySelectorAll('[data-encounter]').forEach(el=>{el.value=state.encounter[el.dataset.encounter];});
    $('caps').textContent=`Effective SD ${fmt(Math.min(750,b.stats.sd))} / HA ${fmt(Math.min(750,b.stats.ha))}. Each is capped at 750. Primary Cleric adds its 5% base-heal focus; other AA/focus/crit effects are not inferred.`;
  }
  function actionList() {
    const b=current();
    $('actions').innerHTML=b.actions.map((a,i)=>`<div class="lab-action"><span>${i+1}</span><div><label class="lab-action-title"><input type="checkbox" data-enable="${i}" ${a.enabled?'checked':''}><span>${escape(a.name)}</span></label><small>${fmt(M.spellValue(a,b.stats,b.classes[0]),1)} ${a.kind==='heal'?'healing':a.kind==='dot'?'damage / tick':'damage'} · ${fmt(a.mana)} mana · ${a.cast}s cast / ${a.cooldown}s reuse</small><small>${a.scaling==='spell'?escape(data.spells.find(s=>s.id===a.spell).evidence):'Resolved input · no further stat scaling'}${a.group?' · family '+escape(a.group):''}</small></div><div class="lab-action-buttons"><button type="button" data-move="${i}" data-direction="-1" aria-label="Move ${escape(a.name)} up" ${i===0?'disabled':''}>↑</button><button type="button" data-move="${i}" data-direction="1" aria-label="Move ${escape(a.name)} down" ${i===b.actions.length-1?'disabled':''}>↓</button>${a.scaling==='resolved'?`<button type="button" data-edit="${i}">Edit</button>`:''}<button type="button" data-remove="${i}" aria-label="Remove ${escape(a.name)}">Remove</button></div></div>`).join('')||'<p>No abilities selected. Add a spell or a resolved ability to begin.</p>';
    const available=data.spells.filter(s=>M.available(s,b.classes)&&!b.actions.some(a=>a.spell===s.id));
    $('spell').innerHTML=available.map(s=>`<option value="${s.id}">${escape(s.name)} · ${s.kind}</option>`).join('')||'<option value="">No more supported spells for these classes</option>';
    $('add-spell').disabled=!available.length;
  }
  function metrics() {
    const a=results[0],b=results[1];
    const specs=[['Sustained DPS',fmt(a.dps,1),fmt(b.dps,1),`B − A: ${fmt(b.dps-a.dps,1)} DPS`],
      ['First 10 seconds',fmt(a.burst,1),fmt(b.burst,1),'DPS over the opening window'],
      ['Mana remaining',fmt(a.mana),fmt(b.mana),`Starting A ${fmt(state.builds[0].stats.mana)} · B ${fmt(state.builds[1].stats.mana)}`],
      ['Effective healing',fmt(a.healing),fmt(b.healing),'Overhealing is excluded'],
      ['Survived',fmt(a.elapsed,1)+'s',fmt(b.elapsed,1)+'s',`Requested ${state.encounter.duration}s; DPS uses the full window`],
      ['First mana wait',a.firstStarved===null?'None':fmt(a.firstStarved,1)+'s',b.firstStarved===null?'None':fmt(b.firstStarved,1)+'s','Includes the reserved-mana limit']];
    $('metrics').innerHTML=specs.map(([name,av,bv,note])=>`<div class="lab-metric"><span>${name}</span><strong>A ${av} <span aria-hidden="true">/</span> B ${bv}</strong><small>${note}</small></div>`).join('');
    $('condition-label').textContent=`${state.encounter.duration}s · ${state.encounter.landed}% spell damage landed`;
    $('breakdown-label').textContent=`${active?'B':'A'} · ${current().name}`;
    const parts=Object.values(results[active].breakdown).filter(x=>x.kind!=='heal'),max=Math.max(1,...parts.map(p=>p.damage));
    $('breakdown').innerHTML=parts.map(p=>`<div class="lab-breakdown-row"><span>${escape(p.name)}</span><div class="lab-bar"><span data-width="${p.damage/max*100}"></span></div><span>${fmt(p.damage)}</span></div>`).join('')||'<p>No damage actions are selected.</p>';
    $('breakdown').querySelectorAll('[data-width]').forEach(el=>{el.style.width=el.dataset.width+'%';});
  }
  function chart() {
    if(!results.length)return;
    const w=Math.max(240,$('mana-chart').clientWidth),h=210,left=50,right=12,top=12,bottom=32;
    const maximum=Math.max(1,...state.builds.map(b=>b.stats.mana));
    const x=t=>left+t/state.encounter.duration*(w-left-right),y=m=>h-bottom-m/maximum*(h-top-bottom);
    let svg=`<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="Mana over time for build A (solid) and B (dashed). Exact remaining values are shown above.">`;
    for(let i=0;i<=2;i++){const m=maximum*i/2;svg+=`<line class="grid" x1="${left}" x2="${w-right}" y1="${y(m)}" y2="${y(m)}"/><text x="${left-8}" y="${y(m)+4}" text-anchor="end">${fmt(m)}</text>`;}
    for(let i=0;i<=3;i++){const t=state.encounter.duration*i/3;svg+=`<text x="${x(t)}" y="${h-8}" text-anchor="${i===3?'end':i===0?'start':'middle'}">${fmt(t)}s</text>`;}
    results.forEach((r,i)=>{svg+=`<polyline class="series-${i?'b':'a'}" fill="none" stroke-width="2" points="${r.trace.map(p=>`${x(p.time)},${y(p.mana)}`).join(' ')}"/>`;});
    $('mana-chart').innerHTML=svg+'</svg>';
  }
  function timeline() {
    const r=results[active],t=Math.min(Number($('time').value),state.encounter.duration),start=Math.min(Math.floor(t/30)*30,Math.max(0,state.encounter.duration-30)),end=Math.min(start+30,state.encounter.duration),span=end-start;
    $('time').max=state.encounter.duration;$('time-label').value=t+'s';$('timeline-label').textContent=`${fmt(start)}–${fmt(end)} seconds`;
    const lanes=current().actions.filter(a=>a.enabled);
    $('timeline').innerHTML=lanes.map(a=>`<div class="lab-lane"><span>${escape(a.name)}</span><div class="lab-lane-track" role="img" aria-label="${escape(a.name)} cast windows from ${start} to ${end} seconds">${r.timeline.filter(c=>c.id===a.id&&c.end>start&&c.start<end).map(c=>`<span class="lab-cast ${a.kind}" data-left="${Math.max(0,c.start-start)/span*100}" data-width="${(Math.min(c.end,end)-Math.max(c.start,start))/span*100}"></span>`).join('')}</div></div>`).join('');
    $('timeline').querySelectorAll('[data-width]').forEach(el=>{el.style.left=el.dataset.left+'%';el.style.width=el.dataset.width+'%';});
    const p=r.trace.filter(p=>p.time<=t).at(-1)||r.trace[0];
    const cast=r.timeline.find(c=>c.start<=t&&c.end>t);
    $('moment').textContent=p?`${active?'B':'A'} at ${t}s: ${fmt(p.mana)} mana · ${fmt(p.hp)} HP · ${fmt(p.damage)} damage. ${r.death!==null&&t>=r.death?'Simulation ended at death.':cast?'Casting '+cast.name+'.':'Between casts.'}`:'';
  }
  function render() {
    fillEditor();actionList();results=state.builds.map(b=>M.simulate(b,state.encounter));metrics();chart();timeline();
    const log=results[active].timeline;
    $('log').innerHTML=`<p class="lab-help">${log.length>300?'First 300 of '+log.length:log.length} casts; times are seconds.</p><table><thead><tr><th>Start</th><th>Finish</th><th>Ability</th></tr></thead><tbody>${log.slice(0,300).map(c=>`<tr><td>${fmt(c.start,1)}</td><td>${fmt(c.end,1)}${c.cancelled?' · stopped at death':''}</td><td>${escape(c.name)}</td></tr>`).join('')}</tbody></table>`;
  }
  root.querySelectorAll('[data-build]').forEach(el=>el.addEventListener('click',()=>{active=Number(el.dataset.build);invalidateSearch();error();cancelEdit();render();}));
  $('build-form').addEventListener('submit',e=>e.preventDefault());
  function updateBuild() {
    invalidateSearch();
    if(!$('build-form').checkValidity()){error('Complete the valid character inputs.');return;}
    const next=copy(state),b=next.builds[active];b.name=$('name').value;
    root.querySelectorAll('[data-stat]').forEach(el=>{b.stats[el.dataset.stat]=Number(el.value);});
    root.querySelectorAll('[data-class]').forEach(el=>{b.classes[Number(el.dataset.class)]=Number(el.value);});
    const before=b.actions.length;b.actions=b.actions.filter(a=>a.scaling!=='spell'||M.available(data.spells.find(s=>s.id===a.spell),b.classes));
    commit(next,before!==b.actions.length?'Spells unavailable to the new class combination were removed.':'Inputs updated. Save to keep this setup.');
  }
  $('build-form').addEventListener('input',updateBuild);
  $('build-form').addEventListener('change',updateBuild);
  $('encounter-form').addEventListener('submit',e=>e.preventDefault());
  function updateEncounter() {
    invalidateSearch();
    if(!$('encounter-form').checkValidity()){error('Complete the valid test conditions.');return;}
    const next=copy(state);root.querySelectorAll('[data-encounter]').forEach(el=>{next.encounter[el.dataset.encounter]=Number(el.value);});commit(next,'Both builds now use the updated test conditions.');
  }
  $('encounter-form').addEventListener('input',updateEncounter);
  $('encounter-form').addEventListener('change',updateEncounter);
  $('copy').addEventListener('click',()=>{const next=copy(state);next.builds[1-active]=copy(current());next.builds[1-active].name=current().name+' copy';commit(next,'Copied the active build. Change one input to compare its effect.');});
  $('save').addEventListener('click',()=>{try{localStorage.setItem(storageKey,JSON.stringify(state));$('status').textContent='Both builds and test conditions saved on this browser.';}catch(e){$('status').textContent='Browser storage is unavailable. Use Export / import to keep your setup.';}});
  $('share').addEventListener('click',()=>{$('transfer-text').value=JSON.stringify(state,null,2);$('import-status').textContent='';$('transfer').showModal();});
  $('close-transfer').addEventListener('click',()=>$('transfer').close());
  $('import').addEventListener('click',()=>{try{const next=M.decode($('transfer-text').value,data.spells);if(commit(next,'Imported both builds. Save to keep them on this browser.')){$('transfer').close();cancelEdit();}}catch(e){$('import-status').textContent='Could not load setup: '+e.message;}});
  $('actions').addEventListener('change',e=>{if(e.target.dataset.enable!==undefined){const next=copy(state);next.builds[active].actions[Number(e.target.dataset.enable)].enabled=e.target.checked;commit(next);}});
  $('actions').addEventListener('click',e=>{
    const target=e.target.closest('button');if(!target)return;
    const next=copy(state),list=next.builds[active].actions;
    if(target.dataset.remove!==undefined){list.splice(Number(target.dataset.remove),1);cancelEdit();commit(next);}
    if(target.dataset.move!==undefined){const i=Number(target.dataset.move),j=i+Number(target.dataset.direction);[list[i],list[j]]=[list[j],list[i]];commit(next);}
    if(target.dataset.edit!==undefined){const a=list[Number(target.dataset.edit)];editing=a.id;$('action-name').value=a.name;$('kind').value=a.kind;$('group').value=a.group;root.querySelectorAll('[data-action]').forEach(el=>{el.value=a[el.dataset.action==='cost'?'mana':el.dataset.action];});$('custom').open=true;$('action-submit').textContent='Update resolved ability';$('action-cancel').hidden=false;$('action-name').focus();}
  });
  $('add-spell').addEventListener('click',()=>{const s=data.spells.find(s=>s.id===$('spell').value);if(!s)return;const next=copy(state);next.builds[active].actions.push(M.fromSpell(s));commit(next);});
  function cancelEdit() {editing=null;$('action-submit').textContent='Add resolved ability';$('action-cancel').hidden=true;}
  $('action-cancel').addEventListener('click',cancelEdit);
  $('action-form').addEventListener('submit',e=>{
    e.preventDefault();const a={id:editing||'custom'+Date.now()+'_'+sequence++,name:$('action-name').value,kind:$('kind').value,group:$('group').value,scaling:'resolved',enabled:true,spell:''};
    root.querySelectorAll('[data-action]').forEach(el=>{a[el.dataset.action==='cost'?'mana':el.dataset.action]=Number(el.value);});
    if(a.kind!=='dot')a.ticks=0;
    const next=copy(state),list=next.builds[active].actions,index=list.findIndex(v=>v.id===editing);if(index>=0)list[index]=a;else list.push(a);
    if(commit(next,'Resolved ability updated. Verify its inputs against your own combat measurements.'))cancelEdit();
  });
  $('optimize').addEventListener('click',async()=>{
    const token=++searchToken,which=active,before=results[active];$('optimize').disabled=true;$('optimize').textContent='Testing orders…';
    const result=await M.optimize(copy(current()),state.encounter,{cancelled:()=>token!==searchToken,progress:n=>{$('search-status').textContent=`Tested ${n} priority orders…`;}});
    if(!result||token!==searchToken)return;
    state.builds[which]=result.build;render();$('optimize').disabled=false;$('optimize').textContent='Find best priority order';
    $('search-status').textContent=`Tested ${result.tested} orders. Best found: ${fmt(result.result.dps,1)} DPS (${fmt(result.result.dps-before.dps,1)} change). Survival first, damage second. Healing priority stays fixed; this does not search spell subsets, gear, AA choices or waiting strategies.`;
  });
  $('time').addEventListener('input',timeline);
  function gearOptions() {
    const items=data.items;const before=items.find(i=>String(i.id)===$('item-before').value);
    const choices=items.filter(i=>i.kind===before.kind&&i.slot===before.slot);
    $('item-after').innerHTML=choices.map(i=>`<option value="${i.id}">${escape(i.name)}</option>`).join('');
    const upgrade=choices.find(i=>i.zone===before.zone&&i.tier===Math.min(3,before.tier+1));$('item-after').value=upgrade?.id??before.id;gearDelta();
  }
  function gearDelta() {
    const a=data.items.find(i=>String(i.id)===$('item-before').value),b=data.items.find(i=>String(i.id)===$('item-after').value),keys=[...new Set([...Object.keys(a.stats),...Object.keys(b.stats)])];
    const rows=keys.map(k=>[k,(b.stats[k]||0)-(a.stats[k]||0)]).filter(([,v])=>v);
    $('gear-delta').innerHTML=`<div class="lab-delta">${rows.map(([k,v])=>`<span>${escape(k)} ${v>0?'+':''}${fmt(v)}</span>`).join('')||'No raw stat difference.'}</div><a href="item-${a.id}.html">Current item</a> · <a href="item-${b.id}.html">Upgrade details</a>`;
  }
  $('item-before').innerHTML=data.items.map(i=>`<option value="${i.id}">${escape(i.name)} · ${escape(i.kind)}</option>`).join('');
  $('item-before').addEventListener('change',gearOptions);$('item-after').addEventListener('change',gearDelta);
  $('apply-gear').addEventListener('click',()=>{
    const a=data.items.find(i=>String(i.id)===$('item-before').value),b=data.items.find(i=>String(i.id)===$('item-after').value),next=copy(state);
    const map={'Spell Damage':'sd','Healing Amount':'ha','Heroic INT':'hint','Heroic WIS':'hwis','HP':'hp','Mana':'mana'};
    for(const [key,stat] of Object.entries(map))next.builds[active].stats[stat]+=(b.stats[key]||0)-(a.stats[key]||0);
    if(commit(next,'Applied the supported raw stat difference once. Indirect stat conversions, sockets and other item effects are not included.')){$('item-before').value=b.id;gearOptions();$('item-after').value=b.id;gearDelta();}
  });
  root.querySelector('.lab-loading').hidden=true;root.querySelector('.lab-app').hidden=false;
  root.querySelectorAll('[data-action]').forEach(el=>{el.value={base:100,cast:1,recovery:1.5,cooldown:0,cost:0,ticks:0}[el.dataset.action];});
  gearOptions();render();
  new ResizeObserver(()=>chart()).observe($('mana-chart'));
})();
