"""
Management command to import Talpa reference data from Excel file.

This imports:
- TalpaProjectNumberRange (from 2814I and 2814E project number range tabs)
- TalpaServiceClass (from Palveluluokat tab)
- TalpaAssetClass (from Käyttöomaisuusluokat tab)
- TalpaProjectType (from Talousarviokohdat and Lajit ja prioriteetit tabs)

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
    TalpaProjectType,
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
        parser.add_argument(
            '--skip-project-types',
            action='store_true',
            help='Skip importing project types and priorities'
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
            'priorities_updated': 0,
            'project_types_created': 0,
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

        if not options['skip_project_types']:
            self._preview_project_types(wb, stats)

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

        if not options['skip_project_types']:
            self._import_project_types(wb, stats)

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

        if not options['skip_project_types']:
             # We don't delete Project Types as they might be linked.
             pass

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
        except Exception:
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

        current_category = None

        for row in list(sheet.rows)[1:]:
            # Check for category header in first column regardless of whether it's a data row
            col0 = str(row[0].value).strip() if row[0].value else None
            
            # Update 'current_category' if we see a value in Col 0
            # Ignore the specific table header 'Poisto-ryhmä'
            if col0 and 'poisto-ryhm' not in col0.lower():
                current_category = col0
            
            data = self._parse_asset_class_row(row)
            if data:
                # Apply the current category to the item
                if current_category:
                    data['category'] = current_category

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

    def _preview_service_classes(self, wb, stats):
        """Preview service class import"""
        self.stdout.write("Previewing Service Classes...")

        service_classes = [
            {'code': '4601', 'name': 'Kadut ja yleiset alueet', 'projectTypePrefix': '2814I'},
            {'code': '4701', 'name': 'Puistot ja viheralueet', 'projectTypePrefix': '2814I'},
            {'code': '3551', 'name': 'Liikunta- ja ulkoilupalvelut', 'projectTypePrefix': '2814I'},
            {'code': '5361', 'name': 'Maaomaisuuden hallinta', 'projectTypePrefix': '2814E'},
        ]

        sheet = self._find_service_class_sheet(wb)
        if sheet:
            self.stdout.write(f"  Found sheet: {sheet.title}")
        else:
            self.stdout.write("  No dedicated sheet found, using known values from form")

        for sc in service_classes:
            self.stdout.write(f"  {sc['code']} - {sc['name']} ({sc['projectTypePrefix']})")

        stats['services_created'] = len(service_classes)

    def _import_service_classes(self, wb, stats):
        """Import service classes"""
        self.stdout.write("Importing Service Classes...")

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
        """Find the 2814I and 2814E project range worksheets"""
        sheets = {'2814I': None, '2814E': None}

        for name in wb.sheetnames:
            name_lower = name.lower()
            if '2814i' in name_lower:
                sheets['2814I'] = wb[name]
            elif 'esirakentaminen' in name_lower or '2814e' in name_lower:
                sheets['2814E'] = wb[name]

        return sheets

    def _parse_2814I_range_row(self, row):
        """Parse a row from the 2814I project number range sheet"""
        try:
            cell_value = str(row[0].value).strip() if row[0].value else None
            if not cell_value:
                return None

            if 'projektinumero' in cell_value.lower() or 'projektiväl' in cell_value.lower():
                return None

            cell_value = cell_value.replace('\u2013', '-').replace('\u2014', '-')

            # Regex: "2814I00003-2814I00300"
            range_pattern = r'^\s*(2814[IE]\d+)\s*[-]\s*(2814[IE]?\d+)'
            match = re.match(range_pattern, cell_value)

            if match:
                range_start = match.group(1)
                range_end = match.group(2)
            else:
                return None

            budget_account = None
            budget_account_number = None
            notes = None

            paren_match = re.search(r'\(([^)]+)\)', cell_value)
            if paren_match:
                paren_content = paren_match.group(1).strip()
                
                budget_match = re.match(r'^(8\s*\d{2}\s*\d{2}\s*\d{2}[A-H]?)', paren_content)
                
                if budget_match:
                    budget_account = budget_match.group(1).strip()
                    remaining = paren_content[budget_match.end():].strip()
                    if remaining.startswith(','):
                        notes = remaining[1:].strip()
                    elif remaining:
                        notes = remaining.strip()
                else:
                    if ',' in paren_content:
                        parts = paren_content.split(',', 1)
                        potential_budget = parts[0].strip()
                        if potential_budget.startswith('8') and len(potential_budget) <= 15:
                            budget_account = potential_budget
                            notes = parts[1].strip() if len(parts) > 1 else None
                        else:
                            notes = paren_content
                    else:
                        if paren_content.startswith('8') and len(paren_content) <= 15:
                            budget_account = paren_content
                        else:
                            notes = paren_content
                
                if budget_account:
                    budget_account_number = budget_account.replace(' ', '')

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
                'notes': notes,
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

            if 'projektinumero' in cell_value.lower() or '2814e-' in cell_value.lower():
                return None

            parts = cell_value.split()
            if len(parts) < 2:
                return None

            range_part = parts[0]
            range_start = range_part.strip()
            range_end = range_start

            for i, part in enumerate(parts):
                if part == '-' and i + 1 < len(parts):
                    range_end = parts[i + 1].strip()
                    break
                elif '-' in part and part != range_start:
                    range_split = part.split('-')
                    if len(range_split) == 2:
                        range_end = range_split[1].strip()
                    break

            budget_account = None
            budget_account_number = None
            budget_match = re.search(r'\(?(8\s*\d{2}\s*\d{2}\s*\d{2})\)?', cell_value)
            if budget_match:
                budget_account = budget_match.group(1).strip()
                budget_account_number = budget_account.replace(' ', '')

            area = None
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
                'isActive': True,
            }
        except Exception:
            return None

    def _parse_sap_range_row(self, row):
        """Parse a row from SAP_Projektinumerovälit.xlsx format"""
        try:
            area_or_district = str(row[0].value).strip() if row[0].value else None
            range_value = str(row[1].value).strip() if row[1].value else None

            if not range_value:
                return None

            if '-' not in range_value:
                return None

            range_parts = range_value.split('-')
            range_start = range_parts[0].strip()
            range_end = range_parts[1].strip() if len(range_parts) > 1 else range_start

            if not range_start.startswith('2814'):
                return None

            if range_start.startswith('2814I') or 'I' in range_start[4:5].upper():
                project_type_prefix = '2814I'
            elif range_start.startswith('2814E') or 'E' in range_start[4:5].upper():
                project_type_prefix = '2814E'
            else:
                project_type_prefix = '2814I'

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

                if not district_name:
                    area = area_or_district

            return {
                'projectTypePrefix': project_type_prefix,
                'budgetAccount': None,
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

        ranges_wb = options.get('_ranges_wb') if options else None

        if ranges_wb:
            self.stdout.write("  Using separate ranges file (SAP format)")
            for sheet_name in ranges_wb.sheetnames:
                sheet = ranges_wb[sheet_name]
                for row in list(sheet.rows)[1:]:
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

        sheets = self._find_project_range_sheets(wb)

        for prefix, sheet in sheets.items():
            if not sheet:
                continue

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

    # =========================================================================
    # PROJECT TYPES (Talousarviokohdat + Lajit ja prioriteetit)
    # =========================================================================

    def _find_sheet_by_keyword(self, wb, keyword):
        """Find sheet containing keyword in title"""
        for name in wb.sheetnames:
            if keyword.lower() in name.lower():
                return wb[name]
        return None

    def _parse_laji_header_cell(self, cell_value):
        """
        Parse Laji ID and Name from header cell.
        Returns (laji_code, search_name) or (None, None).
        
        Formats supported:
        - Standard: "03 (Yhteishankkeet...)"
        - Irregular: "H (Laji 13, Uudet puistot, ...)"
        """
        laji_code = None
        search_name = "Unknown"
        
        # Try Standard format first
        match_std = re.match(r'^(\d+)\s*\((.+)\)', cell_value.replace('\n', ' '))
        if match_std:
            laji_code = match_std.group(1)
            content = match_std.group(2)
            search_name = content.split(',')[0].strip()
            return laji_code, search_name
        
        # Try Irregular "Laji X" format
        if 'laji' in cell_value.lower():
            match_irr = re.search(r'Laji\s*(\d+)', cell_value, re.IGNORECASE)
            if match_irr:
                laji_code = match_irr.group(1)
                parts = cell_value.split(',')
                if len(parts) > 1:
                    search_name = parts[1].strip()
                return laji_code, search_name
                
        return None, None

    def _collect_priorities(self, sheet):
        """
        Parse Lajit sheet to collect metadata for each Laji group.
        Returns: { 'LajiCode': { 'priorities': [], 'category': '', 'search_name': '' } }
        """
        laji_data = {}
        current_laji_code = None
        current_category = None
        
        for row in sheet.rows:
            col0 = str(row[0].value).strip() if row[0].value else None
            col1 = str(row[1].value).strip() if row[1].value and len(str(row[1].value)) < 10 else None
            col3 = str(row[3].value).strip() if len(row) > 3 and row[3].value else None

            if col0:
                # 1. Attempt to parse Laji Header
                laji_code, search_name = self._parse_laji_header_cell(col0)
                if laji_code:
                    current_laji_code = laji_code
                    laji_data[current_laji_code] = {
                        'priorities': [], 
                        'category': current_category,
                        'search_name': search_name
                    }
                    continue

                # 2. Check for Category Header (uppercase text, no numbers/keywords)
                if not laji_code and len(col0) > 3:
                     # Heuristic: Uppercase, not a Laji, not priority, not date
                     if not re.match(r'^\d', col0) and 'laji' not in col0.lower() and 'prior' not in col0.lower():
                        clean_cat = col0.replace(')', '').strip()
                        current_category = clean_cat.capitalize()
                        continue

            # 3. Check for Priority Row (must be under a valid Laji)
            if current_laji_code and col1 and len(col1) <= 2:
                 if current_laji_code in laji_data:
                    laji_data[current_laji_code]['priorities'].append({
                        'priority': col1,
                        'description': col3
                    })

        return laji_data

    def _parse_talous_row(self, row):
        """Parse Talousarviokohdat row: '8030101 Code Name' -> Code, Name"""
        val = str(row[0].value).strip() if row[0].value else None
        if not val:
            return None
        
        # SonarQube fix: Use split instead of regex to avoid potential ReDoS (python:S5852)
        # "8030101 Code Name" -> ["8030101", "Code Name"]
        parts = val.split(maxsplit=1)
        
        if len(parts) == 2:
            raw_code = parts[0]
            name = parts[1]
            
            # Verify code format (7 or 8 digits)
            if raw_code.isdigit() and (7 <= len(raw_code) <= 8):
                # Format raw_code "8030101" -> "8 03 01 01"
                if len(raw_code) == 7:
                     formatted_code = f"{raw_code[0]} {raw_code[1:3]} {raw_code[3:5]} {raw_code[5:7]}"
                     laji_id = raw_code[3:5] 
                else: # len == 8
                     formatted_code = f"{raw_code[0]} {raw_code[1:3]} {raw_code[3:5]} {raw_code[5:7].strip()}"
                     laji_id = raw_code[3:5]

                return {
                    'code': formatted_code,
                    'name': name,
                    'laji_id': laji_id
                }
        return None

    def _build_laji_lookup_list(self, laji_map):
        """
        Build a list for fuzzy matching project types to Laji IDs.
        Returns list of (SearchName, LajiID, PriorityScore).
        """
        laji_lookups = []
        for lid, info in laji_map.items():
            sname = info.get('search_name')
            cat = info.get('category') or ''
            
            if sname and len(sname) > 3:
                score = 1
                if 'projektialueiden' in cat.lower():
                    score = 3
                elif 'puisto' in cat.lower():
                    score = 2
                
                # Penalize generic "Esirakentaminen"
                if lid == '21' or sname.lower() == 'esirakentaminen':
                    score = 0
                
                laji_lookups.append((sname, lid, score))
        
        # Sort by Score (Desc), then Length (Desc)
        laji_lookups.sort(key=lambda x: (x[2], len(x[0])), reverse=True)
        return laji_lookups

    def _format_name_with_id(self, original_name, laji_id):
        """Prepend Laji ID to name if not already present."""
        if laji_id and not original_name.startswith(laji_id):
             return f"{laji_id} {original_name}"
        return original_name

    def _preview_project_types(self, wb, stats):
        """Preview Project Types & Priorities import"""
        self.stdout.write("Previewing Project Types & Priorities...")
        
        lajit_sheet = self._find_sheet_by_keyword(wb, 'lajit')
        talous_sheet = self._find_sheet_by_keyword(wb, 'talousarviokohdat')
        
        if not lajit_sheet or not talous_sheet:
            self.stdout.write(self.style.WARNING("  Required sheets not found"))
            return

        priorities_map = self._collect_priorities(lajit_sheet)
        self.stdout.write(f"  Found {len(priorities_map)} Priority Groups (Lajit)")
        
        count = 0
        for row in list(talous_sheet.rows)[:20]:
            data = self._parse_talous_row(row)
            if data:
                count += 1
                laji_id = data['laji_id']
                prios = priorities_map.get(laji_id, {}).get('priorities', [])
                if count <= 5:
                    self.stdout.write(f"  {data['code']} {data['name']} -> Laji {laji_id} ({len(prios)} priorities)")

        stats['project_types_created'] = 0

    def _import_project_types(self, wb, stats):
        """Import Project Types and apply Priorities"""
        self.stdout.write("Importing Project Types & Priorities...")
        
        lajit_sheet = self._find_sheet_by_keyword(wb, 'lajit')
        talous_sheet = self._find_sheet_by_keyword(wb, 'talousarviokohdat')
        
        if not lajit_sheet or not talous_sheet:
            self.stdout.write(self.style.WARNING("  Required sheets not found, skipping"))
            return

        # 1. Collect Metadata
        laji_map = self._collect_priorities(lajit_sheet)
        self.stdout.write(f"  Loaded metadata for {len(laji_map)} Laji groups")
        
        # 2. Build Lookup List
        laji_lookups = self._build_laji_lookup_list(laji_map)
        
        created_count = 0
        
        # 3. Iterate Talousarviokohdat
        for row in talous_sheet.rows:
            data = self._parse_talous_row(row)
            if not data:
                continue

            laji_id = data['laji_id']
            talous_name_lower = data['name'].lower()
            
            # Find best match from lookup list
            for sname, lid, score in laji_lookups:
                if sname.lower() in talous_name_lower:
                    laji_id = lid
                    break
            
            laji_info = laji_map.get(laji_id)
            prios = laji_info['priorities'] if laji_info else []
            category = laji_info['category'] if laji_info else None

            base_defaults = {
                'name': data['name'],
                'isActive': True,
                'category': category
            }

            if not prios:
                final_name = self._format_name_with_id(data['name'], laji_id)
                TalpaProjectType.objects.update_or_create(
                    code=data['code'],
                    priority=None,
                    defaults={
                        **base_defaults,
                        'name': final_name
                    }
                )
                created_count += 1
            else:
                for p in prios:
                    defaults = base_defaults.copy()
                    if p['description']:
                        defaults['description'] = p['description']
                    
                    defaults['name'] = self._format_name_with_id(data['name'], laji_id)

                    TalpaProjectType.objects.update_or_create(
                        code=data['code'],
                        priority=p['priority'],
                        defaults=defaults
                    )
                    created_count += 1
                    
        self.stdout.write(f"  Processed {created_count} project type definitions")
        stats['project_types_created'] = created_count

    def _print_summary(self, stats, dry_run):
        """Print import summary"""
        self.stdout.write(self.style.SUCCESS("IMPORT SUMMARY"))

        self.stdout.write(f"Asset Classes:   {stats['assets_created']} created, {stats['assets_updated']} updated")
        self.stdout.write(f"Service Classes: {stats['services_created']} created, {stats['services_updated']} updated")
        self.stdout.write(f"Number Ranges:   {stats['ranges_created']} created, {stats['ranges_updated']} updated")
        self.stdout.write(f"Project Types:   {stats.get('project_types_created', 0)} created/updated")

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
