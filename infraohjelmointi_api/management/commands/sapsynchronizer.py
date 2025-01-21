from django.core.management.base import BaseCommand, CommandError

from django.db import transaction
from ...services import SapApiService


class Command(BaseCommand):
    help = "Synchronize SAP costs. " + "\nUsage: python manage.py sapsynchronizer"

    def add_arguments(self, parser):
        """
        No arguments
        """

    @transaction.atomic
    def handle(self, *args, **options):
        SapApiService().sync_all_projects_from_sap(for_financial_statement=False)
