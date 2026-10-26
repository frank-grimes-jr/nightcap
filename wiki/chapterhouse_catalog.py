"""Generate the curated expedition catalog separately from Classic Hunt pools."""
import html

def articles(data):
    result=[]
    def add(slug,title,summary,body,category):
        result.append(dict(slug=slug,title=title,summary=summary,body=body,category=category,
                           status=data['status'],updated=data['updated'],sources=data['sources']))
    links=''.join(f'<li><a href="item-{i["id"]}.html">{html.escape(i["name"])}</a> · {i["kind"]}</li>' for i in data['items'])
    body='<p>Chapterhouse is a curated level-50 capstone reached through the Keeper near Befallen in West Commonlands. Start <a href="camil-vigil.html">The Vigil of the Dawn</a> with Camil in East Commonlands. The global era remains Classic.</p><h2 id="rewards">Published rewards</h2><ul>'+links+'</ul>'
    body+='<h2 id="eligibility">Reward rules</h2><p>Eligible static custom enemies have a 0.5% augment roll, followed by Base 60%, Polished 30%, Exalted 8% or Ascension 2%. Each of the three minibosses has a 35% chance to award its custom item. Final Raid rewards use the <a href="dungeon-modes.html">Raid reward system</a>. Summoned encounter shades award no loot or experience. Stock Rain of Fear loot is excluded.</p><p>The helmet is a one-time personal quest reward. Augment forging uses three identical Base copies, then four Polished or Exalted copies. Full encounter balance and player acceptance remain open.</p>'
    add('zone-chapterhouse','Chapterhouse of the Fallen','Custom Paladin capstone, encounter rewards and Ember augment · Live testing.',body,'World')
    for item in data['items']:
        values={'Item ID':item['id'],'Family':item['kind'],'Required level':item['required_level'],
                'Recommended level':item['recommended_level'],'Slot':item['slot'],'Classes':item['classes'],'MAGIC':'Yes' if item['magic'] else 'No',**item['stats']}
        rows=''.join('<tr><th scope="row">'+html.escape(str(k))+'</th><td>'+html.escape(str(v))+'</td></tr>' for k,v in values.items())
        body='<h2 id="stats">Item details</h2><table class="item-stats"><caption>Published values</caption><tbody>'+rows+'</tbody></table>'
        body+='<h2 id="source">Where to find it</h2><p>'+html.escape(item['source'])+'. See <a href="zone-chapterhouse.html">Chapterhouse reward rules</a>.</p>'
        if item['kind']=='Augment':
            body+='<p>Fits a type-22 socket in head, arms, hands, chest, legs or feet armor. Level and heroic headroom checks apply. Use <a href="zone-hunt.html#forging">#zoneforge</a>: three Base copies, then four Polished or Exalted copies. Ascension is the final quality.</p>'
        elif item['kind']=='Quest helmet':
            body+='<p>Delivered once by Camil after the story. A full inventory leaves the claim pending. The existing helmet appearance, stats and sockets are unchanged.</p>'
        else:body+='<p>This equipment does not use the Ember augment forging recipe.</p>'
        add('item-'+str(item['id']),item['name'],item['kind']+' · Chapterhouse · Live testing.',body,'Equipment')
    return result
