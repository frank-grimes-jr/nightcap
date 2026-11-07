"""Exact reachable personal campaign rewards; separate from the Hunt directory."""
import html

def articles(data):
    e=html.escape;result=[]
    names=['Warrior','Cleric','Paladin','Ranger','Shadowknight','Druid','Monk','Bard','Rogue','Shaman','Necromancer','Wizard','Magician','Enchanter','Beastlord','Berserker']
    chapters=['The First Pages','Beneath the Surface','Steel and Sorcery','A Name Beneath the Moss','What the Fire Kept',"The Captain’s Last Watch",'Where Courage Ends','The Last Lantern']
    fits=['Woven','Leather','Chain','Plate'];grades=['Journey','Oathbound','Restored','Complete'];slots=['Feet','Hands','Left wrist','Right wrist','Arms','Legs','Head','Chest']
    def add(slug,title,summary,body):
        result.append(dict(slug=slug,title=title,summary=summary,body=body,category='Equipment',status=data['status'],updated=data['updated'],sources=data['sources']))
    links=''
    for fit in range(4):
        links+=f'<h2 id="{fits[fit].lower()}">{fits[fit]} outfit</h2><div class="table-scroll"><table><caption>Reachable {fits[fit].lower()} pieces and earned refits</caption><thead><tr><th>Item</th><th>Grade</th><th>Level</th><th>AC</th><th>HP</th><th>Mana</th></tr></thead><tbody>'
        for item in data['items']:
            n=item['id']-964000
            if n//32!=fit:continue
            grade=n%32//8;slot=n%8;classes=', '.join(name for i,name in enumerate(names) if item['classes']&(1<<i))
            stats={'Required level':item['reqlevel'],'Slot':slots[slot],'Fit':fits[fit],'Classes':classes,'AC':item['ac'],'HP':item['hp'],'Mana':item['mana']}
            for field,label in [('astr','STR'),('asta','STA'),('aagi','AGI'),('adex','DEX'),('aint','INT'),('awis','WIS'),('acha','CHA'),('mr','Magic resist'),('fr','Fire resist'),('cr','Cold resist'),('pr','Poison resist'),('dr','Disease resist')]:
                if item.get(field):stats[label]=item[field]
            stats['Augment socket']='Type22' if item.get('augslot1type')==22 else 'None'
            rows=''.join(f'<tr><th scope="row">{e(str(k))}</th><td>{e(str(v))}</td></tr>' for k,v in stats.items())
            source=f'Complete {chapters[slot]} and claim this piece from Oren Lanternwright in East Commonlands.'
            if grade:source+=f' The {grades[grade]} grade also requires '+['','What the Fire Kept','Where Courage Ends','the final campfire in The Last Lantern'][grade]+'. Refit the original piece with Oren.'
            body=f'<h2 id="stats">Item details</h2><table class="item-stats"><caption>{e(item["Name"])}</caption><tbody>{rows}</tbody></table><h2 id="source">Earn this item</h2><p>{e(source)}</p><p>Personal campaign equipment. No trading, shared-bank transfer, pet hand-in or merchant resale. Refits preserve augments, custom dye, binding and ornaments. Missing receipted items are not replaced for free. These are fixed journey grades; duplicate combining and Hunt forging do not upgrade them.</p><p><a href="adventure-journal.html#outfit">Campaign and refit rules</a> · <a href="last-lantern-equipment.html">All outfit pieces</a></p>'
            add('item-'+str(item['id']),item['Name'],f'{grades[grade]} {fits[fit].lower()} campaign armor · Level{item["reqlevel"]} · {slots[slot]}.',body)
            links+=f'<tr><td><a href="item-{item["id"]}.html">{e(item["Name"])}</a></td><td>{grades[grade]}</td><td>{item["reqlevel"]}</td><td>{item["ac"]}</td><td>{item["hp"]}</td><td>{item["mana"]}</td></tr>'
        links+='</tbody></table></div>'
    add('last-lantern-equipment','Last Lantern equipment','Eight earned pieces, four legal armor fits and earned progression refits.','<p>Personal progression armor from <a href="adventure-journal.html">The Last Lantern</a>. Each playthrough earns eight pieces. Select a fit allowed by a held class; these tables show every reachable item and earned refit. Oren offers the earned grade when its chapter and level requirements are met. The six major pieces have a type22 socket; wrists do not. These fixed grades are separate from Hunt qualities and their combining recipes.</p>'+links)
    add('item-900501',"Wayfarer’s Oath [Epic 0.5]",'Personal level35 oath charm with five earned attunements.','<h2 id="source">Earn your oath</h2><p>Complete the three shared journal chapters and at least one level35 oath path. Claim the personal charm from the Ancient Chronicler in East Commonlands, then choose an earned attunement. Additional paths unlock choices on the same charm.</p><h2 id="powers">One oath at a time</h2><p>Guardian, Striker, Arcanist, Warden and Binder powers share one ten-minute recovery. Switching attunement does not reset it. The charm has no armor or attribute budget; its earned power is the reward. No trading, pet hand-in or merchant resale. Missing receipted charms are not replaced for free.</p><p><a href="adventure-journal.html#oath-paths">Exact path trials and bounded powers</a></p>')
    return result
