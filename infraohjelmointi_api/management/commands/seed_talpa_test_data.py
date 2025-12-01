"""
Management command to seed test data for Talpa dropdowns.

This creates sample data for UI development and testing.
Run with: python manage.py seed_talpa_test_data

Data is based on real values from the Excel files:
- SAP_Lajit ja prioriteetit 2025.xlsx
- Ohjelmointityökalu_projektinumerovälit.xlsx
- SAP_Projektinumerovälit.xlsx
- Projektin avauslomake Infra 27.10.2025.xlsx
"""

from django.core.management.base import BaseCommand
from infraohjelmointi_api.models import (
    TalpaProjectType,
    TalpaServiceClass,
    TalpaAssetClass,
    TalpaProjectNumberRange,
)


class Command(BaseCommand):
    help = "Seed test data for Talpa dropdowns (for UI development)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing Talpa test data before seeding",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self.stdout.write("Clearing existing Talpa data...")
            TalpaProjectType.objects.all().delete()
            TalpaServiceClass.objects.all().delete()
            TalpaAssetClass.objects.all().delete()
            TalpaProjectNumberRange.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("Cleared!"))

        self.seed_project_types()
        self.seed_service_classes()
        self.seed_asset_classes()
        self.seed_project_number_ranges()

        self.stdout.write(self.style.SUCCESS("\n✅ Talpa test data seeded successfully!"))
        self.stdout.write("\nData available at:")
        self.stdout.write("  - GET /api/talpa-project-types/")
        self.stdout.write("  - GET /api/talpa-service-classes/")
        self.stdout.write("  - GET /api/talpa-asset-classes/")
        self.stdout.write("  - GET /api/talpa-project-ranges/")

    def seed_project_types(self):
        """
        Seed TalpaProjectType with sample data from SAP_Lajit ja prioriteetit.
        
        The 'priority' field contains letter codes (A, B, C, etc.) from the PRIOR column.
        These letters identify sub-variants within a project type (e.g., different districts).
        """
        self.stdout.write("\nSeeding TalpaProjectType...")
        
        project_types = [
            # 2814I - Infrastructure Investment (Kadut, Puistot)
            # Code 8 03 01 01 - Uudisrakentaminen - different districts (A=Eteläinen, B=Läntinen, etc.)
            {
                "code": "8 03 01 01",
                "name": "Katujen uudisrakentaminen",
                "category": "KADUT, LIIKENNEVÄYLÄT JA RADAT",
                "priority": "A",  # Eteläinen suurpiiri
                "description": "Eteläinen suurpiiri",
                "isActive": True,
            },
            {
                "code": "8 03 01 01",
                "name": "Katujen uudisrakentaminen",
                "category": "KADUT, LIIKENNEVÄYLÄT JA RADAT",
                "priority": "B",  # Läntinen suurpiiri
                "description": "Läntinen suurpiiri",
                "isActive": True,
            },
            {
                "code": "8 03 01 01",
                "name": "Katujen uudisrakentaminen",
                "category": "KADUT, LIIKENNEVÄYLÄT JA RADAT",
                "priority": "C",  # Keskinen suurpiiri
                "description": "Keskinen suurpiiri",
                "isActive": True,
            },
            {
                "code": "8 03 01 01",
                "name": "Katujen uudisrakentaminen",
                "category": "KADUT, LIIKENNEVÄYLÄT JA RADAT",
                "priority": "D",  # Pohjoinen suurpiiri
                "description": "Pohjoinen suurpiiri",
                "isActive": True,
            },
            {
                "code": "8 03 01 01",
                "name": "Katujen uudisrakentaminen",
                "category": "KADUT, LIIKENNEVÄYLÄT JA RADAT",
                "priority": "E",  # Koillinen suurpiiri
                "description": "Koillinen suurpiiri",
                "isActive": True,
            },
            {
                "code": "8 03 01 01",
                "name": "Katujen uudisrakentaminen",
                "category": "KADUT, LIIKENNEVÄYLÄT JA RADAT",
                "priority": "F",  # Kaakkoinen suurpiiri
                "description": "Kaakkoinen suurpiiri",
                "isActive": True,
            },
            {
                "code": "8 03 01 01",
                "name": "Katujen uudisrakentaminen",
                "category": "KADUT, LIIKENNEVÄYLÄT JA RADAT",
                "priority": "G",  # Itäinen suurpiiri
                "description": "Itäinen suurpiiri",
                "isActive": True,
            },
            {
                "code": "8 03 01 01",
                "name": "Katujen uudisrakentaminen",
                "category": "KADUT, LIIKENNEVÄYLÄT JA RADAT",
                "priority": "H",  # Östersundomin suurpiiri
                "description": "Östersundomin suurpiiri",
                "isActive": True,
            },
            # Code 8 03 01 02 - Perusparantaminen ja liikennejärjestelyt
            {
                "code": "8 03 01 02",
                "name": "Katujen perusparantaminen ja liikennejärjestelyt",
                "category": "KADUT, LIIKENNEVÄYLÄT JA RADAT",
                "priority": "A",  # Eteläinen suurpiiri
                "description": "Eteläinen suurpiiri",
                "isActive": True,
            },
            {
                "code": "8 03 01 02",
                "name": "Katujen perusparantaminen ja liikennejärjestelyt",
                "category": "KADUT, LIIKENNEVÄYLÄT JA RADAT",
                "priority": "B",  # Läntinen suurpiiri
                "description": "Läntinen suurpiiri",
                "isActive": True,
            },
            # Code 8 03 03 - Yhteishankkeet (no district subdivision)
            {
                "code": "8 03 03",
                "name": "Yhteishankkeet Väyläviraston kanssa",
                "category": "KADUT, LIIKENNEVÄYLÄT JA RADAT",
                "priority": None,  # No sub-variant
                "description": "Yhteishankkeet valtion väyläviranomaisen kanssa",
                "isActive": True,
            },
            # Code 8 04 01 01 - Puistot
            {
                "code": "8 04 01 01",
                "name": "Uudet puistot ja puistojen peruskorjaus",
                "category": "PUISTORAKENTAMINEN",
                "priority": "A",  # Eteläinen suurpiiri
                "description": "Eteläinen suurpiiri",
                "isActive": True,
            },
            {
                "code": "8 04 01 01",
                "name": "Uudet puistot ja puistojen peruskorjaus",
                "category": "PUISTORAKENTAMINEN",
                "priority": "B",  # Läntinen suurpiiri
                "description": "Läntinen suurpiiri",
                "isActive": True,
            },
            # Code 8 04 01 02 - Liikuntapaikat
            {
                "code": "8 04 01 02",
                "name": "Liikuntapaikat ja ulkoilualueet",
                "category": "PUISTORAKENTAMINEN",
                "priority": None,  # No sub-variant in example
                "description": "Liikuntapaikkojen ja ulkoilualueiden rakentaminen",
                "isActive": True,
            },
            # 2814E - Pre-construction (Esirakentaminen)
            {
                "code": "8 01 03 01",
                "name": "Muu esirakentaminen",
                "category": "ESIRAKENTAMINEN",
                "priority": None,
                "description": "Muu esirakentaminen, alueiden käyttöönotto",
                "isActive": True,
                "notes": "2814E-projekti - vaatii Yksikkö-valinnan (Tontit/Mao/Geo)",
            },
            {
                "code": "8 08 01 02",
                "name": "Länsisatama esirakentaminen",
                "category": "PROJEKTIALUEIDEN ESIRAKENTAMINEN",
                "priority": None,
                "description": "Länsisataman alueen esirakentaminen",
                "isActive": True,
                "notes": "2814E-projekti",
            },
            {
                "code": "8 08 01 03",
                "name": "Kalasatama esirakentaminen",
                "category": "PROJEKTIALUEIDEN ESIRAKENTAMINEN",
                "priority": None,
                "description": "Kalasataman alueen esirakentaminen",
                "isActive": True,
                "notes": "2814E-projekti",
            },
            {
                "code": "8 09 01 01",
                "name": "Malminkartano-Kannelmäki esirakentaminen",
                "category": "KAUPUNKIUUDISTUSALUEET",
                "priority": None,
                "description": "Malminkartano-Kannelmäki KU esirakentaminen",
                "isActive": True,
                "notes": "2814E-projekti",
            },
            # Inactive example
            {
                "code": "8 08 01 01",
                "name": "Kamppi-Töölönlahti (EI KÄYTÖSSÄ)",
                "category": "PROJEKTIALUEIDEN ESIRAKENTAMINEN",
                "priority": None,
                "description": "Tämä ei enää käytössä",
                "isActive": False,
                "notes": "EI ENÄÄ KÄYTÖSSÄ - LAKKAUTETTU V. 2017 JÄLKEEN!",
            },
        ]

        created = 0
        for pt in project_types:
            # Use code + priority as unique identifier
            obj, was_created = TalpaProjectType.objects.update_or_create(
                code=pt["code"],
                priority=pt.get("priority"),  # Can be None
                defaults=pt,
            )
            if was_created:
                created += 1

        self.stdout.write(f"  Created {created} new, updated {len(project_types) - created} existing")

    def seed_service_classes(self):
        """Seed TalpaServiceClass with sample data"""
        self.stdout.write("\nSeeding TalpaServiceClass...")
        
        service_classes = [
            # For 2814I projects
            {
                "code": "4601",
                "name": "Kadut ja yleiset alueet",
                "description": "Katujen, kevyen liikenteen väylien, jalkakäytävien ja liikennealueiden viheralueiden suunnittelu, toteutus, kunnossapito ja puhtaanapito",
                "projectTypePrefix": "2814I",
                "isActive": True,
            },
            {
                "code": "4701",
                "name": "Puistot ja viheralueet",
                "description": "Puistojen ja viheralueiden suunnittelu, toteutus, kunnossapito ja puhtaanapito",
                "projectTypePrefix": "2814I",
                "isActive": True,
            },
            {
                "code": "3551",
                "name": "Liikunta- ja ulkoilupalvelut",
                "description": "Liikuntapaikkojen ja ulkoilualueiden suunnittelu, toteutus ja kunnossapito",
                "projectTypePrefix": "2814I",
                "isActive": True,
            },
            # For 2814E projects
            {
                "code": "5361",
                "name": "Maaomaisuuden hallinta",
                "description": "Maaomaisuuden hankinta, lunastaminen ja luovutus. Sisältää maaperätutkimukset, pilaantuneen maan puhdistamisen, kiinteistön kuntoarviot.",
                "projectTypePrefix": "2814E",
                "isActive": True,
            },
        ]

        created = 0
        for sc in service_classes:
            obj, was_created = TalpaServiceClass.objects.update_or_create(
                code=sc["code"],
                defaults=sc,
            )
            if was_created:
                created += 1

        self.stdout.write(f"  Created {created} new, updated {len(service_classes) - created} existing")

    def seed_asset_classes(self):
        """Seed TalpaAssetClass with sample data from Käyttöomaisuusluokat"""
        self.stdout.write("\nSeeding TalpaAssetClass...")
        
        asset_classes = [
            # Aineelliset hyödykkeet (no holding period)
            {
                "componentClass": "8103000",
                "account": "103000",
                "name": "Maa- ja vesialueet",
                "holdingPeriodYears": None,
                "hasHoldingPeriod": False,
                "category": "Aineelliset hyödykkeet",
                "isActive": True,
            },
            {
                "componentClass": "8103100",
                "account": "103100",
                "name": "Kiinteistöjen liittymismaksut",
                "holdingPeriodYears": None,
                "hasHoldingPeriod": False,
                "category": "Aineelliset hyödykkeet",
                "isActive": True,
            },
            # Kiinteät rakenteet ja laitteet (with holding periods)
            {
                "componentClass": "8106100",
                "account": "106100",
                "name": "Kadut, tiet ja torit (puistot) 20v",
                "holdingPeriodYears": 20,
                "hasHoldingPeriod": True,
                "category": "Kiinteät rakenteet ja laitteet",
                "isActive": True,
            },
            {
                "componentClass": "8106101",
                "account": "106100",
                "name": "Puistot 20v",
                "holdingPeriodYears": 20,
                "hasHoldingPeriod": True,
                "category": "Kiinteät rakenteet ja laitteet",
                "isActive": True,
            },
            {
                "componentClass": "8106115",
                "account": "106100",
                "name": "Katujen rantarakentaminen 15v",
                "holdingPeriodYears": 15,
                "hasHoldingPeriod": True,
                "category": "Kiinteät rakenteet ja laitteet",
                "isActive": True,
            },
            {
                "componentClass": "8106140",
                "account": "106100",
                "name": "Tekniset tunnelit 40v",
                "holdingPeriodYears": 40,
                "hasHoldingPeriod": True,
                "category": "Kiinteät rakenteet ja laitteet",
                "isActive": True,
            },
            {
                "componentClass": "8106210",
                "account": "106200",
                "name": "Sillat, laiturit ja uimalat 10v",
                "holdingPeriodYears": 10,
                "hasHoldingPeriod": True,
                "category": "Kiinteät rakenteet ja laitteet",
                "isActive": True,
            },
            {
                "componentClass": "8106230",
                "account": "106200",
                "name": "Sillat, laiturit ja uimalat 30v",
                "holdingPeriodYears": 30,
                "hasHoldingPeriod": True,
                "category": "Kiinteät rakenteet ja laitteet",
                "isActive": True,
            },
            {
                "componentClass": "8108200",
                "account": "108200",
                "name": "Liikenteen ohjauslaitteet 5v",
                "holdingPeriodYears": 5,
                "hasHoldingPeriod": True,
                "category": "Kiinteät rakenteet ja laitteet",
                "isActive": True,
            },
            {
                "componentClass": "8108916",
                "account": "108900",
                "name": "Yleiset käymälät 15v",
                "holdingPeriodYears": 15,
                "hasHoldingPeriod": True,
                "category": "Kiinteät rakenteet ja laitteet",
                "isActive": True,
            },
        ]

        created = 0
        for ac in asset_classes:
            obj, was_created = TalpaAssetClass.objects.update_or_create(
                componentClass=ac["componentClass"],
                account=ac["account"],
                defaults=ac,
            )
            if was_created:
                created += 1

        self.stdout.write(f"  Created {created} new, updated {len(asset_classes) - created} existing")

    def seed_project_number_ranges(self):
        """Seed TalpaProjectNumberRange with sample data"""
        self.stdout.write("\nSeeding TalpaProjectNumberRange...")
        
        ranges = [
            # 2814I - SAP format ranges (by district)
            {
                "projectTypePrefix": "2814I",
                "budgetAccount": "8 03 01 01",
                "budgetAccountNumber": "8030101A",
                "rangeStart": "2814I00003",
                "rangeEnd": "2814I00300",
                "majorDistrict": "01",
                "majorDistrictName": "Eteläinen suurpiiri",
                "isActive": True,
            },
            {
                "projectTypePrefix": "2814I",
                "budgetAccount": "8 03 01 01",
                "budgetAccountNumber": "8030101B",
                "rangeStart": "2814I00301",
                "rangeEnd": "2814I00700",
                "majorDistrict": "02",
                "majorDistrictName": "Läntinen suurpiiri",
                "isActive": True,
            },
            {
                "projectTypePrefix": "2814I",
                "budgetAccount": "8 03 01 01",
                "budgetAccountNumber": "8030101C",
                "rangeStart": "2814I00701",
                "rangeEnd": "2814I01100",
                "majorDistrict": "03",
                "majorDistrictName": "Keskinen suurpiiri",
                "isActive": True,
            },
            {
                "projectTypePrefix": "2814I",
                "budgetAccount": "8 04 01 01",
                "budgetAccountNumber": "8040101",
                "rangeStart": "2814I10000",
                "rangeEnd": "2814I10600",
                "majorDistrict": None,
                "majorDistrictName": None,
                "notes": "Uudet puistot ja puistojen peruskorjaus",
                "isActive": True,
            },
            # 2814E - MAKE format ranges (by unit)
            {
                "projectTypePrefix": "2814E",
                "budgetAccount": "8 01 03 01",
                "budgetAccountNumber": "8010301",
                "rangeStart": "2814E01000",
                "rangeEnd": "2814E01599",
                "unit": "Tontit",
                "contactPerson": "Test User",
                "contactEmail": "test.user@example.com",
                "notes": "Muu esirakentaminen - Tontit",
                "isActive": True,
            },
            {
                "projectTypePrefix": "2814E",
                "budgetAccount": "8 01 03 01",
                "budgetAccountNumber": "8010301",
                "rangeStart": "2814E01600",
                "rangeEnd": "2814E03999",
                "unit": "Mao",
                "contactPerson": "Test User",
                "contactEmail": "test.user@example.com",
                "notes": "Muu esirakentaminen - Mao",
                "isActive": True,
            },
            {
                "projectTypePrefix": "2814E",
                "budgetAccount": "8 01 03 01",
                "budgetAccountNumber": "8010301",
                "rangeStart": "2814E04000",
                "rangeEnd": "2814E04999",
                "unit": "Geo",
                "contactPerson": "Test User 2",
                "contactEmail": "test.user2@example.com",
                "notes": "Muu esirakentaminen - Geo",
                "isActive": True,
            },
            {
                "projectTypePrefix": "2814E",
                "budgetAccount": "8 08 01 02",
                "budgetAccountNumber": "8080102",
                "rangeStart": "2814E21001",
                "rangeEnd": "2814E21099",
                "unit": "Tontit",
                "area": "Länsisatama",
                "contactPerson": "Test User",
                "contactEmail": "test.user@example.com",
                "isActive": True,
            },
            {
                "projectTypePrefix": "2814E",
                "budgetAccount": "8 08 01 03",
                "budgetAccountNumber": "8080103",
                "rangeStart": "2814E22001",
                "rangeEnd": "2814E22099",
                "unit": "Tontit",
                "area": "Kalasatama",
                "contactPerson": "Test User",
                "contactEmail": "test.user@example.com",
                "isActive": True,
            },
            # Template projects (for reference)
            {
                "projectTypePrefix": "2814I",
                "budgetAccount": "MALLI",
                "rangeStart": "2814I00000",
                "rangeEnd": "2814I00000",
                "notes": "Malliprojekti - Infrainvestointi",
                "isActive": True,
            },
            {
                "projectTypePrefix": "2814E",
                "budgetAccount": "MALLI",
                "rangeStart": "2814E00013",
                "rangeEnd": "2814E00013",
                "notes": "Malliprojekti - Esirakentaminen Make",
                "isActive": True,
            },
        ]

        created = 0
        for r in ranges:
            # Use a combination of fields as unique identifier
            obj, was_created = TalpaProjectNumberRange.objects.update_or_create(
                projectTypePrefix=r["projectTypePrefix"],
                rangeStart=r["rangeStart"],
                rangeEnd=r["rangeEnd"],
                defaults=r,
            )
            if was_created:
                created += 1

        self.stdout.write(f"  Created {created} new, updated {len(ranges) - created} existing")

