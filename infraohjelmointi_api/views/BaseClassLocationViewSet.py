from datetime import date
from collections import defaultdict
from django.db.models import F
from overrides import override
from rest_framework.response import Response
from rest_framework import status

from .BaseViewSet import BaseViewSet
from infraohjelmointi_api.models import ClassFinancial, LocationFinancial
from infraohjelmointi_api.services.CacheService import CacheService


class BaseClassLocationViewSet(BaseViewSet):
    """
    Base class for class and location viewsets
    """

    @staticmethod
    def build_frame_budgets_context(year: int, for_frame_view: bool = False) -> defaultdict:
        """
        Build frame_budgets context for consistent budget overlap logic.
        Uses caching for performance optimization.
        
        Args:
            year: Starting year for frame budget collection
            for_frame_view: Whether to filter for frame view (forFrameView=True) or standard view (forFrameView=False)
            
        Returns:
            defaultdict: Dictionary with keys "{year}-{relation_id}" and frameBudget values
        """
        cached_frame_budgets = CacheService.get_frame_budgets(year=year, for_frame_view=for_frame_view)
        if cached_frame_budgets is not None:
            frame_budgets = defaultdict(lambda: 0)
            frame_budgets.update(cached_frame_budgets)
            return frame_budgets
        
        class_financials = ClassFinancial.objects.filter(
            year__in=range(year, year+11),
            forFrameView=for_frame_view
        ).annotate(relation=F("classRelation")).values("year", "relation", "frameBudget")
        
        location_financials = LocationFinancial.objects.filter(
            year__in=range(year, year+11),
            forFrameView=for_frame_view
        ).annotate(relation=F("locationRelation")).values("year", "relation", "frameBudget")
        
        financials = class_financials.union(location_financials)
        frame_budgets = defaultdict(lambda: 0)
        for f in financials:
            relation_id = str(f['relation']) if f['relation'] else None
            if relation_id:
                frame_budgets[f"{f['year']}-{relation_id}"] = f["frameBudget"]
        
        CacheService.set_frame_budgets(
            year=year,
            for_frame_view=for_frame_view,
            data=dict(frame_budgets)
        )
        
        return frame_budgets

    @staticmethod
    def parse_forced_to_frame_param(forced_to_frame_param):
        """
        Parse and validate forcedToFrame query parameter.
        
        Args:
            forced_to_frame_param: Raw query parameter value
            
        Returns:
            bool: Parsed boolean value
            
        Raises:
            ParseError: If parameter is not a valid boolean
        """
        from rest_framework.exceptions import ParseError
        
        if forced_to_frame_param in ["False", "false"]:
            return False
        if forced_to_frame_param in ["true", "True"]:
            return True
        if forced_to_frame_param not in [True, False]:
            raise ParseError(
                detail={"forcedToFrame": "Value must be a boolean"}, code="invalid"
            )
        return forced_to_frame_param

    @staticmethod
    def _update_frame_view_if_needed(forced_to_frame_status, forced_to_frame, obj, entity_id, relation_field, financial_service):
        """
        Helper method to update frame view when needed.
        
        Args:
            forced_to_frame_status: AppStateValue for forcedToFrameStatus
            forced_to_frame: Current forced_to_frame value
            obj: Financial object instance
            entity_id: UUID of entity (class or location)
            relation_field: Name of relation field in financial model
            financial_service: Service class for financial operations
        """
        if forced_to_frame_status.value and forced_to_frame is False:
            update_kwargs = {
                "year": obj.year,
                f"{relation_field.replace('Relation', '')}_id": entity_id,
                "for_frame_view": True,
                "updatedData": {
                    "frameBudget": obj.frameBudget,
                    "budgetChange": obj.budgetChange
                }
            }
            financial_service.update_or_create(**update_kwargs)

    def create_patch_response(self, entity_id, start_year, entity_service, serializer_class, forced_to_frame=False):
        """
        Create standardized response for PATCH finance endpoints.
        
        Args:
            entity_id: UUID of entity (class or location)
            start_year: Financial year for context
            entity_service: Service class to fetch entity by id
            serializer_class: Serializer class for response
            
        Returns:
            Response: Standardized PATCH response
        """
        # Force fresh instance from database to avoid stale data
        instance = entity_service.get_by_id(id=entity_id)
        instance.refresh_from_db()
        
        # Clear any prefetch cache
        if hasattr(instance, '_prefetched_objects_cache'):
            instance._prefetched_objects_cache.clear()
        
        # Determine if this is a coordinator instance
        is_coordinator = getattr(instance, 'forCoordinatorOnly', False)
        
        return Response(
            serializer_class(
                instance,
                context={
                    "finance_year": start_year,
                    "for_coordinator": is_coordinator,
                    "forcedToFrame": forced_to_frame,
                },
            ).data
        )

    @classmethod
    def _get_coordinator_list_docstring(cls, entity_type, url_path):
        """
        Generate docstring for list_for_coordinator methods.
        
        Args:
            entity_type: "class" or "location"
            url_path: URL path for the endpoint
        """
        entity_plural = f"{entity_type}es" if entity_type == "class" else f"{entity_type}s"
        entity_title = entity_type.title()
        
        return f"""
        Overriden list action to get a list of coordinator Project{entity_title}s

            URL Query Parameters
            ----------

            year (optional) : Int

            Year number to fetch Project {entity_title}s with finances starting from this year.
            Defaults to current year.

            forcedToFrame (optional) : bool

            Query param to fetch coordinator {entity_plural} with frameView project sums.
            Defaults to False.

            Usage
            ----------

            {url_path}/?year=<year>&forcedToFrame=<bool>

            Returns
            -------

            JSON
                List of Project{entity_title} instances with financial sums for projects under each {entity_type}
        """

    @classmethod  
    def _get_coordinator_patch_docstring(cls, entity_type, url_path, param_name):
        """
        Generate docstring for patch_coordinator_*_finances methods.
        
        Args:
            entity_type: "class" or "location" 
            url_path: URL path for the endpoint
            param_name: Parameter name (class_id or location_id)
        """
        entity_title = entity_type.title()
        
        return f"""
        Custom PATCH endpoint for coordinator {entity_type}s **finances ONLY**

            URL Parameters
            ----------

            {param_name} : UUID string

            Coordinator {entity_type} Id

            Usage
            ----------

            {url_path}/coordinator/<{param_name}>/

            Returns
            -------

            JSON
                Patched coordinator Project{entity_title} Instance
        """

    def validate_and_process_patch_finances(self, request, entity_id, entity_service, financial_service, financial_model, relation_field):
        """
        Common validation and processing logic for PATCH finance endpoints.
        
        Args:
            request: HTTP request object
            entity_id: UUID of entity (class or location)
            entity_service: Service class for entity validation
            financial_service: Service class for financial operations
            financial_model: Model class for financial objects
            relation_field: Name of relation field in financial model
            
        Returns:
            tuple: (success: bool, response: Response or data dict)
        """
        try:
            from infraohjelmointi_api.services import AppStateValueService
            from rest_framework.exceptions import ParseError
            import logging
                        
            try:
                forced_to_frame = self.parse_forced_to_frame_param(
                    request.data.get("forcedToFrame", False)
                )
            except ParseError:
                return False, Response(
                    data={"forcedToFrame": "Value must be a boolean"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            # Validate entity exists (check both coordinator and planning classes)
            coordinator_instance_exists = entity_service.instance_exists(id=entity_id, forCoordinatorOnly=True)
            planning_instance_exists = entity_service.instance_exists(id=entity_id, forCoordinatorOnly=False)
            
            if not (coordinator_instance_exists or planning_instance_exists):
                return False, Response(status=status.HTTP_404_NOT_FOUND)
            
            # Check permissions: planner-only users cannot use coordinator endpoint.
            # Users with coordinator rights must still be allowed even if planner flag is true.
            user = getattr(request, "user", None)
            user_is_project_area_planner = bool(
                getattr(user, "is_project_area_planner", False)
            )
            user_group_names = set()
            if user is not None and hasattr(user, "ad_groups"):
                user_group_names = set(
                    user.ad_groups.all().values_list("name", flat=True)
                )

            user_has_coordinator_rights = (
                "sg_kymp_sso_io_koordinaattorit" in user_group_names
                or "sg_kymp_sso_io_admin" in user_group_names
            )

            if user_is_project_area_planner and not user_has_coordinator_rights:
                return False, Response(status=status.HTTP_403_FORBIDDEN)
            
            # Validate patch data format
            if not self.is_patch_data_valid(request.data):
                return False, Response(
                    data={"message": "Invalid data format"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            finances = request.data.get("finances")
            start_year = finances.get("year")
            
            # Validate start_year is present and is an integer
            if start_year is None or not isinstance(start_year, int):
                return False, Response(
                    data={"message": "Invalid year format"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            forced_to_frame_status, _ = AppStateValueService.get_or_create_by_name(
                name="forcedToFrameStatus"
            )
            
            # Validate year mappings and process each year
            for parameter in finances.keys():
                if parameter == "year":
                    continue
                patch_data = finances[parameter]
                year = financial_service.get_request_field_to_year_mapping(
                    start_year=start_year
                ).get(parameter, None)
                                
                if year is None:
                    return False, Response(
                        data={"message": "Invalid data format"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                
                # Process financial data for this year
                filter_kwargs = {
                    "year": year,
                    f"{relation_field}_id": entity_id,
                    "forFrameView": forced_to_frame
                }
                                
                try:
                    obj = financial_model.objects.get(**filter_kwargs)
                    for key, value in patch_data.items():
                        if value is None:
                            return False, Response(
                                data={"message": "Invalid value"},
                                status=status.HTTP_400_BAD_REQUEST,
                            )
                        setattr(obj, key, value)
                    obj.save()
                    
                    CacheService.invalidate_financial_sum(
                        instance_id=entity_id,
                        instance_type='ProjectClass' if relation_field == 'classRelation' else 'ProjectLocation'
                    )
                    for year_offset in range(-10, 1):
                        affected_year = year + year_offset
                        if affected_year >= 2000:
                            CacheService.invalidate_frame_budgets(year=affected_year)
                    self._update_frame_view_if_needed(
                        forced_to_frame_status, forced_to_frame, obj, entity_id, relation_field, financial_service
                    )
                        
                except financial_model.DoesNotExist:
                    create_kwargs = {
                        **patch_data,
                        "year": year,
                        f"{relation_field}_id": entity_id,
                        "forFrameView": forced_to_frame
                    }
                    obj = financial_model(**create_kwargs)
                    try:
                        obj.save()
                    except Exception as save_error:
                        logger.error(
                            "Failed to save new financial record: %s",
                            save_error,
                        )
                        return False, Response(
                            data={"message": "Failed to save financial data: " + str(save_error)},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    
                    CacheService.invalidate_financial_sum(
                        instance_id=entity_id,
                        instance_type='ProjectClass' if relation_field == 'classRelation' else 'ProjectLocation'
                    )
                    for year_offset in range(-10, 1):
                        affected_year = year + year_offset
                        if affected_year >= 2000:
                            CacheService.invalidate_frame_budgets(year=affected_year)
                    self._update_frame_view_if_needed(
                        forced_to_frame_status, forced_to_frame, obj, entity_id, relation_field, financial_service
                    )
                except Exception as update_error:
                    logger.error(
                        "Unexpected error processing financial data: %s",
                        update_error,
                    )
                    return False, Response(
                        data={"message": "Failed to update financial data: " + str(update_error)},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            
            return True, {
                "entity_id": entity_id,
                "start_year": start_year,
                "obj": obj,
                "forced_to_frame": forced_to_frame,
            }
        
        except Exception as e:
            # Catch any unexpected exceptions and return a proper error response
            return False, Response(
                data={"message": f"Internal server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @override
    def list(self, request, *args, **kwargs):
        """
        Overriden list action to get a list of ProjectClass

            URL Query Parameters
            ----------

            year (optional) : Int

            Year number to fetch Project Class/Location with finances starting from this year.
            Defaults to current year.

            Usage
            ----------

            project-classes/?year=<year>

            or

            project-locations/?year=<year>

            Returns
            -------

            JSON
                List of ProjectClass/ProjectLocation instances with financial sums for projects under each instance
        """
        year = int(request.query_params.get("year", date.today().year))
        qs = self.get_queryset()
        frame_budgets = self.build_frame_budgets_context(year, for_frame_view=False)
        
        serializer = self.get_serializer(
            qs, 
            many=True, 
            context={
                "finance_year": year,
                "frame_budgets": frame_budgets
            }
        )

        return Response(serializer.data)

    @override
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        year = int(request.query_params.get("year", date.today().year))
        frame_budgets = self.build_frame_budgets_context(year, for_frame_view=False)
        
        serializer = self.get_serializer(
            instance,
            context={
                "finance_year": year,
                "frame_budgets": frame_budgets
            }
        )
        
        return Response(serializer.data)

    def is_patch_data_valid(self, data):
        """
        Utility function to validate patch data sent to the custom PATCH endpoint for coordinator class/location finances
        """
        finances = data.get("finances", None)
        if finances == None:
            return False

        parameters = list(finances.keys())
        if "year" not in parameters:
            return False
        parameters.remove("year")

        for param in parameters:
            values = finances[param]
            
            if not isinstance(values, dict):
                return False
                
            values_length = len(values.keys())
            if values_length == 0 or values_length > 2:
                return False
            if "frameBudget" not in values and "budgetChange" not in values:
                return False

        return True
