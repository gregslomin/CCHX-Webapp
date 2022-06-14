from django.db import models


class Character(models.Model):
    name = models.CharField(max_length=255)
    identifier = models.CharField(max_length=255)
    session_id = models.CharField(max_length=255)


class Station(models.Model):
    name = models.CharField(max_length=255)
    station_id = models.CharField(max_length=255)


class Item(models.Model):
    item_id = models.CharField(max_length=255)
    name = models.CharField(max_length=255)

    class Meta:
        abstract = True
