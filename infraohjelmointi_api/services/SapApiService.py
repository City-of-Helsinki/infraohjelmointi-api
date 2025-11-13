import logging
import time
from datetime import datetime
from decimal import Decimal
from os import path

import environ
import requests
from django.core.exceptions import MultipleObjectsReturned

from ..models import Project
from .ProjectService import ProjectService
from .SapCostService import SapCostService
from .SapCurrentYearService import SapCurrentYearService

logger = logging.getLogger("infraohjelmointi_api")


env = environ.Env()
env.escape_proxy = True

if path.exists(".env"):
    env.read_env(".env")

requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS = "ALL:@SECLEVEL=1"


class SapApiService:
    def __init__(self) -> None:
        # connection setup
        self.session = requests.Session()
        self.session.auth = (env("SAP_USERNAME"), env("SAP_PASSWORD"))
        self.sap_api_url = env("SAP_API_URL")

        self.sap_api_costs_endpoint = env("SAP_COSTS_ENDPOINT")
        self.sap_api_commitments_endpoint = env("SAP_COMMITMENTS_ENDPOINT")

        # Set the sap start year to be 2017 to get all data from sap
        self.sap_fetch_all_data_start_year = 2017

    def sync_all_projects_from_sap(self, for_financial_statement: bool, sap_year=datetime.now().year) -> None:
        """Method to synchronise projects from SAP.\n
        Given projects must have sapProject otherwise project will not be syncrhonized.
        Will get for_financial_statement as True if called for fetching sap data for certain year only, 
        then also this certain year is given as parameter.
        """

        logger.debug("Synchronizing all projects in DB with SAP")
        projects=ProjectService.list_with_non_null_sap_id()

        # group projects by sapProject, all projects belong to same group
        projects_grouped_by_groups = self.__group_projects_by_sap_id(projects=projects)

        # make only one call either for ungroupped project are all groupped projects
        for group_id in projects_grouped_by_groups.keys():
            projects_grouped_by_sap_id = projects_grouped_by_groups[group_id]

            costs_by_sap_id_all = {}
            costs_by_sap_id_current_year = {}

            for sap_id in projects_grouped_by_sap_id.keys():
                projects_within_group = projects_grouped_by_sap_id[sap_id]
                sync_group: bool = len(projects_within_group) > 1

                project_id_list = [p.id for p in projects_within_group]

                self.__start_and_finish_log_print(sync_group, group_id, sap_id, project_id_list, is_start=True)

                # fetch costs and commitments from SAP
                start_time = time.perf_counter()
                sap_costs_and_commitments = {}
                
                # all sap data is not fetched, if function is called for getting sap data for certain year, 
                # f.g. for financial statement
                if not for_financial_statement:
                    sap_costs_and_commitments["all_sap_data"] = (
                        self.get_all_project_costs_and_commitments_from_sap(sap_id)
                    )
                
                sap_costs_and_commitments["current_year"] = (
                    self.get_costs_and_commitments_by_year(sap_id, sap_year)
                ) 

                handling_time = time.perf_counter() - start_time

                self.__start_and_finish_log_print(sync_group, group_id, sap_id, project_id_list, is_start=False, handling_time=handling_time)  

                if self.validate_costs_and_commitments(sap_costs_and_commitments):
                    costs_by_sap_id_all[sap_id] = sap_costs_and_commitments["all_sap_data"]

                    self.__store_sap_data(
                        service_class = SapCostService,
                        group_id=group_id,
                        costs_by_sap_id=costs_by_sap_id_all,
                        projects_grouped_by_sap_id=projects_grouped_by_sap_id,
                        current_year=sap_year,
                    )
                
                costs_by_sap_id_current_year[sap_id] = sap_costs_and_commitments["current_year"]
                self.__store_sap_data(
                    service_class = SapCurrentYearService,
                    group_id=group_id,
                    costs_by_sap_id=costs_by_sap_id_current_year,
                    projects_grouped_by_sap_id=projects_grouped_by_sap_id,
                    current_year=sap_year,
                )

    def get_costs_and_commitments_by_year(self, id: str, year) -> dict:
        """Method to fetch costs and commitments from SAP for given year"""
        logger.debug(f"Fetching SAP costs and commitments for year {year}")

        # Time frame for sap fetch is from 1.1.{year} to 1.1.{year+1}
        budat_start = datetime.now().replace(year=year, month=1, day=1, hour=0, minute=0, second=0)
        budat_end = datetime.now().replace(year=year+1, month=1, day=1, hour=0, minute=0, second=0)

        # Timeframe for fetching certain year's sap data is from 1.1.{start_year} to 1.1.{start_year+1}
        logger.debug(f"Starting to fetch costs and commitments for SAP id {id} from {budat_start} to {budat_end}")
        json_response_current_year = self.__fetch_costs_and_commitments_from_sap(budat_start, budat_end, id, all_sap_commitments=False)

        grouped_costs_and_commitments_current_year = self.__group_costs_and_commitments( 
        sap_costs_and_commitments=json_response_current_year,
        sap_id=id,
        )

        sap_costs_and_commitments = []
        sap_costs_and_commitments = grouped_costs_and_commitments_current_year

        return sap_costs_and_commitments

    def get_all_project_costs_and_commitments_from_sap(
        self,
        id: str,
    ) -> dict:
        """Method to fetch costs and commitments from SAP with given SAP project id"""
        logger.debug("in get_all_project_costs_and_commitments_from_sap")

        budat_start = datetime.now().replace(year=self.sap_fetch_all_data_start_year, month=1, day=1, hour=0, minute=0, second=0)
        budat_end = datetime.now().replace(year=datetime.now().year + 1, month=1, day=1, hour=0, minute=0, second=0)

        # Timeframe for fetching all sap data costs is from 1.1.2017 to 1.1.{currentyear+1},
        # and for commitments from 1.1.2017 to 1.1.{currentyear+1+5}
        logger.debug(f"Starting to fetch all costs for SAP id {id} from {budat_start.year} to {budat_end.year}, and all commitments from {budat_start.year} to {budat_end.year}+5 years")
        json_response_all = self.__fetch_costs_and_commitments_from_sap(budat_start, budat_end, id, all_sap_commitments=True)

        grouped_costs_and_commitments_all = self.__group_costs_and_commitments(
            sap_costs_and_commitments=json_response_all,
            sap_id=id,
        )
        sap_costs_and_commitments = []
        sap_costs_and_commitments= grouped_costs_and_commitments_all

        return sap_costs_and_commitments

    def __fetch_costs_and_commitments_from_sap(
            self,
            budat_start: datetime,
            budat_end: datetime,
            id: str,
            all_sap_commitments: bool
        )-> dict:
        date_format = "%Y-%m-%dT%H:%M:%S"
        # Init json_response, costs and commitments are zeros by default defaults
        json_response = {
            "costs": [
                {"Posid": f"{id}.01", "Wkgbtr": Decimal(0.000)},
                {"Posid": f"{id}.02", "Wkgbtr": Decimal(0.000)},
            ],
            "commitments": [
                {"Posid": f"{id}.01", "Wkgbtr": Decimal(0.000)},
                {"Posid": f"{id}.02", "Wkgbtr": Decimal(0.000)},
            ],
        }

        # Fetch costs from SAP
        api_url = f"{self.sap_api_url}{self.sap_api_costs_endpoint}".format(
            posid=id,
            budat_start=budat_start.replace(year=budat_start.year).strftime(
                date_format
            ),
            budat_end=budat_end.strftime(date_format),
        )
        json_response["costs"] = self.__make_sap_request(api_url, id, "costs")


        # Fetch commitments from SAP
        if all_sap_commitments:
            # Fetch commitments until the end fo the current year + 5 years
            end_date_for_commitment_fetch = budat_end.replace(year=budat_end.year + 5)

        else:
            # Fetch commitments until the end of the current year
            end_date_for_commitment_fetch = budat_end

        logger.debug(f"In commitment-fetch: start year: {budat_start.year} and end_year: {end_date_for_commitment_fetch.year}")
        api_url = f"{self.sap_api_url}{self.sap_api_commitments_endpoint}".format(
            posid=id,
            budat_start=budat_start.replace(year=budat_start.year).strftime(
                date_format
            ),
            budat_end=end_date_for_commitment_fetch.strftime(date_format),
        )
        json_response["commitments"] = self.__make_sap_request(api_url, id, "commitments")

        return json_response
    
    def __store_sap_data(
        self,
        service_class,
        group_id: str,
        costs_by_sap_id: dict,
        projects_grouped_by_sap_id: dict,
        current_year: int,
    ) -> None:
        """Helper method fo store SAP cost values into DB"""

        # store SAP costs for each project and calculate the total costs for project group
        project_group_id = group_id if group_id != "nogroup" else None
        project_group_costs = {"costs": 0, "commitments": 0}
        costs_by_projects = len(costs_by_sap_id.keys()) > 1
        for sap_id in costs_by_sap_id:
            costs_and_commitments = costs_by_sap_id[sap_id]
            costs = costs_and_commitments.get("costs", {"project_task": 0, "production_task": 0})
            commitments = costs_and_commitments.get("commitments", {"project_task": 0, "production_task": 0})

            for project in projects_grouped_by_sap_id[sap_id]:
                try:
                # store costs and commitments for project
                    project_sap_cost, _ = service_class.get_or_create(
                        project_id=project.id,
                        group_id=project_group_id,
                        year=current_year,
                    )
                except MultipleObjectsReturned as e:
                    logger.error(f"Multiple SapCost objects returned for project '{project.id}' / sap id '{sap_id}' / group id '{project_group_id}'. Error: {e}")
                    continue

                project_sap_cost.project_task_costs = costs["project_task"]
                project_sap_cost.production_task_costs = costs["production_task"]
                project_sap_cost.project_task_commitments = commitments["project_task"]
                project_sap_cost.production_task_commitments = commitments[
                    "production_task"
                ]
                project_sap_cost.sap_id = sap_id

                project_sap_cost.save()

                if costs_by_projects:
                    project_group_costs["costs"] += (
                        project_sap_cost.project_task_costs
                        + project_sap_cost.production_task_costs
                    )
                    project_group_costs["commitments"] += (
                        project_sap_cost.project_task_commitments
                        + project_sap_cost.production_task_commitments
                    )
                else:
                    project_group_costs["costs"] = (
                        project_sap_cost.project_task_costs
                        + project_sap_cost.production_task_costs
                    )
                    project_group_costs["commitments"] = (
                        project_sap_cost.project_task_commitments
                        + project_sap_cost.production_task_commitments
                    )
        if project_group_id is not None:
            try:
                group_sap_cost, _ = service_class.get_or_create(
                project_id=None,
                group_id=project_group_id,
                year=current_year,
                )

                group_sap_cost.group_combined_commitments = project_group_costs[
                    "commitments"
                ]
                group_sap_cost.group_combined_costs = project_group_costs["costs"]
                if not costs_by_projects:
                    group_sap_cost.sap_id = sap_id
                group_sap_cost.save()

            except MultipleObjectsReturned as e:
                logger.error(f"Multiple SapCost objects returned from database for sap id '{sap_id}' / group id '{project_group_id}'. Error: {e}")

    def __group_projects_by_sap_id(self, projects: list[Project]) -> dict:
        """Projects with same SAP id belong to same group thus projects will be grouped by SAP id"""

        # In DB groups can contain projects with different SAP id, thus costs of different projects will form group's costs

        grouped_projects = {}
        for project in projects:
            if not project.sapProject:
                continue
            group_id = project.projectGroup.id if project.projectGroup else "nogroup"
            projects_within_group = (
                grouped_projects[group_id] if group_id in grouped_projects else []
            )
            projects_within_group.append(project)
            grouped_projects[group_id] = projects_within_group

        for group_id in grouped_projects.keys():
            group_projects = grouped_projects[group_id]
            projects_grouped_by_sap_id = {}
            for project in group_projects:
                sap_id = project.sapProject

                group_items = (
                    projects_grouped_by_sap_id[sap_id]
                    if sap_id in projects_grouped_by_sap_id
                    else []
                )
                group_items.append(project)
                projects_grouped_by_sap_id[sap_id] = group_items

            grouped_projects[group_id] = projects_grouped_by_sap_id

        return grouped_projects

    def __group_costs_and_commitments(
        self, sap_costs_and_commitments: dict, sap_id: str
    ) -> dict:
        """Costs and commitments will be summed and grouped by task ids and will be stored to DB"""

        costs = sap_costs_and_commitments["costs"]
        costs_grouped_by_task = self.__calculate_values(sap_id=sap_id, values=costs)

        commitments = sap_costs_and_commitments["commitments"]
        commiments_grouped_by_task = self.__calculate_values(
            sap_id=sap_id, values=commitments
        )
        return {
            "costs": costs_grouped_by_task,
            "commitments": commiments_grouped_by_task,
        }

    def __calculate_values(self, sap_id: str, values: list) -> dict:
        """Costs (actual/commitment) must be calculated for groups thus\n
        result will include two keys separating groups: 01 and others.\n
        """
        # costs must be groupped by task
        # 01 = Project task (planning)
        # 02, 03, 04, 06, 99 = Production task (construction), will be grouped as one
        #
        # Task group id is formatted as sap_id.task_id (2814I06808.01,2814I06808.02,2814I06808.03, or 2814I06808.04)
        # Task id can also contain sub task i.e. 2814I06808.01.01, or sub sub task i.e. 2814I06808.01.01.02
        # 
        # NOTE: SAP returns task IDs in TWO formats:
        #   1. OLD FORMAT (with dots): "2814I03976.01" - backward compatible
        #   2. NEW FORMAT (concatenated): SAPID(variable length) + SUBPROJECT(3 digits) + TASK(2 digits)
        #      Example: "2814I03976" + "001" + "01" = "2814I0397600101"
        #      Planning tasks end with "01" (last 2 chars)
        #      Construction tasks end with "02", "03", "04", "06", "99", etc.
        #
        # EDGE CASE: Some SAP IDs themselves end in "01" (e.g., "2814I03901")
        #   - These bare IDs should NOT be classified as planning tasks
        #   - Only extended IDs (longer than base SAP ID) ending in "01" are planning tasks
        grouped_by_task = {
            "project_task": Decimal(0.000),
            "production_task": Decimal(0.000),
        }
        for cost in values:
            posid = cost["Posid"]
            
            # Determine if this is a planning task using robust logic:
            # 1. Check for old format with dots (e.g., "2814I03976.01")
            if ".01" in posid:
                is_planning = True
            # 2. Check for new format: Must be longer than base SAP ID, end with "01", and start with SAP ID
            #    This prevents false positives for bare SAP IDs that happen to end in "01"
            elif len(posid) > len(sap_id) and posid.endswith("01") and posid.startswith(sap_id):
                is_planning = True
            else:
                is_planning = False
            
            group_id = "project_task" if is_planning else "production_task"
            grouped_by_task[group_id] += Decimal(cost["Wkgbtr"])
        
        return grouped_by_task

    def __log_response_error(self, response: requests.Response, id: str) -> None:
        """Helper method to log response error"""
        logger.error(
            f"SAP responded with status code '{response.status_code}' and reason '{response.reason}' for given id '{id}'"
        )
        logger.error(
            f"SAP responded with response.json() '{response.json()}' for given id '{id}'"
        )
   
    def __make_sap_request(self, api_url, id, type):
        """Helper method to fetch costs from SAP"""
        start_time = time.perf_counter()
        logger.debug(f"Requesting API for {type} from {api_url}")
        response = self.session.get(api_url)
        logger.debug(f"Response: {response}")
        logger.debug(f"Response.raw: {response.raw}")
        logger.debug(f"Response status code: {response.status_code}")
        logger.debug(f"Response content: {response.content}")
        try:
            logger.info(response.json())
        except Exception as e:
            logger.error(f"Error parsing JSON response for id '{id}': {e}")
        response_time = time.perf_counter() - start_time

        logger.debug(f"SAP responded in {response_time}s")

        # Check if SAP responded with error
        if response.status_code != 200:
            self.__log_response_error(response, id)
            return {}

        else:
            return response.json()["d"]["results"]
    
    def validate_costs_and_commitments(self, costs_and_commitments) -> bool:
        if 'all_sap_data' in costs_and_commitments and 'current_year' in costs_and_commitments:
            return True
        
        else:
            return False
        
    def __start_and_finish_log_print(self, sync_group, group_id, sap_id, project_id_list, is_start, handling_time=None):
        if (is_start):
            if sync_group:
                logger.debug(
                    f"Synchronizing given project group '{group_id}' with SAP Id '{sap_id}' from SAP"
                )
            else:
                logger.debug(
                    f"Synchronizing given project(s) '{project_id_list}' with SAP Id '{sap_id}' from SAP"
                )
        else:
            if sync_group:
                logger.info(
                    f"Finished fetching data from SAP for project group '{group_id}' in {handling_time}s"
                )
            else:
                logger.info(
                    f"Finished fetching data from SAP for project {project_id_list} in {handling_time}s"
                )
