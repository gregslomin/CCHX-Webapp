from django.db import models

# Create your models here.
from django.db import models
from django.conf import settings



class Station(models.Model):
    name = models.CharField(max_length=255)
    station_id = models.CharField(max_length=255)

class DogmaAttribute(models.Model):
    attribute_id = models.IntegerField()
    value = models.FloatField()

class Item(models.Model):
    location_id = models.IntegerField()
    type_id = models.IntegerField()
    location_flag = models.CharField(max_length=128)
    location_type = models.CharField(max_length=128)
    mutator_type_id = models.IntegerField(default=-1)
    source_type_id = models.IntegerField(default=-1)
    character = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    attributes = models.ManyToManyField(DogmaAttribute)

class ItemType(models.Model):
    type_id = models.IntegerField()
    name = models.CharField(max_length=255)
    icon_id = models.IntegerField()
    group_id = models.IntegerField()

class AttributeType(models.Model):
    attr_id = models.IntegerField()
    name = models.CharField(max_length=255)
    displayName = models.CharField(max_length=255)



