from django.core.management.base import BaseCommand
from django.db.models import Q

from infraohjelmointi_api.models import Project, SapCost
from infraohjelmointi_api.services.ProjectService import ProjectService


class Command(BaseCommand):
    help = "Validate that all projects with SAP IDs have frozen 2025 data. " + "\nUsage: python manage.py validate_sap_freeze [--check-all-projects]"

    def add_arguments(self, parser):
        parser.add_argument(
            '--check-all-projects',
            action='store_true',
            help='Check all projects, not just those with SAP IDs',
        )
        parser.add_argument(
            '--fail-on-missing',
            action='store_true',
            help='Exit with error code if any projects are missing frozen data',
        )

    def handle(self, *args, **options):
        check_all = options.get('check_all_projects', False)
        fail_on_missing = options.get('fail_on_missing', False)

        self.stdout.write("=" * 80)
        self.stdout.write("SAP Freeze Validation - Checking for frozen 2025 data")
        self.stdout.write("=" * 80)

        # Get projects with SAP IDs
        if check_all:
            projects = Project.objects.all()
            self.stdout.write(f"\nChecking all projects (total: {projects.count()})")
        else:
            projects = ProjectService.list_with_non_null_sap_id()
            self.stdout.write(f"\nChecking projects with SAP IDs (total: {projects.count()})")

        if not projects.exists():
            self.stdout.write(self.style.WARNING("No projects found to check."))
            return

        # Get all SAP IDs
        sap_ids = set(projects.values_list('sapProject', flat=True).distinct())
        sap_ids = {sap_id for sap_id in sap_ids if sap_id}  # Remove None/empty

        self.stdout.write(f"Unique SAP IDs: {len(sap_ids)}")

        # Check each SAP ID for frozen 2025 data
        missing_data = []
        has_data = []
        total_costs = 0
        total_projects_with_data = 0

        for sap_id in sorted(sap_ids):
            # Get all SapCost entries for this SAP ID and year 2025
            sap_costs_2025 = SapCost.objects.filter(
                sap_id=sap_id,
                year=2025
            )

            if not sap_costs_2025.exists():
                missing_data.append({
                    'sap_id': sap_id,
                    'projects': list(projects.filter(sapProject=sap_id).values_list('id', 'name')),
                    'reason': 'No 2025 data found'
                })
            else:
                # Check if any entry has non-zero costs
                has_costs = any(
                    cost.project_task_costs > 0 or cost.production_task_costs > 0
                    for cost in sap_costs_2025
                )

                if not has_costs:
                    missing_data.append({
                        'sap_id': sap_id,
                        'projects': list(projects.filter(sapProject=sap_id).values_list('id', 'name')),
                        'reason': '2025 data exists but all costs are zero'
                    })
                else:
                    # Sum up costs for this SAP ID
                    project_costs = sum(cost.project_task_costs + cost.production_task_costs for cost in sap_costs_2025)
                    has_data.append({
                        'sap_id': sap_id,
                        'projects': list(projects.filter(sapProject=sap_id).values_list('id', 'name')),
                        'costs': project_costs,
                        'entries': sap_costs_2025.count()
                    })
                    total_costs += project_costs
                    total_projects_with_data += len(projects.filter(sapProject=sap_id))

        # Print summary
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("VALIDATION SUMMARY")
        self.stdout.write("=" * 80)

        self.stdout.write(f"\n✅ SAP IDs with frozen 2025 data: {len(has_data)}")
        self.stdout.write(f"❌ SAP IDs missing frozen 2025 data: {len(missing_data)}")
        self.stdout.write(f"\nTotal projects with data: {total_projects_with_data}")
        self.stdout.write(f"Total frozen costs: {total_costs:,.2f}")

        # Print details of missing data
        if missing_data:
            self.stdout.write("\n" + "=" * 80)
            self.stdout.write(self.style.ERROR("MISSING FROZEN DATA:"))
            self.stdout.write("=" * 80)
            for item in missing_data:
                self.stdout.write(f"\nSAP ID: {item['sap_id']}")
                self.stdout.write(f"  Reason: {item['reason']}")
                self.stdout.write(f"  Affected projects: {len(item['projects'])}")
                for project_id, project_name in item['projects'][:5]:  # Show first 5
                    self.stdout.write(f"    - {project_name} ({project_id})")
                if len(item['projects']) > 5:
                    self.stdout.write(f"    ... and {len(item['projects']) - 5} more")

        # Print sample of projects with data
        if has_data:
            self.stdout.write("\n" + "=" * 80)
            self.stdout.write(self.style.SUCCESS("SAMPLE PROJECTS WITH FROZEN DATA:"))
            self.stdout.write("=" * 80)
            for item in has_data[:10]:  # Show first 10
                self.stdout.write(f"\nSAP ID: {item['sap_id']}")
                self.stdout.write(f"  Frozen costs: {item['costs']:,.2f}")
                self.stdout.write(f"  DB entries: {item['entries']}")
                self.stdout.write(f"  Projects: {len(item['projects'])}")

        # Final status
        self.stdout.write("\n" + "=" * 80)
        if missing_data:
            self.stdout.write(self.style.ERROR(f"⚠️  VALIDATION FAILED: {len(missing_data)} SAP ID(s) missing frozen 2025 data"))
            if fail_on_missing:
                self.stdout.write(self.style.ERROR("Exiting with error code due to --fail-on-missing flag"))
                exit(1)
        else:
            self.stdout.write(self.style.SUCCESS("✅ VALIDATION PASSED: All SAP IDs have frozen 2025 data"))
        self.stdout.write("=" * 80)
