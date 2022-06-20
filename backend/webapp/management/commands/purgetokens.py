from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from esi.models import *

class Command(BaseCommand):
    help = 'Delete all auth tokens'

    @transaction.atomic
    def handle(self, *args, **options):
        Token.objects.all().delete()