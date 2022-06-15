from django.db import models

# Create your models here.
from django.db import models
from django.conf import settings



class Station(models.Model):
    name = models.CharField(max_length=255)
    station_id = models.CharField(max_length=255)


class Item(models.Model):
    item_id = models.IntegerField()
    location_id = models.IntegerField()
    type_id = models.IntegerField()
    location_flag = models.CharField(max_length=128)
    location_type = models.CharField(max_length=128)
    character = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
