"""Accessible shell for the production-backed item finder."""
import html

CLASSES = ['Warrior','Cleric','Paladin','Ranger','Shadow Knight','Druid','Monk','Bard',
           'Rogue','Shaman','Necromancer','Wizard','Magician','Enchanter','Beastlord','Berserker']
SLOTS = [(0,'Charm'),(1,'Ear'),(2,'Head'),(3,'Face'),(5,'Neck'),(6,'Shoulders'),(7,'Arms'),
         (8,'Back'),(9,'Wrist'),(11,'Range'),(12,'Hands'),(13,'Primary'),(14,'Secondary'),
         (15,'Finger'),(17,'Chest'),(18,'Legs'),(19,'Feet'),(20,'Waist'),(21,'Power source'),(22,'Ammo')]


def render():
    classes=''.join(f'<label class="loot-class"><input type="checkbox" name="classes" value="{i+1}"><span>{name}</span></label>' for i,name in enumerate(CLASSES))
    slots=''.join(f'<option value="{i}">{html.escape(name)}</option>' for i,name in SLOTS)
    return f'''<div id="loot-finder" data-index="/loot-data/current/index.json">
<div class="loot-intro"><p>Choose your classes. Find your next upgrade. Follow it to the source.</p><p id="loot-freshness" role="status">Loading production loot data…</p></div>
<div id="loot-error" class="notice" role="alert" hidden><p></p><button type="button" id="loot-retry">Try again</button></div>
<section id="loot-search-panel" aria-label="Find equipment">
<form id="loot-filters" autocomplete="off">
<fieldset><legend>Your held classes <small>Choose up to three</small></legend><div class="loot-classes">{classes}</div><p id="loot-class-hint">Any held class is enough to equip an item on Nightcap. Slot, level and deity restrictions still apply.</p></fieldset>
<div class="loot-controls">
<label>Item name or ID<input type="search" id="loot-query" maxlength="100" placeholder="e.g. Flowing Black Silk Sash"></label>
<label>Class matching<select id="loot-match"><option value="any">Any held class</option><option value="all">All selected classes</option></select></label>
<label>Era<select id="loot-era"><option value="current">Current production era</option></select></label>
<label>Slot<select id="loot-slot"><option value="">Any slot</option>{slots}<option value="bag">Bags</option></select></label>
<label>Quality<select id="loot-quality"><option value="">Any quality</option><option value="0">Normal</option><option value="1">Polished</option><option value="2">Exalted</option><option value="3">Ascended</option></select></label>
<label>Maximum required level<input type="number" id="loot-level" min="1" max="125" value="50"></label>
<label>Drop zone<select id="loot-zone"><option value="">Any zone</option></select></label>
<label>Sort by<select id="loot-sort"><option value="name">Name</option><option value="hp">HP, highest first</option><option value="mana">Mana, highest first</option><option value="ac">AC, highest first</option><option value="ratio">Damage / delay</option><option value="rate">Best drop chance</option></select></label>
</div><div class="loot-filter-actions"><button type="button" id="loot-reset">Reset filters</button><span id="loot-selection" aria-live="polite">All classes</span></div>
</form><div class="loot-result-heading"><h2 id="loot-result-title">Equipment</h2><p id="loot-count" role="status" aria-live="polite"></p></div>
<div id="loot-results" aria-busy="true"></div><div class="loot-pagination"><button type="button" id="loot-prev">← Previous</button><span id="loot-page" aria-live="polite"></span><button type="button" id="loot-next">Next →</button></div>
</section><section id="loot-detail" aria-label="Item and drop locations" hidden><a id="loot-back" href="loot-finder.html">← Back to results</a><div id="loot-item"></div></section>
<noscript><p>The production filters need JavaScript. Browse the <a href="items.html">Hunt equipment catalog</a> and <a href="dungeon-modes.html">dungeon rewards</a> without it.</p></noscript></div>'''
