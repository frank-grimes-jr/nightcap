sub EVENT_SPELL_EFFECT_CLIENT {
    return plugin::cairnwright_spell($client, $caster_id, $spell_id, $entity_list);
}

1;
