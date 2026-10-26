"""Public, account-free diagnostic workbench. Data is a reviewed projection only."""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CLASSES = ['Warrior','Cleric','Paladin','Ranger','Shadowknight','Druid','Monk','Bard','Rogue','Shaman','Necromancer','Wizard','Magician','Enchanter','Beastlord','Berserker']


def field(key, title, low, high, step=1, scope='stat'):
    return f'<label>{title}<input id="lab-{key}" data-{scope}="{key}" type="number" min="{low}" max="{high}" step="{step}" required></label>'


def render():
    data = json.loads((ROOT/'build-lab-data.json').read_text(encoding='utf-8'))
    catalog = json.loads((ROOT/'catalog.json').read_text(encoding='utf-8'))
    data['items'] = [i for i in catalog['items'] if i['required_level'] <= 50]
    options = ''.join(f'<option value="{i+1}">{name}</option>' for i,name in enumerate(CLASSES))
    stats = ''.join(field(*args) for args in [
        ('sd','Spell Damage',0,5000),('ha','Heal Amount',0,5000),('hint','Heroic INT',0,2000),('hwis','Heroic WIS',0,2000),
        ('hp','Maximum HP',1,100000),('mana','Starting / maximum mana',0,100000),('regen','Mana per 6-second tick',0,10000),
        ('reserve','Mana reserved for healing',0,100000),('passive','Resolved melee + pet DPS',0,10000,0.1)])
    encounter = ''.join(field(*args,scope='encounter') for args in [
        ('duration','Fight duration · seconds',1,600,1),('incoming','Incoming damage · HP/second',0,10000,1),
        ('landed','Expected spell damage landed · %',0,100,1),('healAt','Heal below HP · %',1,99,1)])
    action_fields = ''.join(field(*args,scope='action') for args in [
        ('base','Resolved damage / heal per hit or tick',0,1000000,1),('cast','Cast / execution · seconds',0.1,60,0.1),
        ('recovery','Recovery · seconds',0,60,0.1),('cooldown','Reuse after completion · seconds',0,900,0.1),
        ('cost','Mana cost',0,100000,1),('ticks','DoT ticks · every 6 seconds',0,100,1)])
    return f'''<section id="build-lab" data-lab="{html.escape(json.dumps(data,separators=(',',':')),quote=True)}">
<noscript><p class="notice">The Build Lab needs JavaScript to calculate results. The model scope and guides below remain readable.</p></noscript>
<div class="lab-loading">Loading the workbench…</div><div class="lab-app" hidden>
<div class="lab-intro"><div><p class="eyebrow">BUILD · EXPERIMENT · COMPARE</p><p>One change. A different fight. Find out why.</p></div><span class="lab-tag">Experimental · Classic 50</span></div>
<div class="lab-toolbar"><div role="group" aria-label="Build to edit"><button type="button" data-build="0" aria-pressed="true">A · Starter control</button><button type="button" data-build="1" aria-pressed="false">B · Dungeon control</button></div><div><button id="lab-copy" type="button">Copy A → B</button><button id="lab-save" type="button">Save on this browser</button><button id="lab-share" type="button">Export / import</button></div></div>
<p id="lab-status" role="status" aria-live="polite">Two dated native stat controls are loaded. Edit the assumptions to explore your own build.</p><p id="lab-error" role="alert" hidden></p>
<div class="lab-workspace"><div class="lab-editor">
<form id="lab-build-form"><h2>At the workbench</h2><label>Build name<input id="lab-name" maxlength="80" required></label>
<div class="lab-classes">{''.join(f'<label>{"Primary class" if i==0 else "Class slot "+str(i+1)}<select data-class="{i}">{options}</select></label>' for i in range(3))}</div>
<p class="lab-help">Classes filter this small spell library. Other class, AA, buff and pet effects require resolved inputs.</p>
<details open><summary>Effective character stats</summary><div class="lab-fields">{stats}</div><p id="lab-caps" class="lab-help"></p></details>
</form>
<details class="lab-gear"><summary>Compare a gear upgrade</summary><p class="lab-help">Published Hunt rewards only. This compares raw item stats; it does not validate a full loadout, sockets or acquisition.</p>
<label>Current item<select id="lab-item-before"></select></label><label>Possible upgrade<select id="lab-item-after"></select></label><div id="lab-gear-delta"></div><button id="lab-apply-gear" type="button">Apply supported stat difference</button><p class="lab-help">Applies SD, HA, heroic INT/WIS, item HP and mana to the active inputs. Other stat conversions and item effects remain unmodeled.</p></details>
<details><summary>Test conditions</summary><form id="lab-encounter-form"><div class="lab-fields">{encounter}</div></form><p class="lab-help">A fixed-duration dummy with constant incoming damage. Landed % is your assumption; it is not a boss resist calculation. Resolved melee/pet DPS already includes misses and resists.</p></details>
</div><div class="lab-results">
<div class="lab-result-heading"><div><p class="eyebrow">THE SAME FIGHT. TWO APPROACHES.</p><h2>Your comparison</h2></div><span id="lab-condition-label"></span></div>
<div id="lab-metrics" class="lab-metrics" aria-live="polite"></div>
<div class="lab-chart-head"><h3>Mana through the fight</h3><span><i class="lab-key lab-key-a"></i> Build A <i class="lab-key lab-key-b"></i> Build B</span></div><div id="lab-mana-chart" class="lab-chart"></div>
<div class="lab-chart-head"><h3>Damage by ability</h3><span id="lab-breakdown-label"></span></div><div id="lab-breakdown"></div>
<section class="lab-rotation"><div class="lab-result-heading"><div><p class="eyebrow">YOUR NEXT MOVE</p><h2>Rotation workbench</h2></div><button type="button" id="lab-optimize">Find best priority order</button></div>
<p class="lab-help">Top priority wins when ready and affordable. Heals take priority below the HP threshold. DoTs refresh after their last tick; same-family DoTs do not stack.</p>
<div id="lab-actions"></div><div class="lab-add"><label>Level-50 spell library<select id="lab-spell"></select></label><button id="lab-add-spell" type="button">Add spell</button></div>
<details id="lab-custom"><summary>Add or edit a resolved ability</summary><p class="lab-help">Enter a measured or externally resolved effect. These values bypass gear scaling and do not prove an ability is legal or owned.</p>
<form id="lab-action-form"><div class="lab-fields"><label>Ability name<input id="lab-action-name" maxlength="80" required></label><label>Effect<select id="lab-kind"><option value="damage">Direct damage</option><option value="dot">Damage over time</option><option value="heal">Direct healing</option></select></label>{action_fields}<label>Shared timer / DoT family<input id="lab-group" maxlength="80" placeholder="Optional group name"></label></div><button type="submit" id="lab-action-submit">Add resolved ability</button><button id="lab-action-cancel" type="button" hidden>Cancel edit</button></form></details>
<p id="lab-search-status" role="status" aria-live="polite"></p><h3>Cast timeline <small id="lab-timeline-label"></small></h3><label class="lab-scrubber">Inspect second <output id="lab-time-label">0</output><input id="lab-time" type="range" min="0" max="60" step="1" value="0"></label><div id="lab-timeline"></div><p id="lab-moment" class="lab-help" aria-live="polite"></p>
<details><summary>Full cast log</summary><div id="lab-log" class="lab-log"></div></details>
</section></div></div>
<dialog id="lab-transfer" aria-labelledby="lab-transfer-heading"><div class="dialog-heading"><h2 id="lab-transfer-heading">Take your builds with you</h2><button type="button" id="lab-close-transfer" aria-label="Close build transfer">✕</button></div><p>Copy this versioned setup to share, or paste one to load both builds and conditions.</p><label>Build setup<textarea id="lab-transfer-text" rows="10" maxlength="40000" spellcheck="false"></textarea></label><button id="lab-import" type="button">Load pasted setup</button><p id="lab-import-status" role="status"></p></dialog>
</div></section>'''
