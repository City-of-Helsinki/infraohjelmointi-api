import requests
from os import path
import environ
import logging
import time
from decimal import Decimal

from datetime import datetime

logger = logging.getLogger("infraohjelmointi_api")

from ..models import (
    Project,
)

from .ProjectService import ProjectService
from .SapCostService import SapCostService


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

    def sync_all_projects_from_sap(self) -> None:
        """Method to synchronise all projects in DB with SAP project costs and commitments.\n"""

        logger.debug("Synchronizing all projects in DB with SAP")
        self.__sync_projects_from_sap(
            projects=ProjectService.list_with_non_null_sap_id()
        )

    def sync_project_from_sap(self, sap_id: str) -> None:
        """Method to synchronise project with given SAP id with SAP project costs and commitments.\n"""

        logger.debug(f"Synchronizing project(s) with SAP Id '{sap_id}' with SAP")
        projects = ProjectService.get_by_sap_id(sap_id=sap_id)
        self.__sync_projects_from_sap(projects=projects)

    def __sync_projects_from_sap(self, projects: list[Project]) -> None:
        """Method to synchronise projects from SAP.\n
        Given projects must have sapProject otherwise project will not be syncrhonized.
        """

        # group projects by sapProject, all projects belong to same group
        projects_grouped_by_groups = self.__group_projects_by_sap_id(projects=projects)
        current_year = datetime.now().year

        # make only one call either for ungroupped project are all groupped projects
        for group_id in projects_grouped_by_groups.keys():
            projects_grouped_by_sap_id = projects_grouped_by_groups[group_id]

            costs_by_sap_id = {}

            for sap_id in projects_grouped_by_sap_id.keys():
                projects_within_group = projects_grouped_by_sap_id[sap_id]
                sync_group: bool = len(projects_within_group) > 1

                project_id_list = [p.id for p in projects_within_group]

                if sync_group:
                    logger.debug(
                        f"Synchronizing given project group '{group_id}' with SAP Id '{sap_id}' from SAP"
                    )
                else:
                    logger.debug(
                        f"Synchronizing given project(s) '{project_id_list}' with SAP Id '{sap_id}' from SAP"
                    )

                start_time = time.perf_counter()
                # fetch project costs from SAP
                sap_costs_and_commitments = (
                    self.get_project_costs_and_commitments_from_sap(sap_id)
                )

                costs_by_sap_id[sap_id] = sap_costs_and_commitments

                handling_time = time.perf_counter() - start_time
                if sync_group:
                    logger.debug(
                        f"Project group '{group_id}' costs loaded successully from SAP in {handling_time}s"
                    )
                else:
                    logger.info(
                        f"Project {project_id_list} costs loaded successully from SAP in {handling_time}s"
                    )

            self.__store_sap_costs(
                group_id=group_id,
                costs_by_sap_id=costs_by_sap_id,
                projects_grouped_by_sap_id=projects_grouped_by_sap_id,
                current_year=current_year,
            )

    def get_project_costs_and_commitments_from_sap(
        self,
        id: str,
        budat_start: datetime = datetime.now().replace(
            month=1, day=1, hour=0, minute=0, second=0
        ),
        budat_end: datetime = datetime.now().replace(
            year=datetime.now().year + 1, month=1, day=1, hour=0, minute=0, second=0
        ),
    ) -> dict:
        """Method to fetch costs and commitments from SAP with given SAP project id"""
        logger.debug("in get_project_costs_and_commitments_from_sap")
        start_time = time.perf_counter()
        date_format = "%Y-%m-%dT%H:%M:%S"

        # Fetch projects by SAP ID and get earliest planning start year
        projects = ProjectService.get_by_sap_id(id)

        sap_start_year = None

        for project in projects:
            if not project.planningStartYear:
                logger.debug(f"No planning start year set for project ID {project.id}.")
            elif project.planningStartYear > budat_start.year:
                logger.debug(f"Planning start year is set in the future for project ID {project.id}.")
            elif (sap_start_year and sap_start_year > project.planningStartYear) or not sap_start_year:
                sap_start_year = project.planningStartYear

        if sap_start_year:
            api_url = f"{self.sap_api_url}{self.sap_api_costs_endpoint}".format(
                posid=id,
                budat_start=budat_start.replace(year=sap_start_year).strftime(
                    date_format
                ),
                budat_end=budat_end.strftime(date_format),
            )

            logger.debug("Requesting API {} for costs".format(api_url))
            response = self.session.get(api_url)
            response_time = time.perf_counter() - start_time

            logger.debug(f"SAP responded in {response_time}s")
            # costs and commitments are zeros by default defaults
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

            # Check if SAP responded with error
            if response.status_code != 200:
                logger.error(
                    f"SAP responded for costs with status code '{response.status_code}' and reason '{response.reason}' for given id '{id}'"
                )
                logger.error(
                    f"SAP responded for costs with status code '{response.headers}' for given id '{id}'"
                )
                logger.error(
                    f"SAP responded for costs with status code '{response.url}' for given id '{id}'"
                )
                logger.error(
                    f"SAP responded for costs with status code '{response._content}' for given id '{id}'"
                )
            else:
                json_response["costs"] = response.json()["d"]["results"]


            start_time = time.perf_counter()
            api_url = f"{self.sap_api_url}{self.sap_api_commitments_endpoint}".format(
                posid=id,
                budat_start=budat_start.replace(year=sap_start_year).strftime(
                    date_format
                ),
                budat_end=budat_end.strftime(date_format),
            )
            logger.debug("Requesting API {} for commitments from {} to {}".format(api_url, sap_start_year, budat_end.year))

            response = self.session.get(api_url)
            response_time = time.perf_counter() - start_time

            logger.debug(f"SAP responded in {response_time}s")

            # Check if SAP responded with error
            if response.status_code != 200:
                logger.error(
                    f"SAP responded for commitments with status code '{response.status_code}' and reason '{response.reason}' for given id '{id}'"
                )
            else:
                json_response["commitments"] = response.json()["d"]["results"]

            return self.__group_costs_and_commitments(
                sap_costs_and_commitments=json_response,
                sap_id=id,
            )
        else:
            logger.debug(
                f"No planning start year set or planning start year in the future for project(s) with SAP id {id}. Skipping SAP data fetch for id {id}"
            )
            return {}

    def __store_sap_costs(
        self,
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
                # store costs and commitments for project
                project_sap_cost, _ = SapCostService.get_or_create(
                    project_id=project.id,
                    group_id=project_group_id,
                    year=current_year,
                )

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
            group_sap_cost, _ = SapCostService.get_or_create(
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
        # 01 = Project task
        # 02, 03, 04 = Production task, will be grouped as one
        #
        # Task group id is formatted as sap_id.task_id (2814I06808.01,2814I06808.02,2814I06808.03, or 2814I06808.04)
        # Task id can also contain sub task i.e. 2814I06808.01.01, or sub sub task i.e. 2814I06808.01.01.02
        grouped_by_task = {
            "project_task": Decimal(0.000),
            "production_task": Decimal(0.000),
        }
        project_task_id = f"{sap_id}.01"
        for cost in values:
            task_id = cost["Posid"]
            group_id = (
                "project_task" if project_task_id in task_id else "production_task"
            )

            grouped_by_task[group_id] = grouped_by_task[group_id] + Decimal(
                cost["Wkgbtr"]
            )
        return grouped_by_task
