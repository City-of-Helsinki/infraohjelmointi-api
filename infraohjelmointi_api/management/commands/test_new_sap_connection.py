"""
Test script to probe the new SAP S4 connection without modifying anything.

This script:
- Tests connection to new SAP URL(s)
- Fetches sample data (Toteumat/costs and Sidotut/commitments)
- Shows what data is available
- Does NOT modify database or any configuration
- Safe to run anytime

Usage:
    python manage.py test_new_sap_connection [--sap-id SAP_ID] [--year YEAR] [--url URL]
    
    --url options:
        both        - Test both direct instance AND load balancer (default)
        direct      - Test only direct instance (vhhskp50ci:44300)
        loadbalancer - Test only load balancer (s4prod:44380)
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

# SAP S4 URLs
SAP_URLS = {
    "direct": {
        "name": "Direct Instance (P50)",
        "url": "https://vhhskp50ci.sap.hel.fi:44300/sap/opu/odata/sap/ZINFRA_TOOL_SRV/",
    },
    "loadbalancer": {
        "name": "Load Balancer (Web Dispatcher)",
        "url": "https://s4prod.sap.hel.fi:44380/sap/opu/odata/sap/ZINFRA_TOOL_SRV/",
    },
}


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
        parser.add_argument(
            '--url',
            type=str,
            choices=['both', 'direct', 'loadbalancer'],
            default='both',
            help='Which URL to test: both (default), direct (vhhskp50ci:44300), or loadbalancer (s4prod:44380)',
        )

    def handle(self, *args, **options):
        sap_id = options.get('sap_id')
        test_year = options.get('year', 2026)
        test_2025 = options.get('test_2025', False)
        url_choice = options.get('url', 'both')

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

        # Determine which URLs to test
        if url_choice == 'both':
            urls_to_test = ['direct', 'loadbalancer']
        else:
            urls_to_test = [url_choice]

        self.stdout.write(f"Testing URL(s): {', '.join(urls_to_test)}")
        self.stdout.write("")

        # Common endpoints (same for both URLs)
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

        # Store results for comparison
        url_results = {}

        # Test each URL
        for url_key in urls_to_test:
            url_config = SAP_URLS[url_key]
            url_name = url_config["name"]
            base_url = url_config["url"]

            self.stdout.write("=" * 80)
            self.stdout.write(self.style.SUCCESS(f"TESTING: {url_name}"))
            self.stdout.write(f"URL: {base_url}")
            self.stdout.write("=" * 80)
            self.stdout.write("")

            url_results[url_key] = {"name": url_name, "connection": False, "costs": None, "commitments": None}

            # Test 1: Connection test
            self.stdout.write("-" * 80)
            self.stdout.write(self.style.WARNING("TEST 1: Connection Test"))
            self.stdout.write("-" * 80)

            try:
                test_url = f"{base_url}$metadata"
                self.stdout.write(f"Probing: {test_url}")

                response = session.get(test_url, verify=False, timeout=30)
                self.stdout.write(f"Status Code: {response.status_code}")

                if response.status_code == 200:
                    self.stdout.write(self.style.SUCCESS("✓ Connection successful!"))
                    url_results[url_key]["connection"] = True
                elif response.status_code == 401:
                    self.stdout.write(self.style.ERROR("✗ Authentication failed - check credentials"))
                    continue
                elif response.status_code == 403:
                    self.stdout.write(self.style.ERROR("✗ Access forbidden - check permissions"))
                    continue
                else:
                    self.stdout.write(self.style.WARNING(f"⚠ Unexpected status: {response.status_code}"))
                    self.stdout.write(f"Response: {response.text[:200]}")
            except requests.exceptions.SSLError as e:
                self.stdout.write(self.style.ERROR(f"✗ SSL Error: {e}"))
                continue
            except requests.exceptions.ConnectionError as e:
                self.stdout.write(self.style.ERROR(f"✗ Connection Error: {e}"))
                self.stdout.write("Check VPN, network, or firewall settings")
                continue
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Error: {e}"))
                continue

            self.stdout.write("")

            # Test 2: Fetch Toteumat (Costs)
            self.stdout.write("-" * 80)
            self.stdout.write(self.style.WARNING(f"TEST 2: Fetch Toteumat (Costs) for {test_year}"))
            self.stdout.write("-" * 80)

            date_format = "%Y-%m-%dT%H:%M:%S"
            budat_start = datetime.now().replace(year=test_year, month=1, day=1, hour=0, minute=0, second=0)
            budat_end = datetime.now().replace(year=test_year + 1, month=1, day=1, hour=0, minute=0, second=0)

            costs_url = f"{base_url}{new_costs_endpoint}".format(
                posid=sap_id,
                budat_start=budat_start.strftime(date_format),
                budat_end=budat_end.strftime(date_format),
            )

            self.stdout.write(f"Date range: {budat_start.date()} to {budat_end.date()}")

            try:
                start_time = time.perf_counter()
                response = session.get(costs_url, verify=False, timeout=60)
                response_time = time.perf_counter() - start_time

                self.stdout.write(f"Status Code: {response.status_code}")
                self.stdout.write(f"Response Time: {response_time:.2f}s")

                if response.status_code == 200:
                    data = response.json()
                    results = data.get("d", {}).get("results", [])
                    self.stdout.write(self.style.SUCCESS(f"✓ Success! Found {len(results)} cost entries"))
                    if results:
                        total = sum(Decimal(str(entry.get("Wkgbtr", 0))) for entry in results)
                        self.stdout.write(f"Total costs: {total:,.2f}")
                        url_results[url_key]["costs"] = total
                    else:
                        url_results[url_key]["costs"] = Decimal(0)
                else:
                    self.stdout.write(self.style.ERROR(f"✗ Request failed"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Error: {e}"))

            self.stdout.write("")

            # Test 3: Fetch Sidotut (Commitments)
            self.stdout.write("-" * 80)
            self.stdout.write(self.style.WARNING(f"TEST 3: Fetch Sidotut (Commitments) for {test_year}"))
            self.stdout.write("-" * 80)

            commit_start = datetime.now().replace(year=2017, month=1, day=1, hour=0, minute=0, second=0)
            commit_end = datetime.now().replace(year=test_year + 6, month=1, day=1, hour=0, minute=0, second=0)

            commitments_url = f"{base_url}{new_commitments_endpoint}".format(
                posid=sap_id,
                budat_start=commit_start.strftime(date_format),
                budat_end=commit_end.strftime(date_format),
            )

            self.stdout.write(f"Date range: {commit_start.date()} to {commit_end.date()}")

            try:
                start_time = time.perf_counter()
                response = session.get(commitments_url, verify=False, timeout=60)
                response_time = time.perf_counter() - start_time

                self.stdout.write(f"Status Code: {response.status_code}")
                self.stdout.write(f"Response Time: {response_time:.2f}s")

                if response.status_code == 200:
                    data = response.json()
                    results = data.get("d", {}).get("results", [])
                    self.stdout.write(self.style.SUCCESS(f"✓ Success! Found {len(results)} commitment entries"))
                    if results:
                        total = sum(Decimal(str(entry.get("Wkgbtr", 0))) for entry in results)
                        self.stdout.write(f"Total commitments: {total:,.2f}")
                        url_results[url_key]["commitments"] = total
                    else:
                        url_results[url_key]["commitments"] = Decimal(0)
                else:
                    self.stdout.write(self.style.ERROR(f"✗ Request failed"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Error: {e}"))

            self.stdout.write("")

        # Summary comparison (if testing both)
        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS("TEST RESULTS SUMMARY"))
        self.stdout.write("=" * 80)
        self.stdout.write("")

        if len(urls_to_test) > 1:
            self.stdout.write("COMPARISON:")
            self.stdout.write("-" * 60)
            self.stdout.write(f"{'Endpoint':<30} {'Connection':<12} {'Costs':<15} {'Commitments':<15}")
            self.stdout.write("-" * 60)
            for url_key, result in url_results.items():
                conn = "✓" if result["connection"] else "✗"
                costs = f"{result['costs']:,.2f}" if result['costs'] is not None else "N/A"
                commits = f"{result['commitments']:,.2f}" if result['commitments'] is not None else "N/A"
                self.stdout.write(f"{result['name']:<30} {conn:<12} {costs:<15} {commits:<15}")
            self.stdout.write("-" * 60)
            self.stdout.write("")

            # Check if results match
            if all(r["connection"] for r in url_results.values()):
                self.stdout.write(self.style.SUCCESS("✓ Both URLs are working!"))
                cost_vals = [r["costs"] for r in url_results.values() if r["costs"] is not None]
                commit_vals = [r["commitments"] for r in url_results.values() if r["commitments"] is not None]
                if len(cost_vals) == 2 and cost_vals[0] == cost_vals[1]:
                    self.stdout.write(self.style.SUCCESS("✓ Cost data matches between both endpoints"))
                elif len(cost_vals) == 2:
                    self.stdout.write(self.style.WARNING("⚠ Cost data differs between endpoints"))
                if len(commit_vals) == 2 and commit_vals[0] == commit_vals[1]:
                    self.stdout.write(self.style.SUCCESS("✓ Commitment data matches between both endpoints"))
                elif len(commit_vals) == 2:
                    self.stdout.write(self.style.WARNING("⚠ Commitment data differs between endpoints"))
            else:
                for url_key, result in url_results.items():
                    if not result["connection"]:
                        self.stdout.write(self.style.ERROR(f"✗ {result['name']} failed to connect"))
        else:
            result = list(url_results.values())[0]
            if result["connection"]:
                self.stdout.write(self.style.SUCCESS(f"✓ {result['name']} is working!"))
            else:
                self.stdout.write(self.style.ERROR(f"✗ {result['name']} failed"))

        self.stdout.write("")
        self.stdout.write("RECOMMENDATION:")
        if "loadbalancer" in url_results and url_results["loadbalancer"]["connection"]:
            self.stdout.write(self.style.SUCCESS("→ Use LOAD BALANCER URL for production (future-proof)"))
            self.stdout.write("  https://s4prod.sap.hel.fi:44380/sap/opu/odata/sap/ZINFRA_TOOL_SRV/")
        elif "direct" in url_results and url_results["direct"]["connection"]:
            self.stdout.write(self.style.WARNING("→ Load balancer not working, use DIRECT URL"))
            self.stdout.write("  https://vhhskp50ci.sap.hel.fi:44300/sap/opu/odata/sap/ZINFRA_TOOL_SRV/")

        self.stdout.write("")
        self.stdout.write("This was a READ-ONLY test. No data was modified.")

