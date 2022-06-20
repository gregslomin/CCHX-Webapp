from django.core.management.base import BaseCommand, CommandError
from webapp.models import *
from zipfile import ZipFile
import requests
import os
import shutil
from tqdm import tqdm
import yaml
from django.db import transaction

class Command(BaseCommand):
    help = 'Load SDE'

    @transaction.atomic
    def handle(self, *args, **options):
        with requests.get("https://eve-static-data-export.s3-eu-west-1.amazonaws.com/tranquility/sde.zip", stream=True) as r:
            # check header to get content length, in bytes
            total_length = int(r.headers.get("Content-Length"))

            # implement progress bar via tqdm
            with tqdm.wrapattr(r.raw, "read", total=total_length, desc="")as raw:

                # save the output to a file
                with open(f"{os.path.basename(r.url)}", 'wb')as output:
                    shutil.copyfileobj(raw, output)
        zf = ZipFile('sde.zip')
        print('Unzipping typeIDs.yaml')
        data = zf.read('sde/fsd/typeIDs.yaml')
        print('Parsing typeIDs yaml')
        typeids = yaml.load(data)
        print('Deleting existing ItemType models')
        ItemType.objects.all().delete()
        print('Writing new typeID models')
        for type_id in tqdm(typeids):
            type_id_data = typeids[type_id]
            ItemType(type_id=type_id,
                     name=type_id_data['name']['en'],
                     icon_id=type_id_data.get('icon_id', 0),
                     group_id=type_id_data.get('group_id', 0)).save()

        print('Unzipping dogmaAttribute.yaml')
        data = zf.read('sde/fsd/dogmaAttributes.yaml')
        print('Parsing DogmaAttribute yaml')
        typeids = yaml.load(data)
        print('Deleting existing AttributeType models')
        AttributeType.objects.all().delete()
        print('Writing new AttributeType models')
        for attr_id in tqdm(typeids):
            attr_id_data = typeids[attr_id]
            AttributeType(attr_id=attr_id,
                          name=attr_id_data['name'],
                          displayName=attr_id_data.get('displayNameID', {}).get('en', '')).save()


