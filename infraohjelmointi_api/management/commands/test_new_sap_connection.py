"""
Test script to probe the new SAP S4 connection without modifying anything.

This script:
- Tests connection to new SAP URL
- Fetches sample data (Toteumat/costs and Sidotut/commitments)
- Shows what data is available
- Does NOT modify database or any configuration
- Safe to run anytime

Usage:
    python manage.py test_new_sap_connection [--sap-id SAP_ID] [--year YEAR]
"""

import json
import time
from datetime import datetime, timezone
from decimal import Decimal

import os
from os import path

import environ
import requests
from django.core.management.base import BaseCommand

from infraohjelmointi_api.services.ProjectService import ProjectService

env = environ.Env()
env.escape_proxy = True

# Read .env file if it exists (same as SapApiService)
if path.exists(".env"):
    env.read_env(".env")

# Allow insecure SSL (same as in SapApiService)
requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS = "ALL:@SECLEVEL=1"


class Command(BaseCommand):
    help = "Test new SAP S4 connection - safe read-only probe"

    def add_arguments(self, parser):
        parser.add_argument(
            '--sap-id',
            type=str,
            help='Specific SAP ID to test (if not provided, uses first available)',
        )
        parser.add_argument(
            '--year',
            type=int,
            default=2026,
            help='Year to test (default: 2026)',
        )
        parser.add_argument(
            '--test-2025',
            action='store_true',
            help='Also test 2025 data (to verify historical data availability)',
        )

    def handle(self, *args, **options):
        sap_id = options.get('sap_id')
        test_year = options.get('year', 2026)
        test_2025 = options.get('test_2025', False)

        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS("NEW SAP S4 CONNECTION TEST"))
        self.stdout.write("=" * 80)
        self.stdout.write("")

        # Get SAP ID to test
        if not sap_id:
            projects = ProjectService.list_with_non_null_sap_id()
            if not projects.exists():
                # Fallback to known test IDs if database is empty
                known_test_ids = [
                    "2814I00100",  # From IO-790.md verification example
                    "2814I00708",  # From test files
                    "2814I00720",  # Valtimontie project
                    "2814I04749",  # From test files
                ]
                self.stdout.write(self.style.WARNING("No projects with SAP IDs found in database"))
                self.stdout.write(f"Using fallback test ID: {known_test_ids[0]}")
                self.stdout.write(f"(Other known IDs: {', '.join(known_test_ids[1:])})")
                sap_id = known_test_ids[0]
            else:
                sap_id = projects.first().sapProject
                self.stdout.write(f"Using SAP ID from database: {sap_id}")
        else:
            self.stdout.write(f"Using provided SAP ID: {sap_id}")

        self.stdout.write("")

        # New SAP configuration
        new_sap_url = "https://vhhskp50ci.sap.hel.fi:44300/sap/opu/odata/sap/ZINFRA_TOOL_SRV/"
        new_costs_endpoint = "ActualCostsSet?sap-client=300&$format=json&$filter=(Posid eq '{posid}') and (Budat ge datetime'{budat_start}' and Budat le datetime'{budat_end}')"
        new_commitments_endpoint = "CommitmentLinesSet?sap-client=300&$format=json&$filter=(Posid eq '{posid}') and (Budat ge datetime'{budat_start}' and Budat le datetime'{budat_end}')"

        # Get credentials from environment
        try:
            sap_username = env("SAP_USERNAME")
            sap_password = env("SAP_PASSWORD")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error reading SAP credentials: {e}"))
            self.stdout.write("Make sure SAP_USERNAME and SAP_PASSWORD are set in environment")
            return

        if not sap_username or not sap_password:
            self.stdout.write(self.style.ERROR("SAP_USERNAME or SAP_PASSWORD not set"))
            return

        self.stdout.write("✓ Credentials found in environment")
        self.stdout.write("")

        # Create session
        session = requests.Session()
        session.auth = (sap_username, sap_password)

        # Test 1: Connection test
        self.stdout.write("-" * 80)
        self.stdout.write(self.style.WARNING("TEST 1: Connection Test"))
        self.stdout.write("-" * 80)

        try:
            # Try to access the service root
            test_url = f"{new_sap_url}$metadata"
            self.stdout.write(f"Testing connection to: {new_sap_url}")
            self.stdout.write(f"Probing: {test_url}")

            # Note: verify=False is intentional - matches production SapApiService behavior
            # SAP systems use self-signed certificates that require this setting
            response = session.get(test_url, verify=False, timeout=30)  # NOSONAR
            self.stdout.write(f"Status Code: {response.status_code}")

            if response.status_code == 200:
                self.stdout.write(self.style.SUCCESS("✓ Connection successful!"))
            elif response.status_code == 401:
                self.stdout.write(self.style.ERROR("✗ Authentication failed - check credentials"))
                return
            elif response.status_code == 403:
                self.stdout.write(self.style.ERROR("✗ Access forbidden - check permissions"))
                return
            else:
                self.stdout.write(self.style.WARNING(f"⚠ Unexpected status: {response.status_code}"))
                self.stdout.write(f"Response: {response.text[:200]}")
        except requests.exceptions.SSLError as e:
            self.stdout.write(self.style.ERROR(f"✗ SSL Error: {e}"))
            self.stdout.write("Note: SSL verification is disabled (same as production)")
        except requests.exceptions.ConnectionError as e:
            self.stdout.write(self.style.ERROR(f"✗ Connection Error: {e}"))
            self.stdout.write("Check VPN, network, or firewall settings")
            return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Error: {e}"))
            return

        self.stdout.write("")

        # Test 2: Fetch Toteumat (Costs) for 2026
        self.stdout.write("-" * 80)
        self.stdout.write(self.style.WARNING(f"TEST 2: Fetch Toteumat (Costs) for {test_year}"))
        self.stdout.write("-" * 80)

        date_format = "%Y-%m-%dT%H:%M:%S"
        budat_start = datetime.now().replace(year=test_year, month=1, day=1, hour=0, minute=0, second=0)
        budat_end = datetime.now().replace(year=test_year + 1, month=1, day=1, hour=0, minute=0, second=0)

        costs_url = f"{new_sap_url}{new_costs_endpoint}".format(
            posid=sap_id,
            budat_start=budat_start.strftime(date_format),
            budat_end=budat_end.strftime(date_format),
        )

        self.stdout.write(f"URL: {costs_url}")
        self.stdout.write(f"Date range: {budat_start.date()} to {budat_end.date()}")

        try:
            start_time = time.perf_counter()
            # Note: verify=False is intentional - matches production SapApiService behavior
            response = session.get(costs_url, verify=False, timeout=60)  # NOSONAR
            response_time = time.perf_counter() - start_time

            self.stdout.write(f"Status Code: {response.status_code}")
            self.stdout.write(f"Response Time: {response_time:.2f}s")

            if response.status_code == 200:
                try:
                    data = response.json()
                    results = data.get("d", {}).get("results", [])
                    self.stdout.write(self.style.SUCCESS(f"✓ Success! Found {len(results)} cost entries"))

                    if results:
                        self.stdout.write("\nSample data (first 3 entries):")
                        for i, entry in enumerate(results[:3], 1):
                            posid = entry.get("Posid", "N/A")
                            amount = entry.get("Wkgbtr", 0)
                            date = entry.get("Budat", "N/A")
                            self.stdout.write(f"  {i}. Posid: {posid}, Amount: {amount}, Date: {date}")

                        # Calculate totals
                        total = sum(Decimal(str(entry.get("Wkgbtr", 0))) for entry in results)
                        self.stdout.write(f"\nTotal costs: {total:,.2f}")
                    else:
                        self.stdout.write(self.style.WARNING("⚠ No cost data found for this period"))
                except json.JSONDecodeError as e:
                    self.stdout.write(self.style.ERROR(f"✗ JSON parse error: {e}"))
                    self.stdout.write(f"Response: {response.text[:500]}")
            else:
                self.stdout.write(self.style.ERROR(f"✗ Request failed"))
                self.stdout.write(f"Response: {response.text[:500]}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Error: {e}"))

        self.stdout.write("")

        # Test 3: Fetch Sidotut (Commitments) for 2026
        self.stdout.write("-" * 80)
        self.stdout.write(self.style.WARNING(f"TEST 3: Fetch Sidotut (Commitments) for {test_year}"))
        self.stdout.write("-" * 80)

        # Commitments: from 2017 to test_year + 5 (same as production logic)
        commit_start = datetime.now().replace(year=2017, month=1, day=1, hour=0, minute=0, second=0)
        commit_end = datetime.now().replace(year=test_year + 6, month=1, day=1, hour=0, minute=0, second=0)

        commitments_url = f"{new_sap_url}{new_commitments_endpoint}".format(
            posid=sap_id,
            budat_start=commit_start.strftime(date_format),
            budat_end=commit_end.strftime(date_format),
        )

        self.stdout.write(f"URL: {commitments_url}")
        self.stdout.write(f"Date range: {commit_start.date()} to {commit_end.date()}")

        try:
            start_time = time.perf_counter()
            # Note: verify=False is intentional - matches production SapApiService behavior
            response = session.get(commitments_url, verify=False, timeout=60)  # NOSONAR
            response_time = time.perf_counter() - start_time

            self.stdout.write(f"Status Code: {response.status_code}")
            self.stdout.write(f"Response Time: {response_time:.2f}s")

            if response.status_code == 200:
                try:
                    data = response.json()
                    results = data.get("d", {}).get("results", [])
                    self.stdout.write(self.style.SUCCESS(f"✓ Success! Found {len(results)} commitment entries"))

                    if results:
                        self.stdout.write("\nSample data (first 3 entries):")
                        for i, entry in enumerate(results[:3], 1):
                            posid = entry.get("Posid", "N/A")
                            amount = entry.get("Wkgbtr", 0)
                            date = entry.get("Budat", "N/A")
                            self.stdout.write(f"  {i}. Posid: {posid}, Amount: {amount}, Date: {date}")

                        # Calculate totals
                        total = sum(Decimal(str(entry.get("Wkgbtr", 0))) for entry in results)
                        self.stdout.write(f"\nTotal commitments: {total:,.2f}")

                        # Show breakdown by year if possible
                        if results:
                            years = {}
                            for entry in results:
                                date_str = entry.get("Budat", "")
                                if date_str:
                                    try:
                                        year = datetime.fromisoformat(date_str.replace("Z", "+00:00")).year
                                        years[year] = years.get(year, 0) + Decimal(str(entry.get("Wkgbtr", 0)))
                                    except:
                                        pass

                            if years:
                                self.stdout.write("\nBreakdown by year:")
                                for year in sorted(years.keys()):
                                    self.stdout.write(f"  {year}: {years[year]:,.2f}")
                    else:
                        self.stdout.write(self.style.WARNING("⚠ No commitment data found for this period"))
                except json.JSONDecodeError as e:
                    self.stdout.write(self.style.ERROR(f"✗ JSON parse error: {e}"))
                    self.stdout.write(f"Response: {response.text[:500]}")
            else:
                self.stdout.write(self.style.ERROR(f"✗ Request failed"))
                self.stdout.write(f"Response: {response.text[:500]}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Error: {e}"))

        self.stdout.write("")

        # Test 4: Test 2025 data (if requested)
        if test_2025:
            self.stdout.write("-" * 80)
            self.stdout.write(self.style.WARNING("TEST 4: Fetch 2025 Data (Historical)"))
            self.stdout.write("-" * 80)

            budat_start_2025 = datetime.now().replace(year=2025, month=1, day=1, hour=0, minute=0, second=0)
            budat_end_2025 = datetime.now().replace(year=2026, month=1, day=1, hour=0, minute=0, second=0)

            costs_url_2025 = f"{new_sap_url}{new_costs_endpoint}".format(
                posid=sap_id,
                budat_start=budat_start_2025.strftime(date_format),
                budat_end=budat_end_2025.strftime(date_format),
            )

            self.stdout.write(f"Testing if new SAP has 2025 cost data...")
            self.stdout.write(f"URL: {costs_url_2025}")

            try:
                # Note: verify=False is intentional - matches production SapApiService behavior
                response = session.get(costs_url_2025, verify=False, timeout=60)  # NOSONAR
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("d", {}).get("results", [])
                    if results:
                        total = sum(Decimal(str(entry.get("Wkgbtr", 0))) for entry in results)
                        self.stdout.write(self.style.SUCCESS(f"✓ New SAP has 2025 data: {len(results)} entries, total: {total:,.2f}"))
                        self.stdout.write(self.style.WARNING("⚠ Note: This data will NOT be used after freeze (2025 is frozen)"))
                    else:
                        self.stdout.write(self.style.WARNING("⚠ New SAP has no 2025 data (expected - will use frozen data)"))
                else:
                    self.stdout.write(self.style.WARNING(f"⚠ Could not fetch 2025 data (status: {response.status_code})"))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"⚠ Error testing 2025 data: {e}"))

        # Summary
        self.stdout.write("")
        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS("TEST COMPLETE"))
        self.stdout.write("=" * 80)
        self.stdout.write("")
        self.stdout.write("This was a READ-ONLY test. No data was modified.")
        self.stdout.write("If all tests passed, the new SAP connection is ready for switch day.")
