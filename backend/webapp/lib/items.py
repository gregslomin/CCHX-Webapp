from webapp.models import Item, Station, ItemType, AttributeType

def get_item_response(item, esi, token):
    item_res = {'item_id': item.id, 'type_id': item.type_id, 'location':item.get_location_string(esi, token), 'price':item.price}
    attr_map = {x.attribute_id:x.value for x in item.attributes.all()}
    try:
        if item.type_id == ItemType.objects.get(name='Abyssal Magnetic Field Stabilizer').type_id:
            damage_attr = AttributeType.objects.get(name='damageMultiplier').attr_id
            rof_attr = AttributeType.objects.get(name='speedMultiplier').attr_id
            cpu_attr = AttributeType.objects.get(name='cpu').attr_id
            pg_attr = AttributeType.objects.get(name='power').attr_id
            damage_modifier = attr_map[damage_attr]
            rof = attr_map[rof_attr]
            dps = ((damage_modifier / rof) - 1) * 100
            item_res['dps'] = round(dps, 3)
            item_res['rof'] = round((1 - rof) + 1, 3)
            item_res['damage'] = round(damage_modifier, 3)
            item_res['cpu'] = round(attr_map[cpu_attr], 3)
            item_res['power_grid'] = round(attr_map[pg_attr], 0)
    except Exception as e:
        print(e)
        print(attr_map)

    return item_res
