from django.shortcuts import render

# Create your views here.
from esi.decorators import token_required
from django.http import HttpResponse
from pprint import pprint
from esi.clients import EsiClientProvider
esi = EsiClientProvider()

from .models import Item, DogmaAttribute

@token_required(scopes="esi-assets.read_assets.v1")
def FetchAssets(request, token):
    access_token = token.valid_access_token()
    assets = esi.client.Assets.get_characters_character_id_assets(character_id=token.character_id,
                                                                  token=access_token).results()

    item_ids = [x['item_id'] for x in assets]
    asset_names = esi.client.Assets.post_characters_character_id_asset_names(character_id=token.character_id,
                                                                             item_ids=item_ids,
                                                                             token=access_token).results()
    asset_name_map = {x['item_id']: x['name'] for x in asset_names}

    for asset in assets:
        item = Item(item_id=asset['item_id'],
                    type_id=asset['type_id'],
                    location_flag=asset['location_flag'],
                    location_id=asset['location_id'],
                    location_type=asset['location_type'],
                    name=asset_name_map.get(asset['item_id'], ''),
                    character=request.user)
        item.save()

        dogma = esi.client.Dogma.get_dogma_dynamic_items_type_id_item_id(type_id=item.type_id, item_id=item.item_id).results()
        for attribute in dogma['dogma_attributes']:
            DogmaAttribute(attribute_id=attribute['id'],
                           value=attribute['value'],
                           item=item).save()

    return HttpResponse(status=200)