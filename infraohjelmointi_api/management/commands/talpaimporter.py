"""
Management command to import Talpa reference data from Excel file.

This imports:
- TalpaProjectNumberRange (from 2814I and 2814E project number range tabs)
- TalpaServiceClass (from Palveluluokat tab)
- TalpaAssetClass (from Käyttöomaisuusluokat tab)

Usage:
    python manage.py talpaimporter --file path/to/Projektin_avauslomake_Infra.xlsx
    python manage.py talpaimporter --file path/to/excel.xlsx --dry-run
"""

import os
import re
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

try:
    import openpyxl
except ImportError:
    raise CommandError("openpyxl is required to read Excel files. Please install it.")

from infraohjelmointi_api.models import (
    TalpaProjectNumberRange,
    TalpaServiceClass,
    TalpaAssetClass,
)


class Command(BaseCommand):
    help = """
    Import Talpa reference data from Excel file.
    
    This imports project number ranges, service classes, and asset classes
    from the official Talpa Excel specification file.
    
    Usage: python manage.py talpaimporter --file path/to/excel.xlsx
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            required=True,
            help='Path to the Talpa Excel file (Projektin avauslomake Infra)'
        )
        parser.add_argument(
            '--ranges-file',
            type=str,
            required=False,
            help='Path to SAP_Projektinumerovälit.xlsx for project number ranges'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be imported without making changes'
        )
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='Clear all existing Talpa reference data before importing'
        )
        parser.add_argument(
            '--skip-ranges',
            action='store_true',
            help='Skip importing project number ranges'
        )
        parser.add_argument(
            '--skip-services',
            action='store_true',
            help='Skip importing service classes'
        )
        parser.add_argument(
            '--skip-assets',
            action='store_true',
            help='Skip importing asset classes'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        ranges_file_path = options.get('ranges_file')
        dry_run = options['dry_run']
        clear_existing = options['clear_existing']

        if not os.path.exists(file_path):
            raise CommandError(f"Excel file not found: {file_path}")

        self.stdout.write(self.style.NOTICE("Importing Talpa Reference Data from Excel..."))

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made\n"))

        try:
            wb = openpyxl.load_workbook(file_path, data_only=True, read_only=True)
        except Exception as e:
            raise CommandError(f"Error reading Excel file: {e}")

        self.stdout.write(f"Opened: {file_path}")
        self.stdout.write(f"Worksheets found: {wb.sheetnames}\n")

        # Load ranges file if provided
        ranges_wb = None
        if ranges_file_path:
            if not os.path.exists(ranges_file_path):
                raise CommandError(f"Ranges Excel file not found: {ranges_file_path}")
            try:
                ranges_wb = openpyxl.load_workbook(ranges_file_path, data_only=True, read_only=True)
                self.stdout.write(f"Opened ranges file: {ranges_file_path}")
                self.stdout.write(f"Ranges worksheets: {ranges_wb.sheetnames}\n")
            except Exception as e:
                raise CommandError(f"Error reading ranges Excel file: {e}")

        stats = {
            'ranges_created': 0,
            'ranges_updated': 0,
            'services_created': 0,
            'services_updated': 0,
            'assets_created': 0,
            'assets_updated': 0,
            'errors': []
        }

        # Pass ranges_wb to import functions
        options['_ranges_wb'] = ranges_wb

        if dry_run:
            self._dry_run_import(wb, options, stats)
        else:
            self._execute_import(wb, options, stats, clear_existing)

        self._print_summary(stats, dry_run)

    def _dry_run_import(self, wb, options, stats):
        """Preview what would be imported"""
        if not options['skip_assets']:
            self._preview_asset_classes(wb, stats)

        if not options['skip_services']:
            self._preview_service_classes(wb, stats)

        if not options['skip_ranges']:
            self._preview_project_number_ranges(wb, stats, options)

    @transaction.atomic
    def _execute_import(self, wb, options, stats, clear_existing):
        """Execute the actual import"""
        if clear_existing:
            self._clear_existing_data(options, stats)

        if not options['skip_assets']:
            self._import_asset_classes(wb, stats)

        if not options['skip_services']:
            self._import_service_classes(wb, stats)

        if not options['skip_ranges']:
            self._import_project_number_ranges(wb, stats, options)

    def _clear_existing_data(self, options, stats):
        """Clear existing Talpa reference data"""
        self.stdout.write(self.style.WARNING("Clearing existing Talpa reference data..."))

        if not options['skip_ranges']:
            count = TalpaProjectNumberRange.objects.count()
            TalpaProjectNumberRange.objects.all().delete()
            self.stdout.write(f"Deleted {count} project number ranges")

        if not options['skip_services']:
            count = TalpaServiceClass.objects.count()
            TalpaServiceClass.objects.all().delete()
            self.stdout.write(f"Deleted {count} service classes")

        if not options['skip_assets']:
            count = TalpaAssetClass.objects.count()
            TalpaAssetClass.objects.all().delete()
            self.stdout.write(f"Deleted {count} asset classes")

    # =========================================================================
    # ASSET CLASSES (Käyttöomaisuusluokat)
    # =========================================================================

    def _find_asset_class_sheet(self, wb):
        """Find the Käyttöomaisuusluokat worksheet"""
        for name in wb.sheetnames:
            if 'käyttöomaisuus' in name.lower() or 'kayttoomaisuus' in name.lower():
                return wb[name]
        return None

    def _parse_asset_class_row(self, row):
        """Parse a row from the asset class sheet"""
        # Expected columns based on Excel image:
        # Poisto-ryhmä | Käyttöomaisuusluokka | Kom-luokka | Tili | Pito-aika | Kom-luokka (nimi)
        # Example: Aineelliset... | Maa- ja vesialueet | 8103000 | 103000 | EP | 8103000 (Maa- ja vesialueet)

        try:
            component_class = str(row[2].value).strip() if row[2].value else None
            account = str(row[3].value).strip() if row[3].value else None
            holding_period_raw = str(row[4].value).strip() if row[4].value else None
            name = str(row[1].value).strip() if row[1].value else None

            if not component_class or not account or not name:
                return None

            # Skip header rows
            if component_class.lower() in ['kom-luokka', 'komponenttiluokka', 'tili']:
                return None

            # Parse holding period
            has_holding_period = True
            holding_period_years = None

            if holding_period_raw:
                if holding_period_raw.upper() == 'EP':
                    # EP = Ei poisteta (No depreciation)
                    has_holding_period = False
                else:
                    try:
                        holding_period_years = int(holding_period_raw)
                    except ValueError:
                        pass

            # Determine category from first column or component class prefix
            category = None
            if row[0].value:
                category = str(row[0].value).strip()

            return {
                'componentClass': component_class,
                'account': account,
                'name': name,
                'holdingPeriodYears': holding_period_years,
                'hasHoldingPeriod': has_holding_period,
                'category': category,
                'isActive': True,
            }
        except Exception as e:
            return None

    def _preview_asset_classes(self, wb, stats):
        """Preview asset class import"""
        self.stdout.write("Previewing Asset Classes...")

        sheet = self._find_asset_class_sheet(wb)
        if not sheet:
            self.stdout.write(self.style.WARNING("  Sheet not found"))
            return

        self.stdout.write(f"  Found sheet: {sheet.title}")
        count = 0
        for row in list(sheet.rows)[1:]:  # Skip header
            data = self._parse_asset_class_row(row)
            if data:
                count += 1
                if count <= 5:
                    self.stdout.write(f"  {count}. {data['componentClass']} - {data['name'][:40]}...")

        self.stdout.write(f"  Total asset classes found: {count}")
        stats['assets_created'] = count

    def _import_asset_classes(self, wb, stats):
        """Import asset classes"""
        self.stdout.write("Importing Asset Classes...")

        sheet = self._find_asset_class_sheet(wb)
        if not sheet:
            self.stdout.write(self.style.WARNING("  Sheet not found, skipping"))
            return

        for row in list(sheet.rows)[1:]:
            data = self._parse_asset_class_row(row)
            if data:
                obj, created = TalpaAssetClass.objects.update_or_create(
                    componentClass=data['componentClass'],
                    account=data['account'],
                    defaults=data
                )
                if created:
                    stats['assets_created'] += 1
                else:
                    stats['assets_updated'] += 1

        self.stdout.write(f"  Created: {stats['assets_created']}, Updated: {stats['assets_updated']}")

    # =========================================================================
    # SERVICE CLASSES (Palveluluokat)
    # =========================================================================

    def _find_service_class_sheet(self, wb):
        """Find the Palveluluokat worksheet or section"""
        for name in wb.sheetnames:
            if 'palvelu' in name.lower():
                return wb[name]
        return None

    def _parse_service_class_row(self, row, project_type_prefix=None):
        """Parse a row from the service class data"""
        try:
            # Expected format: Code (name) | Code | Description
            # Example: 4601 (Kadut ja yleiset alueet) | 4601 | Kadut ja yleiset alueet | ...
            code = str(row[1].value).strip() if row[1].value else None
            name = str(row[2].value).strip() if row[2].value else None
            description = str(row[3].value).strip() if len(row) > 3 and row[3].value else None

            if not code or not name:
                return None

            # Skip header rows
            if code.lower() in ['koodi', 'code', 'palveluluokka']:
                return None

            return {
                'code': code,
                'name': name,
                'description': description,
                'projectTypePrefix': project_type_prefix,
                'isActive': True,
            }
        except Exception:
            return None

    def _preview_service_classes(self, wb, stats):
        """Preview service class import"""
        self.stdout.write("Previewing Service Classes...")

        # Service classes may be embedded in main sheet rather than separate tab
        # Based on images: 4601, 4701, 3551 for 2814I and 5361 for 2814E
        service_classes = [
            {'code': '4601', 'name': 'Kadut ja yleiset alueet', 'projectTypePrefix': '2814I'},
            {'code': '4701', 'name': 'Puistot ja viheralueet', 'projectTypePrefix': '2814I'},
            {'code': '3551', 'name': 'Liikunta- ja ulkoilupalvelut', 'projectTypePrefix': '2814I'},
            {'code': '5361', 'name': 'Maaomaisuuden hallinta', 'projectTypePrefix': '2814E'},
        ]

        sheet = self._find_service_class_sheet(wb)
        if sheet:
            self.stdout.write(f"  Found sheet: {sheet.title}")
            # Parse from sheet if found
        else:
            self.stdout.write("  No dedicated sheet found, using known values from form")

        for sc in service_classes:
            self.stdout.write(f"  {sc['code']} - {sc['name']} ({sc['projectTypePrefix']})")

        stats['services_created'] = len(service_classes)

    def _import_service_classes(self, wb, stats):
        """Import service classes"""
        self.stdout.write("Importing Service Classes...")

        # Known service classes from the Excel form structure
        service_classes = [
            {
                'code': '4601',
                'name': 'Kadut ja yleiset alueet',
                'description': 'Katujen, kevyen liikenteen väylien, jalkakäytävien ja liikennealueiden viheralueiden suunnittelu, toteutus, kunnossapito ja puhtaanapito',
                'projectTypePrefix': '2814I',
                'isActive': True,
            },
            {
                'code': '4701',
                'name': 'Puistot ja viheralueet',
                'description': 'Puistojen ja viheralueiden suunnittelu, toteutus, kunnossapito ja puhtaanapito',
                'projectTypePrefix': '2814I',
                'isActive': True,
            },
            {
                'code': '3551',
                'name': 'Liikunta- ja ulkoilupalvelut',
                'description': 'Yleisten edellytysten luominen liikunnalle paikallisella tasolla sekä kuntalaisten liikkumista tukevan toiminta, suunnittelu, toteutus sekä kunnossapito',
                'projectTypePrefix': '2814I',
                'isActive': True,
            },
            {
                'code': '5361',
                'name': 'Maaomaisuuden hallinta',
                'description': 'Maaomaisuuden hankinta, lunastaminen ja luovutus. Sisältää maaperätutkimukset, pilaantuneen maan puhdistamisen, kiinteistön kuntoarviot.',
                'projectTypePrefix': '2814E',
                'isActive': True,
            },
        ]

        for sc in service_classes:
            obj, created = TalpaServiceClass.objects.update_or_create(
                code=sc['code'],
                defaults=sc
            )
            if created:
                stats['services_created'] += 1
            else:
                stats['services_updated'] += 1

        self.stdout.write(f"  Created: {stats['services_created']}, Updated: {stats['services_updated']}")

    # =========================================================================
    # PROJECT NUMBER RANGES (2814I and 2814E)
    # =========================================================================

    def _find_project_range_sheets(self, wb):
        """Find the 2814I and 2814E project range worksheets

        Known sheet names:
        - '2814I-projektinumerovälit' for 2814I ranges
        - 'Esirakentaminen projektinumerov' for 2814E ranges
        """
        sheets = {'2814I': None, '2814E': None}

        for name in wb.sheetnames:
            name_lower = name.lower()
            # Match 2814I sheet (contains '2814i' in name)
            if '2814i' in name_lower:
                sheets['2814I'] = wb[name]
            # Match 2814E sheet (contains 'esirakentaminen' or '2814e')
            elif 'esirakentaminen' in name_lower or '2814e' in name_lower:
                sheets['2814E'] = wb[name]

        return sheets

    def _parse_2814I_range_row(self, row):
        """Parse a row from the 2814I project number range sheet"""
        try:
            # Expected format from Excel image:
            # RangeStart-RangeEnd (BudgetAccount) Description, DISTRICT_NAME
            # Example: 2814100003-2814100300 (8 03 01 01) Katujen uudisrakentaminen, ETELÄINEN SUURPIIRI

            cell_value = str(row[0].value).strip() if row[0].value else None
            if not cell_value:
                return None

            # Skip if it looks like a header
            if 'projektinumero' in cell_value.lower() or 'projektiväl' in cell_value.lower():
                return None

            # Normalize dashes (en-dash U+2013, em-dash U+2014) to regular hyphen
            cell_value = cell_value.replace('\u2013', '-').replace('\u2014', '-')

            # Parse format: "2814100003-2814100300 (8 03 01 01) Description, DISTRICT"
            # or: "2814100003-2814100300 8 03 01 01 Description"

            # Parse using Regex to handle variations like:
            # "2814I00003-2814I00300" (no spaces)
            # "2814I00003 - 2814I00300" (spaces)
            # "2814I00003- 2814I00300" (space after)
            range_pattern = r'^\s*(2814[IE]\d+)\s*[-]\s*(2814[IE]?\d+)'

            match = re.match(range_pattern, cell_value)

            if match:
                range_start = match.group(1)
                range_end = match.group(2)

                # If end doesn't have prefix (e.g. "2814I001-002"), add it?
                # (Assuming full format for now based on audit)
            else:
                return None

            # Try to extract budget account (format like "8 03 01 01" or "(8 03 01 01)")
            budget_account = None
            budget_account_number = None

            # Look for pattern like "(8 03 01 01)" or "8 03 01 01"
            budget_match = re.search(r'\(?(8\s*\d{2}\s*\d{2}\s*\d{2}[A-H]?)\)?', cell_value)
            if budget_match:
                budget_account = budget_match.group(1).strip()
                # Create compact version for budgetAccountNumber
                budget_account_number = budget_account.replace(' ', '')

            # Try to extract district name (usually at the end)
            district_name = None
            district_code = None

            district_patterns = [
                (r'ETELÄINEN\s+SUURPIIRI', '01', 'Eteläinen suurpiiri'),
                (r'LÄNTINEN\s+SUURPIIRI', '02', 'Läntinen suurpiiri'),
                (r'KESKINEN\s+SUURPIIRI', '03', 'Keskinen suurpiiri'),
                (r'POHJOINEN\s+SUURPIIRI', '04', 'Pohjoinen suurpiiri'),
                (r'KOILLINEN\s+SUURPIIRI', '05', 'Koillinen suurpiiri'),
                (r'KAAKKOINEN\s+SUURPIIRI', '06', 'Kaakkoinen suurpiiri'),
                (r'ITÄINEN\s+SUURPIIRI', '07', 'Itäinen suurpiiri'),
                (r'ÖSTERSUNDOM', '08', 'Östersundomin suurpiiri'),
            ]

            for pattern, code, name in district_patterns:
                if re.search(pattern, cell_value, re.IGNORECASE):
                    district_code = code
                    district_name = name
                    break

            return {
                'projectTypePrefix': '2814I',
                'budgetAccount': budget_account,
                'budgetAccountNumber': budget_account_number,
                'rangeStart': range_start,
                'rangeEnd': range_end,
                'majorDistrict': district_code,
                'majorDistrictName': district_name,
                'isActive': True,
            }
        except Exception:
            return None

    def _parse_2814E_range_row(self, row):
        """Parse a row from the 2814E project number range sheet"""
        try:
            cell_value = str(row[0].value).strip() if row[0].value else None
            if not cell_value:
                return None

            # Skip headers
            if 'projektinumero' in cell_value.lower() or '2814e-' in cell_value.lower():
                return None

            # Parse format: "2814E02000 - 2814E02999 (8 01 03 01) Description"
            parts = cell_value.split()
            if len(parts) < 2:
                return None

            # Extract range
            range_part = parts[0]
            range_start = range_part.strip()
            range_end = range_start

            # Look for range end after "-"
            for i, part in enumerate(parts):
                if part == '-' and i + 1 < len(parts):
                    range_end = parts[i + 1].strip()
                    break
                elif '-' in part and part != range_start:
                    range_split = part.split('-')
                    if len(range_split) == 2:
                        range_end = range_split[1].strip()
                    break

            # Extract budget account
            budget_account = None
            budget_account_number = None
            budget_match = re.search(r'\(?(8\s*\d{2}\s*\d{2}\s*\d{2})\)?', cell_value)
            if budget_match:
                budget_account = budget_match.group(1).strip()
                budget_account_number = budget_account.replace(' ', '')

            # Extract area/unit info (for 2814E these are more complex)
            area = None
            unit = None
            contact_person = None
            contact_email = None

            # Common areas
            area_patterns = [
                'Kalasatama', 'Länsisatama', 'Pasila', 'Kruunuvuorenranta',
                'Kuninkaankolmio', 'Malmi', 'Malminkartano', 'Mellunkylä',
                'Meri-Rastila', 'Läntinen bulevardikaupunki', 'Makasiiniranta'
            ]
            for area_name in area_patterns:
                if area_name.lower() in cell_value.lower():
                    area = area_name
                    break

            return {
                'projectTypePrefix': '2814E',
                'budgetAccount': budget_account,
                'budgetAccountNumber': budget_account_number,
                'rangeStart': range_start,
                'rangeEnd': range_end,
                'area': area,
                'unit': unit,
                'contactPerson': contact_person,
                'contactEmail': contact_email,
                'isActive': True,
            }
        except Exception:
            return None

    def _parse_sap_range_row(self, row):
        """Parse a row from SAP_Projektinumerovälit.xlsx format

        Format: Column 1 = District/Area name, Column 2 = Range (e.g., 2814I00003-2814I00300)
        """
        try:
            area_or_district = str(row[0].value).strip() if row[0].value else None
            range_value = str(row[1].value).strip() if row[1].value else None

            if not range_value:
                return None

            # Parse range from column 2 (format: 2814I00003-2814I00300)
            if '-' not in range_value:
                return None

            range_parts = range_value.split('-')
            range_start = range_parts[0].strip()
            range_end = range_parts[1].strip() if len(range_parts) > 1 else range_start

            # Skip if not a valid range format
            if not range_start.startswith('2814'):
                return None

            # Determine project type prefix
            if range_start.startswith('2814I') or 'I' in range_start[4:5].upper():
                project_type_prefix = '2814I'
            elif range_start.startswith('2814E') or 'E' in range_start[4:5].upper():
                project_type_prefix = '2814E'
            else:
                # Default to 2814I if ambiguous
                project_type_prefix = '2814I'

            # Parse district info for 2814I
            district_code = None
            district_name = None
            area = None

            if area_or_district:
                district_patterns = [
                    (r'ETELÄINEN', '01', 'Eteläinen suurpiiri'),
                    (r'LÄNTINEN', '02', 'Läntinen suurpiiri'),
                    (r'KESKINEN', '03', 'Keskinen suurpiiri'),
                    (r'POHJOINEN', '04', 'Pohjoinen suurpiiri'),
                    (r'KOILLINEN', '05', 'Koillinen suurpiiri'),
                    (r'KAAKKOINEN', '06', 'Kaakkoinen suurpiiri'),
                    (r'ITÄINEN', '07', 'Itäinen suurpiiri'),
                    (r'ÖSTERSUNDOM', '08', 'Östersundomin suurpiiri'),
                ]

                for pattern, code, name in district_patterns:
                    if re.search(pattern, area_or_district, re.IGNORECASE):
                        district_code = code
                        district_name = name
                        break

                # If no district match, use as area (for 2814E)
                if not district_name:
                    area = area_or_district

            return {
                'projectTypePrefix': project_type_prefix,
                'budgetAccount': None,  # SAP file doesn't have budget account in this format
                'budgetAccountNumber': None,
                'rangeStart': range_start,
                'rangeEnd': range_end,
                'majorDistrict': district_code,
                'majorDistrictName': district_name,
                'area': area if project_type_prefix == '2814E' else None,
                'isActive': True,
            }
        except Exception:
            return None

    def _preview_project_number_ranges(self, wb, stats, options=None):
        """Preview project number range import"""
        self.stdout.write("Previewing Project Number Ranges...")

        # Check if we have a separate ranges file
        ranges_wb = options.get('_ranges_wb') if options else None

        if ranges_wb:
            self.stdout.write("  Using separate ranges file (SAP format)")
            total = 0
            for sheet_name in ranges_wb.sheetnames:
                sheet = ranges_wb[sheet_name]
                self.stdout.write(f"\n  Processing sheet: {sheet_name}")
                count = 0
                for row in list(sheet.rows)[1:]:  # Skip header
                    data = self._parse_sap_range_row(row)
                    if data:
                        count += 1
                        if count <= 5:
                            self.stdout.write(
                                f"    {data['rangeStart']} - {data['rangeEnd']} "
                                f"({data.get('majorDistrictName') or data.get('area') or 'No location'})"
                            )

                self.stdout.write(f"  Total ranges from {sheet_name}: {count}")
                total += count

            stats['ranges_created'] = total
            return

        # Fall back to main workbook
        sheets = self._find_project_range_sheets(wb)

        total = 0
        for prefix, sheet in sheets.items():
            if sheet:
                self.stdout.write(f"\n  {prefix} sheet: {sheet.title}")
                count = 0
                for row in list(sheet.rows)[1:]:
                    if prefix == '2814I':
                        data = self._parse_2814I_range_row(row)
                    else:
                        data = self._parse_2814E_range_row(row)

                    if data:
                        count += 1
                        if count <= 3:
                            self.stdout.write(f"    {data['rangeStart']} - {data['rangeEnd']}")

                self.stdout.write(f"  Total {prefix} ranges: {count}")
                total += count
            else:
                self.stdout.write(f"\n  {prefix} sheet: NOT FOUND")

        stats['ranges_created'] = total

    def _import_project_number_ranges(self, wb, stats, options=None):
        """Import project number ranges"""
        self.stdout.write("Importing Project Number Ranges...")

        # Check if we have a separate ranges file
        ranges_wb = options.get('_ranges_wb') if options else None

        if ranges_wb:
            self.stdout.write("  Using separate ranges file (SAP format)")
            for sheet_name in ranges_wb.sheetnames:
                sheet = ranges_wb[sheet_name]
                self.stdout.write(f"  Processing sheet: {sheet_name}")

                for row in list(sheet.rows)[1:]:  # Skip header
                    data = self._parse_sap_range_row(row)
                    if data:
                        obj, created = TalpaProjectNumberRange.objects.update_or_create(
                            projectTypePrefix=data['projectTypePrefix'],
                            rangeStart=data['rangeStart'],
                            rangeEnd=data['rangeEnd'],
                            defaults=data
                        )
                        if created:
                            stats['ranges_created'] += 1
                        else:
                            stats['ranges_updated'] += 1

            self.stdout.write(f"  Created: {stats['ranges_created']}, Updated: {stats['ranges_updated']}")
            return

        # Fall back to main workbook
        sheets = self._find_project_range_sheets(wb)

        for prefix, sheet in sheets.items():
            if not sheet:
                self.stdout.write(f"  {prefix} sheet not found, skipping")
                continue

            self.stdout.write(f"  Processing {prefix} from: {sheet.title}")

            for row in list(sheet.rows)[1:]:
                if prefix == '2814I':
                    data = self._parse_2814I_range_row(row)
                else:
                    data = self._parse_2814E_range_row(row)

                if data:
                    obj, created = TalpaProjectNumberRange.objects.update_or_create(
                        projectTypePrefix=data['projectTypePrefix'],
                        rangeStart=data['rangeStart'],
                        rangeEnd=data['rangeEnd'],
                        defaults=data
                    )
                    if created:
                        stats['ranges_created'] += 1
                    else:
                        stats['ranges_updated'] += 1

        self.stdout.write(f"  Created: {stats['ranges_created']}, Updated: {stats['ranges_updated']}")

    def _print_summary(self, stats, dry_run):
        """Print import summary"""
        self.stdout.write(self.style.SUCCESS("IMPORT SUMMARY"))

        self.stdout.write(f"Asset Classes:   {stats['assets_created']} created, {stats['assets_updated']} updated")
        self.stdout.write(f"Service Classes: {stats['services_created']} created, {stats['services_updated']} updated")
        self.stdout.write(f"Number Ranges:   {stats['ranges_created']} created, {stats['ranges_updated']} updated")

        if stats['errors']:
            self.stdout.write(self.style.ERROR(f"\nErrors ({len(stats['errors'])}):"))
            for error in stats['errors'][:10]:
                self.stdout.write(f"  - {error}")
            if len(stats['errors']) > 10:
                self.stdout.write(f"  ... and {len(stats['errors']) - 10} more")

        if dry_run:
            self.stdout.write(self.style.WARNING("\nThis was a dry run. No changes were made."))
        else:
            self.stdout.write(self.style.SUCCESS("\nImport completed successfully!"))
