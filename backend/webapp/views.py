import json
import csv
import io
import xlsxwriter

from django.http import HttpResponse
from django.shortcuts import redirect
from django.db import transaction
from esi.clients import EsiClientProvider
from esi.models import *
from webapp.lib import items as item_lib
from tqdm import *


esi = EsiClientProvider()

from .models import Item, DogmaAttribute, ItemType, AttributeType


def asset(request):
    item_id = request.GET.get('item_id', None)
    item = Item.objects.get(id=item_id)

    if request.method == request.POST:
        price = request.POST.get('price', None)
        if price:
            item.price = price
            item.save()

    return HttpResponse(json.dumps(item_lib.get_item_response(item, esi)))


def react_redirect(request):
    response = redirect('http://localhost:3000')
    return response

def list_assets(request):
    type_id = request.GET.get('type_id', None)
    location_string = request.GET.get('location', None)
    format = request.GET.get('format', 'json')
    sort = request.GET.get('sort', 'dps')
    eve_character = request.user.eve_character
    token = Token.get_token(eve_character.character_id, 'esi-assets.read_assets.v1')
    access_token = token.valid_access_token()

    assets = None
    if type_id:
        assets = Item.objects.filter(type_id=type_id, character=request.user)
    else:
        assets = Item.objects.filter(character=request.user)

    items = assets.all()

    item_response = []
    for item in items:
        if location_string:
            try:
                if location_string not in item.get_location_string(esi, access_token):
                    continue
            except:
                continue
        item_response.append(item_lib.get_item_response(item, esi, access_token))

    item_response.sort(reverse=True, key=lambda x: x.get(sort, 0))

    if 'json' in format:
        return HttpResponse(json.dumps(item_response))
    elif 'xls' in format:
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()
        bold = workbook.add_format({'bold': True})
        highlight = workbook.add_format()
        highlight.set_bg_color('#00ffff')
        normal = workbook.add_format()

        row = 0
        width = [40, 8, 8, 8, 8, 90, 50]
        header = ['name', 'dps', 'damage', 'rof', 'cpu', 'location', 'link']
        for x in range(len(header)):
            entry = header[x]
            worksheet.write(row, x, entry, bold)
            worksheet.set_column(x, x, width[x])


        for item in item_response:
            row += 1
            data = [ItemType.objects.get(type_id=item['type_id']).name, str(item.get('dps', ' '))+'%', str(item.get('damage', ' ')), str(item.get('rof', ' ')), str(item.get('cpu', ' ')), item['location'], 'https://mutaplasmid.space/module/{}'.format(item['item_id'])]
            for x in range(len(data)):
                entry = data[x]
                worksheet.write(row, x, entry, highlight if row % 2 == 0 else normal)
        workbook.close()
        return HttpResponse(output.getvalue(),
                            headers={'Content-Disposition': 'attachment; filename="abyssals.xlsx"'},
                            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    else:
        response = HttpResponse(
            content_type='text/csv',
            headers={'Content-Disposition': 'attachment; filename="abyssals.csv"'},
        )
        writer = csv.writer(response, delimiter='\t')
        writer.writerow(['name', 'dps', 'damage', 'rof', 'cpu', 'location', 'link'])
        for item in item_response:
            writer.writerow([ItemType.objects.get(type_id=item['type_id']).name, str(item.get('dps', ' '))+'%', str(item.get('damage', ' ')), str(item.get('rof', ' ')), str(item.get('cpu', ' ')), item['location'], 'https://mutaplasmid.space/module/{}'.format(item['item_id'])])
        return response

@transaction.atomic
def fetch_assets(request):
    eve_character = request.user.eve_character
    token = Token.get_token(eve_character.character_id, 'esi-assets.read_assets.v1')
    access_token = token.valid_access_token()

    valid_abyssals = ["Abyssal Magnetic Field Stabilizer", "Abyssal Heat Sink", "Abyssal Large Armor Plate"]
    abyssal_type_ids = [x.type_id for x in ItemType.objects.filter(name__in=valid_abyssals)]

    assets = esi.client.Assets.get_characters_character_id_assets(character_id=token.character_id,
                                                                  token=access_token).results()

    asset_names = []
    asset_ids = [x['item_id'] for x in assets]
    num_asset_ids = len(asset_ids)
    num_chunks = int(num_asset_ids / 900)
    remainder_chunk = True if num_asset_ids % 900 else False
    for x in range(num_chunks + 1 if remainder_chunk else 0):
        id_range = None
        if x <= num_chunks:
            id_range = asset_ids[x*900:(x+1)*900]
        elif remainder_chunk:
            asset_ids[x*900:num_asset_ids%900]
        asset_names_res = esi.client.Assets.post_characters_character_id_assets_names(character_id=token.character_id,
                                                                                      item_ids=id_range,
                                                                                      token=access_token).results()
        asset_names.extend(asset_names_res)

    asset_name_map = {x['item_id']:x['name'] for x in asset_names}

    old_assets = Item.objects.filter(character=request.user).all()
    old_asset_map = {x.id:x for x in old_assets}
    for asset in tqdm(assets):

        item, created = Item.objects.update_or_create(id=asset['item_id'],
                    type_id=asset['type_id'],
                    location_flag=asset['location_flag'],
                    location_id=asset['location_id'],
                    location_type=asset['location_type'],
                    custom_name=asset_name_map.get(asset['item_id'], ''),
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


    return HttpResponse(json.dumps(assets), status=200)
