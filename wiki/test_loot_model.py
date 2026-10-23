import unittest
from loot_model import content_passes, drop_probability, quality_outputs, project
from loot_capture import FIELDS


def capture_fixture():
    def row(kind, **values):
        result={key.lower():0 for key in FIELDS[kind][1].split()}
        result.update(min_expansion=-1,max_expansion=-1,content_flags='',content_flags_disabled='')
        result.update(values)
        return result
    raw={kind:[] for kind in FIELDS}
    raw.update(era=0,era_name='Classic',captured_at='2026-10-23T00:00:00+00:00',default_ruleset=1)
    raw['zones']=[row('zones',short_name='test',long_name='Test zone',zoneidnumber=1)]
    raw['spawns']=[row('spawns',id=1,spawngroupID=1,zone='test',respawntime=60)]
    raw['spawn_entries']=[row('spawn_entries',spawngroupID=1,npcID=1,chance=100)]
    raw['npcs']=[row('npcs',id=1,name='a_test_mob',level=10,loottable_id=1)]
    raw['tables']=[row('tables',id=1)]
    raw['links']=[row('links',loottable_id=1,lootdrop_id=1,multiplier=1,probability=100)]
    raw['drops']=[row('drops',id=1)]
    raw['entries']=[row('entries',lootdrop_id=1,item_id=1,chance=50,multiplier=1)]
    raw['items']=[row('items',id=1,name='Test sword',slots=8192,classes=1)]
    return raw


def entry(item=1, chance=50, multiplier=1, **extra):
    return dict(item_id=item, chance=chance, multiplier=multiplier, **extra)


class LootModelTests(unittest.TestCase):
    def test_independent_rolls_use_global_multiplier(self):
        self.assertAlmostEqual(drop_probability([entry()], {1: 1}, 0, 0, 100, 1, 4), .9375)

    def test_weighted_pool_uses_all_items_including_non_equipment(self):
        self.assertAlmostEqual(drop_probability([entry(1, 10), entry(2, 90)], {1: 1}, 1, 1, 100, 1, 1), .1)

    def test_optional_weighted_rolls_and_minimum(self):
        # P(pool rolls)=1-(.9*.9)=.19; target share=.5
        self.assertAlmostEqual(drop_probability([entry(1, 10), entry(2, 10)], {1: 1}, 2, 0, 50, 1, 1), .5*(1-.905**2))
        self.assertAlmostEqual(drop_probability([entry(1, 10), entry(2, 10)], {1: 1}, 2, 1, 100, 1, 1), 1-.5*.905)

    def test_quality_is_per_copy_not_multiplied_after_at_least_one(self):
        self.assertAlmostEqual(drop_probability([entry(1, 100)], {1: .01}, 0, 0, 100, 1, 4), 1-.99**4)
        self.assertAlmostEqual(drop_probability([entry(1, 50, 3)], {1: .2}, 1, 1, 100, 1, 1), 1-.8*.9**2)

    def test_zero_and_boundary_cases(self):
        self.assertEqual(drop_probability([entry(1, 0)], {1: 1}, 1, 1, 100, 1, 1), 0)
        self.assertEqual(drop_probability([entry(1, 100)], {1: 1}, 0, 0, 0, 1, 4), 0)
        self.assertEqual(drop_probability([entry(1, 100)], {1: 1}, 1, 3, 100, 1, 1), 1)

    def test_over_100_is_a_weight_or_guaranteed_roll(self):
        self.assertAlmostEqual(drop_probability([entry(1,150),entry(2,50)],{1:1},1,0,100,1,1),.75)
        self.assertEqual(drop_probability([entry(1,150)],{1:1},0,0,100,1,1),1)

    def test_missing_quality_falls_back_to_normal(self):
        items={1: dict(id=1, slots=4, bagslots=0), 200001: dict(id=200001)}
        self.assertEqual(quality_outputs(items[1], items, [2000,500,100]), {1:.8,200001:.2})

    def test_content_flags_all_for_runtime_any_for_sql(self):
        row=dict(min_expansion=-1,max_expansion=0,content_flags='a,b',content_flags_disabled='c')
        self.assertFalse(content_passes(row,0,{'a'},{'c'}))
        self.assertTrue(content_passes(row,0,{'a'},{'c'},sql=True))
        self.assertFalse(content_passes(row,1,{'a','b'},{'c'}))
        self.assertFalse(content_passes(dict(content_flags_disabled='unknown'),0,set(),set()))

    def test_projection_preserves_source_and_excludes_nonpublic_fields(self):
        raw=capture_fixture();raw['items'][0]['private_note']='must not escape'
        index,details=project(raw)
        self.assertEqual(len(index['items']),1)
        self.assertEqual(details['1']['sources'][0]['rate'],[50,50])
        self.assertEqual(details['1']['sources'][0]['npc'],'a test mob')
        self.assertNotIn('private_note',details['1'])
        self.assertNotIn('minstatus',details['1'])

    def test_disabled_and_out_of_era_paths_cannot_expose_items(self):
        for kind,change in [('disabled_spawns',{'spawn2_id':1,'disabled':1}),
                            ('spawns',{'min_expansion':1}),('drops',{'content_flags':'unavailable'}),
                            ('zones',{'min_status':80}),('items',{'minstatus':80})]:
            raw=capture_fixture()
            if kind=='disabled_spawns':raw[kind].append(change)
            else:raw[kind][0].update(change)
            self.assertEqual(project(raw)[0]['items'],[],kind)

    def test_global_zero_filters_are_unrestricted_and_levels_are_resolved(self):
        raw=capture_fixture();raw['npcs'][0].update(loottable_id=0,maxlevel=11,rare_spawn=1,raid_target=1)
        raw['global_loot']=[dict(id=1,loottable_id=1,enabled=1,min_level=11,max_level=0,
            rare=0,raid=0,hot_zone=0,zone='',race='',**{'class':'','bodytype':''})]
        index,details=project(raw)
        self.assertEqual(details['1']['sources'][0]['rate'],[0,50])
        raw['npcs'][0]['skip_global_loot']=1
        self.assertEqual(project(raw)[0]['items'],[])

    def test_native_large_pool_default_precedes_missing_definitions(self):
        raw=capture_fixture();raw['links'][0].update(mindrop=1,droplimit=0)
        raw['entries'] += [raw['entries'][0]|{'item_id':100+i} for i in range(100)]
        raw['items'].append(raw['items'][0]|{'id':2,'slots':0})
        raw['entries'].append(raw['entries'][0]|{'item_id':2})
        # A mandatory roll followed by nine optional weighted rolls, even though
        # the available pool is small. Counting only existing items gives 50%.
        self.assertAlmostEqual(project(raw)[1]['1']['sources'][0]['rate'][0],100*(1-.5*.625**9))


if __name__=='__main__': unittest.main()
