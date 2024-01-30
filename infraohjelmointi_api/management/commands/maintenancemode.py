import os
import traceback

from django.core.management.base import BaseCommand
from infraohjelmointi_api.services import MaintenanceModeService

import logging
logger = logging.getLogger("infraohjelmointi_api")

class Command(BaseCommand):
    help = (
        "Set maintenance mode on/off."
        + "\nUsage: python manage.py maintenancemode --isMaintenanceModeOn <bool>"
    )

    def add_arguments(self, parser):
        """
        Add the following arguments to the hierarchies command

        --file /folder/file.xlsx
        """
        parser.add_argument(
            "--isMaintenanceModeOn",
            type=str,
            help=(
                "Argument to set maintenance mode on/off "
                + "Usage: --isMaintenanceModeOn <bool>"
            ),
            default="",
        )


    def handle(self, *args, **options):
        if not options["isMaintenanceModeOn"]:
            self.stdout.write(
                self.style.ERROR(
                    "No arguments given. "
                    + "\nUsage: python manage.py maintenancemode --isMaintenanceModeOn <bool>"
                )
            )
            return
        
        elif options["isMaintenanceModeOn"] in ["False", "false"]:
            try:
                self.setMaintenanceMode(isMaintenanceModeOn=False)
                self.stdout.write(
                    self.style.SUCCESS(
                        "Done."
                    )
                )
            except Exception as e:
                traceback.print_stack(e)
                self.stdout.write(self.style.ERROR(e))

        elif options["isMaintenanceModeOn"] in ["True", "true"]:
            try:
                self.setMaintenanceMode(isMaintenanceModeOn=True)
                self.stdout.write(
                    self.style.SUCCESS(
                        "Done."
                    )
                )
            except Exception as e:
                traceback.print_stack(e)
                self.stdout.write(self.style.ERROR(e))


    def setMaintenanceMode(self, isMaintenanceModeOn: bool):
        setMode = MaintenanceModeService.update_or_create(
                    value=isMaintenanceModeOn
                )
        if setMode:
            logger.info("\nMaintenance mode was set to: {}\n".format(
                        setMode.value
                    ))