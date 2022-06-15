from django.shortcuts import render

# Create your views here.
from esi.decorators import token_required
from django.http import HttpResponse
from pprint import pprint
from esi.clients import EsiClientProvider
esi = EsiClientProvider()

from .models import Item

@token_required(scopes="esi-assets.read_assets.v1")
def FetchAssets(request, token):
    access_token = token.valid_access_token()
    assets = esi.client.Assets.get_characters_character_id_assets(character_id=token.character_id,
                                                                  token=access_token).results()

    for asset in assets:
        item = Item(item_id=asset['item_id'],
                    type_id=asset['type_id'],
                    location_flag=asset['location_flag'],
                    location_id=asset['location_id'],
                    location_type=asset['location_type'],
                    character=request.user)
        item.save()

    pprint(assets)

    return HttpResponse(status=200)
