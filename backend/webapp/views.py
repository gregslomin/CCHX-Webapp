from django.shortcuts import render

# Create your views here.
from esi.decorators import token_required
from django.http import HttpResponse
from pprint import pprint
from esi.clients import EsiClientProvider
from tqdm import *
import json

esi = EsiClientProvider()

from .models import Item, DogmaAttribute

def list_assets(request):
    type_id = request.GET.get('type_id', None)

    assets = None
    if type_id:
        assets = Item.objects.filter(type_id=type_id, character=request.user)
    else:
        assets = Item.objects.filter(character=request.user)

    items = assets.all()

    item_response = []
    for item in items:
        item_res = {'item_id': item.id, 'type_id': item.type_id}
        attr_map = {x.attribute_id:x.value for x in item.attributes.all()}

        if item.type_id == 49722:
            damage_modifier = attr_map[64]
            rof = attr_map[204]
            dps = ((damage_modifier / rof) - 1) * 100
            item_res['dps'] = round(dps, 2)
            item_res['rof'] = round((1 - rof) + 1, 2)
            item_res['damage'] = round(damage_modifier, 2)

        item_response.append(item_res)

    return HttpResponse(json.dumps(item_response))

@token_required(scopes="esi-assets.read_assets.v1")
def fetch_assets(request, token):
    abyssal_type_ids = [49722, 49726, 47820, ]
    access_token = token.valid_access_token()
    assets = esi.client.Assets.get_characters_character_id_assets(character_id=token.character_id,
                                                                  token=access_token).results()

    old_assets = Item.objects.filter(character=request.user).all()
    old_asset_map = {x.id:x for x in old_assets}
    for asset in tqdm(assets):
        item, created = Item.objects.update_or_create(id=asset['item_id'],
                    type_id=asset['type_id'],
                    location_flag=asset['location_flag'],
                    location_id=asset['location_id'],
                    location_type=asset['location_type'],
                    character=request.user)

        if item.id in old_asset_map:
            del old_asset_map[item.id]

        if created or (item.type_id in abyssal_type_ids and item.mutator_type_id == -1):
            item.save()
            if item.type_id in abyssal_type_ids:
                try:
                    dogma = esi.client.Dogma.get_dogma_dynamic_items_type_id_item_id(item_id=item.id, type_id=item.type_id).results()
                    for attribute in dogma['dogma_attributes']:
                        attribute_object = DogmaAttribute(attribute_id=attribute['attribute_id'], value=attribute['value'])
                        attribute_object.save()
                        item.attributes.add(attribute_object)
                    item.mutator_type_id = dogma['mutator_type_id']
                    item.source_type_id = dogma['source_type_id']
                    item.save()
                except Exception as e:
                    print('{}'.format(e))
                    pass

        item.save()

    print("Deleting {}".format(old_asset_map.keys()))
    Item.objects.filter(id__in=old_asset_map.keys()).delete()


    return HttpResponse(status=200)
